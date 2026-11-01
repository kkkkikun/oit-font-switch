#!/usr/bin/env python3
"""把参考字体的【】轮廓嵌入目标字体，并按「贴内缘」摆放。

背景（红米 K50 Ultra / 超级看书 WebView 实测）：
  阅读页是 Chromium WebView，CSS 字体栈结尾是 sans-serif（= 我们的 Hanyi）。
  Hanyi 2018 原本自带 U+3010/U+3011，但字形只有 0.53em 高、且不在同一套
  「贴内缘」位置上；若把这些码位从 cmap 摘掉让系统回退，Chromium 会改用
  回退字体（MiSans）的括号 —— 字号(92px) 与正文(97px) 不同、单元格宽度不同，
  于是「【」与正文之间出现一条明显空档，视觉上左右不对称。

本工具：把参考字体的括号轮廓按目标字体的 upem 缩放后写回目标字体的
uni3010/uni3011 字形，并可选地调整水平位置（--inset 表示括号墨迹与字框
边缘的距离，单位 em），让括号紧贴被括住的内容。

用法:
  python3 embed_bracket_glyphs.py \
      --font HanyiSentyChalkOriginal.ttf \
      --source oem/MiSansVF.stock.ttf \
      --out HanyiSentyChalkOriginal.embedded.ttf \
      --inset 0.02
"""

import argparse
import sys

from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen

BRACKETS = {"\u3010": ("\u3010", "left"), "\u3011": ("\u3011", "right")}


def glyph_of(font, ch):
    cmap = font.getBestCmap()
    name = cmap.get(ord(ch))
    if name is None:
        raise SystemExit(f"字体缺少 U+{ord(ch):04X}")
    return name


def ink_box(font, name):
    gs = font.getGlyphSet()
    pen = BoundsPen(gs)
    gs[name].draw(pen)
    if not pen.bounds:
        raise SystemExit(f"字形 {name} 没有墨迹")
    return pen.bounds


def set_advance(font, ch, em_value):
    """把某字符的步进改为 em_value（单位 em），用于收敛正文里的空档。"""
    cmap = font.getBestCmap()
    name = cmap.get(ord(ch))
    if name is None:
        return None
    old = font["hmtx"][name][0]
    upem = font["head"].unitsPerEm
    font["hmtx"][name] = (round(em_value * upem), font["hmtx"][name][1])
    print(f"  步进调整 U+{ord(ch):04X}: {old} ({old / upem:.4f}em) → {font['hmtx'][name][0]} ({em_value:.4f}em)")
    return name


def build(args):
    target = TTFont(args.font)
    source = TTFont(args.source, fontNumber=0)

    t_upem = target["head"].unitsPerEm
    s_upem = source["head"].unitsPerEm
    scale = t_upem / s_upem

    t_gs = target.getGlyphSet()
    s_gs = source.getGlyphSet()

    for ch, (label, side) in BRACKETS.items():
        t_name = glyph_of(target, ch)
        s_name = glyph_of(source, ch)

        sx0, sy0, sx1, sy1 = ink_box(source, s_name)
        inset_units = args.inset * t_upem

        if side == "left":  # 【：墨迹贴字框右缘
            tx = t_upem - inset_units - sx1 * scale
        else:               # 】：墨迹贴字框左缘
            tx = inset_units - sx0 * scale
        ty = args.shift_y * t_upem

        rec = RecordingPen()
        s_gs[s_name].draw(rec)
        pen = TTGlyphPen(None)
        tpen = TransformPen(pen, (scale, 0, 0, scale, tx, ty))
        rec.replay(tpen)

        new_glyph = pen.glyph()
        target["glyf"][t_name] = new_glyph

        # hmtx 的 lsb 必须与新轮廓的 xMin 一致，否则 FreeType/Minikin 会按旧 lsb 定位，
        # 导致括号整体横向错位。
        adv = target["hmtx"][t_name][0]
        new_lsb = min(p[0] for p in new_glyph.coordinates)
        target["hmtx"][t_name] = (adv, new_lsb)

        adv = target["hmtx"][t_name][0]
        print(f"U+{ord(ch):04X} {label}: 已写入 {t_name} "
              f"(adv={adv} = {adv / t_upem:.4f}em, 源墨迹 x=[{sx0},{sx1}] → 目标 x=[{tx + sx0 * scale:.0f},{tx + sx1 * scale:.0f}])")

    if args.space is not None:
        set_advance(target, " ", args.space)
    if args.ideo_space is not None:
        set_advance(target, "\u3000", args.ideo_space)

    target.save(args.out)
    print(f"已保存 {args.out}")

    # 复核
    check = TTFont(args.out)
    cmap = check.getBestCmap()
    upem = check["head"].unitsPerEm
    glyf = check["glyf"]
    for ch in BRACKETS:
        name = cmap.get(ord(ch))
        g = glyf[name]
        xs = [p[0] for p in g.coordinates]
        ys = [p[1] for p in g.coordinates]
        adv, lsb = check["hmtx"][name]
        ok = "✓" if lsb == min(xs) else "✗ lsb 与 xMin 不一致！"
        print(f"  复核 U+{ord(ch):04X}: glyph={name} adv={adv} ({adv / upem:.4f}em) "
              f"inkx=[{min(xs) / upem:.4f},{max(xs) / upem:.4f}]em inky=[{min(ys) / upem:.4f},{max(ys) / upem:.4f}]em "
              f"lsb={lsb} {ok}")


def main():
    ap = argparse.ArgumentParser(description="把括号轮廓嵌入目标字体")
    ap.add_argument("--font", required=True, help="目标字体（含 U+3010/U+3011）")
    ap.add_argument("--source", required=True, help="参考字体（取括号轮廓）")
    ap.add_argument("--out", required=True, help="输出字体")
    ap.add_argument("--inset", type=float, default=0.02,
                    help="括号墨迹与字框边缘的距离，单位 em（默认 0.02）")
    ap.add_argument("--shift-y", type=float, default=0.0,
                    help="括号垂直偏移，单位 em（默认 0，基线不变）")
    ap.add_argument("--space", type=float, default=None,
                    help="U+0020 普通空格的步进，单位 em（默认不改）")
    ap.add_argument("--ideo-space", type=float, default=None,
                    help="U+3000 表意空格的步进，单位 em（默认不改）")
    args = ap.parse_args()
    build(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())

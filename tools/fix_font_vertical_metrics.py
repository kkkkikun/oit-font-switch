#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修正「汉仪新蒂黑板报底字」的垂直度量，让它在 Android 上不再显得下沉。

问题根因（红米 K50 Ultra / HyperOS 2 / Android 15 实测定位）
--------------------------------------------------------------------------
该字体的 head 表字体边界是 y[-826, 3271]（upem=2048），即上边界高达 **1.60 em**。
罪魁祸首是 U+005E '^'：它的墨迹被放在基线上方 1.52~1.60 em 处（一个 0.075em
高的小尖角悬在天上），把整个字体边界顶了上去。

Android 的 TextView 默认 includeFontPadding=true，TextView 的高度与基线位置
按字体的 **fTop/fBottom**（来自字体边界）计算，而不是 hhea 的 ascent/descent：

    TextView 高度   = fTop - fBottom
    首行基线位置    = fTop   （距视图顶部）

于是每个 TextView 顶部凭空多出
    fTop - 实际墨迹顶 = 3271 - 1406 = 1865 单位 ≈ 0.91 em ≈ 51 px
的空白，正文整体被推到行的下沿 —— 这就是「字体位置偏下、不太适配」的真正原因。

（实测佐证：安装后「我的设备」这一行，TextView 边界 [223,1032][467,1147]，
高度 115px；其中正文墨迹在 y 1084~1132，正文底部与图标底部齐平；而安装前
MiSans 的正文是与图标居中对齐的。）

修正做法
--------------------------------------------------------------------------
1. 把悬空的 '^' 等异常字形平移回 em 框内的正常位置；
2. 把 head 字体边界收紧到「真实字形墨迹范围」（上界取除异常字形外的最大值）；
3. 同步 hhea / OS/2 的 ascent、descent、lineGap 与 typo / win 度量，
   使行高与 Android 原生中文字体（Noto Sans CJK）接近。

效果：TextView 高度 = 真实墨迹高度，正文重新与图标居中对齐，行高回到正常。
"""

import os
import sys

from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen

FONT_FILE = "HanyiSentyChalkOriginal.ttf"

# 目标：字体边界覆盖绝大多数字形，但不因个别异常字形被撑大
# （取真实字形墨迹的 99 分位与 1 分位，再取整）
def target_bounds(ink_tops, ink_bottoms):
    tops = sorted(ink_tops)
    bots = sorted(ink_bottoms)
    y_max = tops[int(len(tops) * 0.995)]
    y_min = bots[int(len(bots) * 0.005)]
    return int(round(y_max)), int(round(y_min))


def ink_bounds(gs, glyph_name):
    bp = BoundsPen(gs)
    try:
        gs[glyph_name].draw(bp)
    except Exception:
        return None
    return bp.bounds


def translate_glyph(font, gs, name, dy):
    """把字形轮廓整体上/下平移 dy（复合字形平移各组件偏移）"""
    glyf = font["glyf"]
    g = glyf[name]
    if g.isComposite():
        for comp in g.components:
            comp.y += dy
            comp.recalcBounds(glyf)
    else:
        if g.numberOfContours:
            g.coordinates.translate((0, dy))
            g.recalcBounds(glyf)


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else FONT_FILE
    dst = sys.argv[2] if len(sys.argv) > 2 else "HanyiSentyChalkOriginal.fixed.ttf"
    font = TTFont(src)
    upem = font["head"].unitsPerEm
    head = font["head"]
    hhea = font["hhea"]
    os2 = font["OS/2"]
    gs = font.getGlyphSet()
    cmap = font.getBestCmap()

    print("== 原始度量 ==")
    print(f"  upem={upem}  head bbox y[{head.yMin},{head.yMax}]")
    print(f"  hhea asc={hhea.ascent} desc={hhea.descent} gap={hhea.lineGap}")
    print(f"  OS/2 typo {os2.sTypoAscender}/{os2.sTypoDescender}/{os2.sTypoLineGap}"
          f"  win {os2.usWinAscent}/{os2.usWinDescent}")

    # ---- 1. 统计每个字形的墨迹范围 -------------------------------------
    bounds = {}
    for cp, name in cmap.items():
        b = ink_bounds(gs, name)
        if b:
            bounds[name] = (cp, b)

    # 找到把字体边界撑爆的元凶：墨迹完全悬在 em 框上方的字形
    normal_top = 1900          # 正常汉字墨迹顶的量级
    stray = [(cp, n, b) for n, (cp, b) in bounds.items() if b[3] > normal_top]
    stray.sort(key=lambda x: -x[2][3])
    print("\n== 异常（悬空/超界）字形 ==")
    for cp, n, b in stray[:10]:
        print(f"   U+{cp:04X} '{chr(cp) if 32 < cp < 0x3000 else '?'}' {n} ink y[{b[1]},{b[3]}]")

    # ---- 2. 把异常字形平移回 em 框 --------------------------------------
    moved = []
    for cp, name, b in stray:
        h = b[3] - b[1]
        if b[1] > 0.55 * upem:      # 整块悬在基线上方 → 视作放错位置
            dy = int(round(0.60 * upem)) - b[1]      # 落到 x 高度附近
        else:                       # 只是顶端越界 → 压回框内
            dy = int(round(normal_top)) - b[3]
        translate_glyph(font, gs, name, dy)
        moved.append((cp, name, dy))
        print(f"   平移 U+{cp:04X} {name}: dy={dy:+d}")

    # ---- 3. 重新统计真实墨迹范围 ----------------------------------------
    gs = font.getGlyphSet()
    bounds = {}
    for cp, name in cmap.items():
        b = ink_bounds(gs, name)
        if b:
            bounds[name] = (cp, b)
    tops = [b[3] for _, b in bounds.values()]
    bots = [b[1] for _, b in bounds.values()]
    y_max, y_min = target_bounds(tops, bots)
    # 保证覆盖所有字形（平移后仍有越界就取绝对值）
    y_max = max(y_max, max(tops))
    y_min = min(y_min, min(bots))
    print(f"\n== 收紧后的字体边界 ==\n   y[{y_min},{y_max}]  "
          f"= [{y_min/upem:.3f}em, {y_max/upem:.3f}em]  (原 [{head.yMin},{head.yMax}])")

    # ---- 4. 写回度量 ----------------------------------------------------
    head.yMin, head.yMax = y_min, y_max
    head.xMin, head.xMax = min(head.xMin, 0), max(head.xMax, 0)
    head.recalcBBox = False

    ascent, descent = y_max, y_min
    hhea.ascent, hhea.descent, hhea.lineGap = ascent, descent, 0
    os2.sTypoAscender, os2.sTypoDescender, os2.sTypoLineGap = ascent, descent, 0
    os2.usWinAscent, os2.usWinDescent = ascent, -descent
    os2.fsSelection &= ~(1 << 7)      # 不用 typo 度量（Android 走 hhea/边界）

    print(f"   hhea asc={ascent} desc={descent} gap=0  行高={(ascent-descent)/upem:.3f}em")
    print(f"   OS/2 typo {ascent}/{descent}/0  win {ascent}/{-descent}")

    font.save(dst)
    print(f"\n已写出 {dst}")

    # ---- 5. 复核 --------------------------------------------------------
    f2 = TTFont(dst)
    h2, hh2, o2 = f2["head"], f2["hhea"], f2["OS/2"]
    print("== 复核 ==")
    print(f"   head bbox y[{h2.yMin},{h2.yMax}]  hhea {hh2.ascent}/{hh2.descent}"
          f"  win {o2.usWinAscent}/{o2.usWinDescent}")
    gs2 = f2.getGlyphSet()
    cm2 = f2.getBestCmap()
    tops, bots = [], []
    for cp, name in cm2.items():
        b = ink_bounds(gs2, name)
        if b:
            tops.append(b[3]); bots.append(b[1])
    print(f"   实际墨迹范围 y[{min(bots)},{max(tops)}]  "
          f"TextView 预计高度={(max(tops)-min(bots))/upem:.3f}em")
    ok = (max(tops) <= h2.yMax) and (min(bots) >= h2.yMin)
    print(f"   边界自洽: {'✓' if ok else '✗'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

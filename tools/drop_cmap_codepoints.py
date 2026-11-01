#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从字体的 cmap 里摘掉指定码位，让这些字符回退到系统其它字体渲染。

为什么需要
--------------------------------------------------------------------------
某些字体版本把中文括号类标点设计成「实心黑楔块」（例如 2018 版的
【】〔〕〖〗），视觉上非常突兀。同一款字体的旧版本（2016）干脆**没有**
这些码位，于是靠回退字体渲染，反而正常。

把码位从 cmap 里删掉（字形保留但不可达），系统就会像对待旧版本一样，
把这些字符交给回退字体 —— 效果与旧版一致，但保留新版本的其他改进。

用法：
    python3 drop_cmap_codepoints.py <src.ttf> <dst.ttf> <码位...>
    python3 drop_cmap_codepoints.py <src.ttf> <dst.ttf> --preset brackets

码位可以写成十进制（3010）或十六进制（0x3010 或 U+3010）。
"""

import sys

from fontTools.ttLib import TTFont

# 黑板报体 2018 版里设计成实心块的方括号类标点
PRESET_BRACKETS = [
    0x3010,  # 【
    0x3011,  # 】
    0x3014,  # 〔
    0x3015,  # 〕
    0x3016,  # 〖
    0x3017,  # 〗
]


def parse_cp(s):
    s = s.strip()
    try:
        if s.lower().startswith("u+"):
            return int(s[2:], 16)
        if s.lower().startswith("0x"):
            return int(s, 16)
        return int(s)
    except ValueError:
        raise SystemExit("无法解析码位: %s" % s)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    src, dst = sys.argv[1], sys.argv[2]
    rest = sys.argv[3:]
    if not rest:
        print("至少要给一个码位，或 --preset brackets")
        return 2
    if "--preset" in rest:
        i = rest.index("--preset")
        preset_name = rest[i + 1] if i + 1 < len(rest) else "brackets"
        rest = rest[:i] + rest[i + 2:]
        if preset_name != "brackets":
            print("未知预设: %s（可用: brackets）" % preset_name)
            return 2
        cps = list(PRESET_BRACKETS) + [parse_cp(r) for r in rest]
    else:
        cps = [parse_cp(r) for r in rest]

    font = TTFont(src)
    cmap_tables = font["cmap"].tables
    dropped = []

    for table in cmap_tables:
        # 只处理 BMP / Unicode 平台的子表
        if table.isUnicode():
            for cp in cps:
                if cp in table.cmap:
                    del table.cmap[cp]
                    dropped.append(cp)
    # getBestCmap 用的那张子表也要确保一致
    best = font.getBestCmap()
    for cp in cps:
        if cp in best:
            best.pop(cp, None)

    font.save(dst)

    print("已写出 %s" % dst)
    print("摘掉的码位: %s" % (", ".join("U+%04X %s" % (cp, chr(cp)) for cp in sorted(set(dropped))) or "（无）"))
    # 复核
    f2 = TTFont(dst)
    c2 = f2.getBestCmap()
    still = [cp for cp in cps if cp in c2]
    print("复核: 仍可达的码位 %d 个 %s" % (len(still), still if still else "✓"))
    print("      总码位数 %d -> %d" % (len(font.getBestCmap()), len(c2)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

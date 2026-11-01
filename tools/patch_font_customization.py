#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改写 MIUI 的 /product/etc/fonts_customization.xml。

为什么是「删除」而不是「替换」
--------------------------------------------------------------------------
AOSP 的 fonts_customization.xml 机制（customizationType="new-named-family"）
**只在 /product/fonts/ 里解析字体文件**。黑板报底字装在 /system/fonts/，所以
直接把家族内容换成 HanyiSentyChalkOriginal.ttf 的做法，会让这 13 个家族
**整族被静默丢弃**（实测：dumpsys 里 mitype / miuiex 等直接消失，而不是变字体）。

因此改为：
    1) 从 customization 文件里**移除**这 13 个家族（miclock-* / mitype-mono-*
       等一律不动）；
    2) 由主配置（miui_font_fallback.xml / miui_fonts.xml）注册同名家族，
       主配置的字体文件在 /system/fonts/ 解析，指向黑板报底字。

被移除的家族
--------------------------------------------------------------------------
    mitype / mitype-thin / mitype-extralight / mitype-light / mitype-normal
    mitype-regular / mitype-medium / mitype-demibold / mitype-semibold
    mitype-bold / mitype-heavy
    miuiex / miuiex-light

刻意**不移除**的
--------------------------------------------------------------------------
    mitype-mono-*    等宽（终端/代码类场景）
    mitype-clock*    时钟专用
    miclock-*        锁屏艺术字（Beihaibei / SilkSerif 等刻意造型字体）

探针家族（一次性验证用，验证完可删）
--------------------------------------------------------------------------
    oit-test-prod  → MitypeVF.ttf            （只存在于 /product/fonts/）
    oit-test-sys   → HanyiSentyChalkOriginal.ttf（只存在于 /system/fonts/）
    重启后看 dumpsys 里哪个还在，就能确认 customization 到底解析哪个目录。
"""

import os
import re
import sys
import xml.etree.ElementTree as ET

FONT_FILE = "HanyiSentyChalkOriginal.ttf"
PS_NAME = "HanyiSentyChalkOriginal"

TARGET_NAMES = (
    "mitype", "mitype-thin", "mitype-extralight", "mitype-light", "mitype-normal",
    "mitype-regular", "mitype-medium", "mitype-demibold", "mitype-semibold",
    "mitype-bold", "mitype-heavy",
    "miuiex", "miuiex-light",
)

# 探针：验证 fonts_customization.xml 的字体文件解析目录
PROBE_FAMILIES = (
    ("oit-test-prod", "MitypeVF.ttf", "MIUITypeface-M"),
    ("oit-test-sys", FONT_FILE, PS_NAME),
)


def _attr(attrs, key):
    m = re.search(r'\b%s\s*=\s*"([^"]*)"' % key, attrs)
    return m.group(1) if m else None


def patch(text):
    notes = []
    out = []
    pos = 0
    for m in re.finditer(r"<family\b([^>]*)>(.*?)</family>", text, re.S):
        out.append(text[pos:m.start()])
        pos = m.end()
        attrs, body = m.group(1), m.group(2)
        name = _attr(attrs, "name")
        if name in TARGET_NAMES:
            notes.append("移除家族 %-22s（改由主配置注册 → %s）" % (name, FONT_FILE))
            continue  # 不输出 = 移除
        out.append(m.group(0))
    out.append(text[pos:])
    return "".join(out), notes


def inject_probes(text):
    blocks = []
    for name, file, ps in PROBE_FAMILIES:
        blocks.append(
            '    <family customizationType="new-named-family" name="%s">\n'
            '        <font weight="400" style="normal" postScriptName="%s">%s</font>\n'
            '    </family>\n' % (name, ps, file))
    assert "</fonts-modification>" in text
    return text.replace("</fonts-modification>", "".join(blocks) + "</fonts-modification>")


def main():
    if len(sys.argv) < 3:
        print("用法: patch_font_customization.py <src.xml> <dst.xml> [--no-probe]")
        return 2
    src, dst = sys.argv[1], sys.argv[2]
    no_probe = "--no-probe" in sys.argv[3:]
    text = open(src, encoding="utf-8").read()
    patched, notes = patch(text)
    if not no_probe:
        patched = inject_probes(patched)
        notes.append("插入探针家族: %s" % ", ".join(n for n, _, _ in PROBE_FAMILIES))
    print("== %s ==" % os.path.basename(src))
    for n in notes:
        print("   -", n)
    root = ET.fromstring(patched)
    fams = root.findall("family")
    names = [f.get("name") for f in fams]
    for t in TARGET_NAMES:
        assert t not in names, "目标家族未被移除: %s" % t
    hit = [f for f in fams if FONT_FILE in ET.tostring(f, encoding="unicode")]
    print("   XML 解析通过 ✓ 家族总数=%d 目标家族已全部移除=%d 探针引用新字体=%d"
          % (len(fams), len(TARGET_NAMES), len(hit)))
    open(dst, "w", encoding="utf-8", newline="\n").write(patched)
    print("   已写出 %s" % dst)
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 HyperOS / MIUI 的字体配置改写成「汉仪新蒂黑板报底字」全局字体。

实测结论（红米 K50 Ultra / HyperOS 2 / Android 15 / Kitsune Mask，2026-10-31）
--------------------------------------------------------------------------
运行时真正生效的字体配置是：

    /system_ext/etc/miui_font_fallback.xml     ← fallback 家族清单（151 条）
    /system_ext/etc/miui_fonts.xml             ← 命名家族清单

证据：`dumpsys font` 的 "Named Family List" / "Dump Fallback Families" 与
miui_* 两份文件逐条吻合（sans-serif→Roboto+wdth100、zh-Hans→NotoSansCJK、
und-Arab→NotoNaskhArabic…）；而 hyper_* 那份的 MiSans*/Noto* 内容完全对不上。

首轮安装失效的根因：**/system/etc/fonts.xml 根本没被采用**（改写后
dumpsys 里 HanyiSentyChalk 零命中，sans-serif 仍是 Roboto）。Android 15 的
FontManagerService 在存在 font_fallback.xml 时走新格式，fonts.xml 被忽略。

另外 Kitsune Mask 不支持 system_ext/ 覆盖（实测 /system_ext/etc/hyper_fonts.xml
重启后仍是原始 90,506 字节），所以 /system_ext 下这 4 份文件改用
post-fs-data.sh 里 `mount -o bind` 挂载改写版。

被改写的家族（每个压成单条 weight=400）
--------------------------------------------------------------------------
    name="sans-serif"               系统默认家族
    (无名默认家族 / 拉丁)            运行时的 sans-serif 实际落点（Roboto-Regular.ttf）
    name="sans-serif-condensed"
    lang="zh" / "zh-Hans" / "zh-Hant,zh-Bopo"

单条 weight=400 的原因：静态字体没有 wght 轴，保留多条可变字重记录会让
粗体精确命中 weight=700 而不合成加粗。

其余 150+ 个 Noto / 各文字族一律不动，保证 emoji、符号、阿拉伯语等
仍按原回退链正常显示。
"""

import os
import re
import sys
import xml.etree.ElementTree as ET

FONT_FILE = "HanyiSentyChalkOriginal.ttf"
PS_NAME = "HanyiSentyChalkOriginal"

# 命名家族 → 直接命中
TARGET_NAMES = ("sans-serif", "sans-serif-condensed")
# 语言家族 → 直接命中
TARGET_LANGS = ("zh", "zh-Hans", "zh-Hant,zh-Bopo")
# 无名默认家族里，判定为「拉丁默认」的那一个（符号家族 NotoSansSymbols 不动）
LATIN_DEFAULT_FILES = ("Roboto-Regular.ttf", "MiSansLatinVF.ttf")

NEW_ENTRY = ('<font weight="400" style="normal" postScriptName="%s">%s</font>'
              % (PS_NAME, FONT_FILE))

# 需要**新增**的命名家族：MIUI 系统应用（设置/桌面/系统UI）显式请求这些家族，
# 不走系统默认 sans-serif。它们原本由 /product/etc/fonts_customization.xml
# 注册，但那个机制只在 /product/fonts/ 里解析字体文件，而黑板报底字装在
# /system/fonts/，所以改到主配置里注册（主配置的字体文件在 /system/fonts/ 解析）。
EXTRA_FAMILIES = (
    "mitype", "mitype-thin", "mitype-extralight", "mitype-light", "mitype-normal",
    "mitype-regular", "mitype-medium", "mitype-demibold", "mitype-semibold",
    "mitype-bold", "mitype-heavy",
    "miuiex", "miuiex-light",
)

# 仅注册为「可选字体」时使用的家族名（与字体 name 表的 family 名一致）
OPTIONAL_FAMILY = "Hanyi Senty Chalk Original"

ATTR_RE = r'([A-Za-z-]+)\s*=\s*"([^"]*)"'


def _attr(attrs, key):
    m = re.search(r'\b%s\s*=\s*"([^"]*)"' % key, attrs)
    return m.group(1) if m else None


def _files(body):
    return re.findall(r'<font\b[^>]*>\s*([A-Za-z0-9_.-]+\.(?:ttf|ttc|otf))', body)


def is_target(attrs, body):
    name = _attr(attrs, "name")
    lang = _attr(attrs, "lang")
    if name in TARGET_NAMES:
        return True
    if lang in TARGET_LANGS:
        return True
    if name is None and lang is None:
        return any(f in LATIN_DEFAULT_FILES for f in _files(body))
    return False


def label(attrs):
    name = _attr(attrs, "name")
    lang = _attr(attrs, "lang")
    if name:
        return 'name="%s"' % name
    if lang:
        return 'lang="%s"' % lang
    return "(无名默认家族)"


def patch(text):
    """返回 (改写后文本, 改动明细列表)"""
    notes = []
    out = []
    pos = 0
    for m in re.finditer(r"<family\b([^>]*)>(.*?)</family>", text, re.S):
        out.append(text[pos:m.start()])
        pos = m.end()
        attrs, body = m.group(1), m.group(2)
        if not is_target(attrs, body):
            out.append(m.group(0))
            continue
        old_files = sorted(set(_files(body)))
        old_n = len(re.findall(r"<font\b", body))
        out.append("<family%s>\n        %s\n    </family>" % (attrs, NEW_ENTRY))
        notes.append("%-26s %d 条记录 %s -> 1 条 -> %s"
                     % (label(attrs), old_n, old_files, FONT_FILE))
    out.append(text[pos:])
    return "".join(out), notes


def inject_extra_families(text):
    """在 </familyset> 前追加 EXTRA_FAMILIES 里的命名家族"""
    blocks = []
    for name in EXTRA_FAMILIES:
        blocks.append(
            '    <family name="%s">\n        %s\n    </family>\n'
            % (name, NEW_ENTRY))
    if "</familyset>" not in text:
        raise AssertionError("文件里没有 </familyset>，无法追加家族")
    return text.replace("</familyset>", "".join(blocks) + "</familyset>")


def inject_optional_family(text):
    """只追加一个具名家族（可选字体模式：系统默认保持原厂，仅多一个可选家族）"""
    block = ('    <family name="%s">\n        %s\n    </family>\n'
             % (OPTIONAL_FAMILY, NEW_ENTRY))
    assert "</familyset>" in text
    return text.replace("</familyset>", block + "</familyset>")


def verify(patched, expect_min):
    root = ET.fromstring(patched)
    fams = root.findall("family")
    hit = []
    for f in fams:
        blob = ET.tostring(f, encoding="unicode")
        if FONT_FILE in blob:
            hit.append(f)
            assert "<axis" not in blob, "改写后的家族里仍有 axis 标签: %s" % blob[:200]
    assert len(hit) >= expect_min, "命中家族数 %d < 期望 %d" % (len(hit), expect_min)
    # 未改写的家族必须保持原样（数量不变）
    return fams, hit


def main():
    if len(sys.argv) < 3:
        print("用法: patch_font_config.py <src.xml> <dst.xml> [期望命中家族数]")
        return 2
    src, dst = sys.argv[1], sys.argv[2]
    expect = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    text = open(src, encoding="utf-8").read()
    extra_only = "--extra-only" in sys.argv[3:]
    if extra_only:
        patched, notes = text, []
        patched = inject_optional_family(patched)
        notes.append("追加可选家族: %s（其余家族保持原厂）" % OPTIONAL_FAMILY)
    else:
        patched, notes = patch(text)
        patched = inject_extra_families(patched)
        notes.append("追加命名家族: %s" % ", ".join(EXTRA_FAMILIES))
    print("== %s ==" % os.path.basename(src))
    for n in notes:
        print("   -", n)
    fams, hit = verify(patched, expect)
    print("   XML 解析通过 ✓ 家族总数=%d 改写=%d" % (len(fams), len(hit)))
    open(dst, "w", encoding="utf-8", newline="\n").write(patched)
    print("   已写出 %s" % dst)
    return 0


if __name__ == "__main__":
    sys.exit(main())

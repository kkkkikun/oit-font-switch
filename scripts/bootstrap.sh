#!/usr/bin/env bash
#
# bootstrap.sh —— 在已 root 的 HyperOS/MIUI 设备上，从零部署「汉仪新蒂黑板报体底字」全局字体
#
#   1. 从设备拉取 5 份运行时真正生效的字体配置（OEM XML）
#   2. 打补丁：chalk 模式（全局）/ optional 模式（只注册一个可选字体）
#   3. 推送字体 + 配置到设备暂存区
#   4. 安装 Magisk 模块
#   5. 重启（或用 --no-reboot 跳过）
#
# 用法：
#   ./scripts/bootstrap.sh --font /path/to/HanyiSentyChalkOriginal.ttf [--serial <serial>] [--no-reboot]
#
# 说明：本仓库**不包含字体本体**。汉仪新蒂黑板报体底字是商业字体，
#      官网条款为「个人非商业使用免费下载」，商用须另行取得授权。
#      官方下载地址见 README。
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD="$REPO_ROOT/build"
STAGE_REMOTE="/data/local/tmp/oit-font"

ADB="${ADB:-adb}"
SERIAL=""
FONT=""
REBOOT=1

die() { echo "错误: $*" >&2; exit 1; }
info() { echo "==> $*"; }

while [ $# -gt 0 ]; do
  case "$1" in
    --font)     FONT="${2:?}"; shift 2 ;;
    --serial)   SERIAL="${2:?}"; shift 2 ;;
    --adb)      ADB="${2:?}"; shift 2 ;;
    --no-reboot) REBOOT=0; shift ;;
    -h|--help)  sed -n '2,25p' "$0"; exit 0 ;;
    *)          die "未知参数: $1" ;;
  esac
done

# ---- 设备 ----
if [ -z "$SERIAL" ]; then
  mapfile -t DEVICES < <("$ADB" devices | awk 'NR>1 && $2=="device" {print $1}')
  [ "${#DEVICES[@]}" -eq 1 ] || die "需要恰好一台设备在线，当前 ${#DEVICES[@]} 台；用 --serial 指定"
  SERIAL="${DEVICES[0]}"
fi
info "设备: $SERIAL"
A() { "$ADB" -s "$SERIAL" "$@"; }

A shell "su -c 'id -u'" | grep -q 0 || die "设备未 root"

# ---- 字体本体 ----
if [ -z "$FONT" ]; then
  for cand in "$REPO_ROOT/HanyiSentyChalkOriginal.ttf" "$REPO_ROOT/build/HanyiSentyChalkOriginal.ttf"; do
    [ -f "$cand" ] && FONT="$cand" && break
  done
fi
[ -n "$FONT" ] || die "请用 --font 指定字体文件路径（本仓库不含字体本体，见 README 的下载说明）"
[ -f "$FONT" ] || die "字体文件不存在: $FONT"
FONT="$(cd "$(dirname "$FONT")" && pwd)/$(basename "$FONT")"
info "字体: $FONT"

rm -rf "$BUILD"
mkdir -p "$BUILD/oem" "$BUILD/optional"

# ---- 1. 拉 OEM 配置 ----
# 这 5 个文件才是 Android 15 / HyperOS 运行时真正解析的
OEM_FILES=(
  "/system_ext/etc/miui_font_fallback.xml:miui_font_fallback"
  "/system_ext/etc/miui_fonts.xml:miui_fonts"
  "/system_ext/etc/hyper_font_fallback.xml:hyper_font_fallback"
  "/system_ext/etc/hyper_fonts.xml:hyper_fonts"
  "/product/etc/fonts_customization.xml:fonts_customization"
)
info "拉取设备上的字体配置…"
for entry in "${OEM_FILES[@]}"; do
  remote="${entry%%:*}"; base="${entry##*:}"
  A pull "$remote" "$BUILD/oem/$base.xml" >/dev/null 2>&1 \
    || die "拉取失败: $remote（该机型可能没有这个文件）"
  echo "    $remote -> oem/$base.xml"
done

# ---- 2. 打补丁 ----
info "生成 chalk 模式配置…"
for base in miui_font_fallback miui_fonts hyper_font_fallback hyper_fonts; do
  python3 "$REPO_ROOT/tools/patch_font_config.py" \
    "$BUILD/oem/$base.xml" "$BUILD/oem/$base.patched.xml" 1
done
python3 "$REPO_ROOT/tools/patch_font_customization.py" \
  "$BUILD/oem/fonts_customization.xml" "$BUILD/oem/fonts_customization.patched.xml" --no-probe

info "生成 optional 模式配置…"
for base in miui_font_fallback miui_fonts; do
  python3 "$REPO_ROOT/tools/patch_font_config.py" \
    "$BUILD/oem/$base.xml" "$BUILD/optional/$base.optional.xml" 1 --extra-only
done

# ---- 3. 推送 ----
info "推送到设备暂存区 $STAGE_REMOTE …"
A shell "mkdir -p $STAGE_REMOTE"
A push "$FONT" "$STAGE_REMOTE/HanyiSentyChalkOriginal.ttf" >/dev/null
for base in miui_font_fallback miui_fonts hyper_font_fallback hyper_fonts fonts_customization; do
  A push "$BUILD/oem/$base.patched.xml" "$STAGE_REMOTE/$base.patched.xml" >/dev/null
done
for base in miui_font_fallback miui_fonts; do
  A push "$BUILD/optional/$base.optional.xml" "$STAGE_REMOTE/$base.optional.xml" >/dev/null
done
A push "$REPO_ROOT/magisk/install_magisk_module.sh" /data/local/tmp/install_magisk_module.sh >/dev/null

# ---- 4. 装模块 ----
info "安装 Magisk 模块…"
A shell "su -c 'sh /data/local/tmp/install_magisk_module.sh'"

# ---- 5. 重启 ----
if [ "$REBOOT" = "1" ]; then
  info "重启设备…"
  A reboot
  echo "重启后用下面任一方式切换字体："
  echo "  手机上: 打开 Termux 输入  oit-font"
  echo "  电脑上:  adb shell su -c '/data/adb/oit-font chalk'"
else
  echo "已跳过重启。用下面任一方式立即生效："
  echo "  adb shell su -c '/data/adb/oit-font chalk'"
fi

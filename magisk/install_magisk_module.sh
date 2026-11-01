#!/system/bin/sh
# ============================================================================
#  在已 root 的 HyperOS 设备上安装「汉仪新蒂黑板报体底字」为全局系统字体
#
#  运行时真正生效的字体配置（2026-10-31 红米 K50 Ultra 实测）
#  ---------------------------------------------------------------------------
#      /system_ext/etc/miui_font_fallback.xml   ← fallback 家族清单
#      /system_ext/etc/miui_fonts.xml           ← 命名家族清单
#      /product/etc/fonts_customization.xml    ← mitype / miuiex 家族
#      /product/fonts/MiSansVF.ttf             ← MIUI 主题引擎的「系统字体」槽位
#
#  /system/etc/fonts.xml 在 Android 15 上不被 FontManagerService 采用（实测改写后
#  dumpsys font 里 HanyiSentyChalk 零命中），所以本模块不再覆盖它 —— 顺带把
#  MIUI 主题商店的「系统字体」切换功能恢复原状。
#
#  Kitsune Mask 不支持 system_ext/ 覆盖，上述 5 个文件用 post-fs-data.sh 里的
#  `mount -o bind` 挂载改写版。
#
#  三种模式（state 文件控制，开机自动生效）
#  ---------------------------------------------------------------------------
#      chalk     全局黑板报体（默认）
#      optional  系统默认仍是 MiSans，只额外注册一个具名家族
#                 "Hanyi Senty Chalk Original"，供支持字体选择的 App 按名选用
#      stock     完全恢复原厂（卸载所有 bind）
#
#  回滚：rm -rf /data/adb/modules/oit-senty-font && reboot
# ============================================================================
set -e

MODID="oit-senty-font"
MODDIR="/data/adb/modules/$MODID"
STAGE="/data/local/tmp/oit-font"
TTF="HanyiSentyChalkOriginal.ttf"

PATCHED="miui_font_fallback miui_fonts hyper_font_fallback hyper_fonts fonts_customization"
OPTIONAL="miui_font_fallback miui_fonts"

[ "$(id -u)" = "0" ] || { echo "需要 root" >&2; exit 1; }
[ -f "$STAGE/$TTF" ] || { echo "缺少 $STAGE/$TTF" >&2; exit 2; }
for f in $PATCHED; do
  [ -f "$STAGE/$f.patched.xml" ] || { echo "缺少 $STAGE/$f.patched.xml" >&2; exit 3; }
done
for f in $OPTIONAL; do
  [ -f "$STAGE/$f.optional.xml" ] || { echo "缺少 $STAGE/$f.optional.xml" >&2; exit 4; }
done

echo "== 卸载上一版留下的 bind mount =="
# 不先 umount 的话，$MODDIR/system/fonts/HanyiSentyChalkOriginal.ttf 是
# /product/fonts/MiSansVF.ttf 的 bind 源，rm 会报 Device or resource busy
for f in miui_font_fallback miui_fonts hyper_font_fallback hyper_fonts; do
  umount "/system_ext/etc/$f.xml" 2>/dev/null || true
done
umount /product/etc/fonts_customization.xml 2>/dev/null || true
umount /product/fonts/MiSansVF.ttf 2>/dev/null || true

echo "== 备份原始字体配置 =="
mkdir -p "$MODDIR/backup"
for p in /system_ext/etc/miui_font_fallback.xml /system_ext/etc/miui_fonts.xml \
         /system_ext/etc/hyper_font_fallback.xml /system_ext/etc/hyper_fonts.xml \
         /product/etc/fonts_customization.xml; do
  [ -f "$p" ] && cp -a "$p" "$MODDIR/backup/$(basename "$p").orig" 2>/dev/null || true
done
cp -a /system/etc/fonts.xml "$MODDIR/backup/system_etc_fonts.xml.orig" 2>/dev/null || true

echo "== 建立模块目录 =="
rm -rf "$MODDIR/system" "$MODDIR/system_ext" "$MODDIR/patched" "$MODDIR/optional"
mkdir -p "$MODDIR/system/fonts" "$MODDIR/patched" "$MODDIR/optional"

# 字体本体（systemless → /system/fonts/，配置里按名字引用它）
cp "$STAGE/$TTF" "$MODDIR/system/fonts/$TTF"

# chalk 模式配置
for f in $PATCHED; do
  cp "$STAGE/$f.patched.xml" "$MODDIR/patched/$f.xml"
done

# optional 模式配置（原厂 + 一个具名家族）
for f in $OPTIONAL; do
  cp "$STAGE/$f.optional.xml" "$MODDIR/optional/$f.xml"
done

# apply.sh：按模式挂载/卸载配置，post-fs-data.sh 与 oit-font 切换脚本共用
cat > "$MODDIR/apply.sh" <<'EOF'
#!/system/bin/sh
MODDIR=/data/adb/modules/oit-senty-font
BB=/data/adb/magisk/busybox
MODE="${1:-$(cat "$MODDIR/state" 2>/dev/null)}"
[ -z "$MODE" ] && MODE=chalk
MNT() {
  [ -f "$1" ] && [ -f "$2" ] || return 0
  if [ -x "$BB" ]; then
    "$BB" mount -o bind "$1" "$2" 2>/dev/null || "$BB" mount --bind "$1" "$2" 2>/dev/null || true
  else
    mount -o bind "$1" "$2" 2>/dev/null || mount --bind "$1" "$2" 2>/dev/null || true
  fi
}
UNMNT() {
  umount "$1" 2>/dev/null || true
  umount -l "$1" 2>/dev/null || true
}
# 先全部卸载，回到出厂状态
for f in miui_font_fallback miui_fonts hyper_font_fallback hyper_fonts; do
  UNMNT "/system_ext/etc/$f.xml"
done
UNMNT /product/etc/fonts_customization.xml
UNMNT /product/fonts/MiSansVF.ttf
# 再按模式挂载
case "$MODE" in
  chalk)
    for f in miui_font_fallback miui_fonts hyper_font_fallback hyper_fonts; do
      MNT "$MODDIR/patched/$f.xml" "/system_ext/etc/$f.xml"
    done
    MNT "$MODDIR/patched/fonts_customization.xml" "/product/etc/fonts_customization.xml"
    MNT "$MODDIR/system/fonts/HanyiSentyChalkOriginal.ttf" "/product/fonts/MiSansVF.ttf"
    ;;
  optional)
    MNT "$MODDIR/optional/miui_font_fallback.xml" "/system_ext/etc/miui_font_fallback.xml"
    MNT "$MODDIR/optional/miui_fonts.xml" "/system_ext/etc/miui_fonts.xml"
    ;;
  stock) ;;
esac
echo "$MODE" > "$MODDIR/state"
EOF

# post-fs-data.sh：开机时按 state 应用
cat > "$MODDIR/post-fs-data.sh" <<'EOF'
#!/system/bin/sh
MODDIR=/data/adb/modules/oit-senty-font
sh "$MODDIR/apply.sh" "$(cat "$MODDIR/state" 2>/dev/null || echo chalk)"
EOF

# 用户侧切换脚本：/data/adb/oit-font {chalk|optional|stock|status}
cat > "$MODDIR/oit-font" <<'EOF'
#!/system/bin/sh
MODDIR=/data/adb/modules/oit-senty-font
[ "$(id -u)" = "0" ] || exec su -c "$0 $*"
case "$1" in
  chalk|optional|stock)
    sh "$MODDIR/apply.sh" "$1"
    echo "正在重启系统界面使字体生效（约 20 秒）…"
    sleep 1
    stop; start
    ;;
  status)
    echo "当前字体模式: $(cat "$MODDIR/state" 2>/dev/null)"
    ;;
  *)
    echo "用法: oit-font {chalk|optional|stock|status}"
    echo "  chalk     全局黑板报体底字"
    echo "  optional  系统默认保持 MiSans，额外注册具名家族 'Hanyi Senty Chalk Original'"
    echo "  stock     恢复原厂字体"
    exit 1
    ;;
esac
EOF

chmod 0755 "$MODDIR/apply.sh" "$MODDIR/post-fs-data.sh" "$MODDIR/oit-font"
chmod 0644 "$MODDIR/system/fonts/$TTF" "$MODDIR/patched"/*.xml "$MODDIR/optional"/*.xml
chown -R 0:0 "$MODDIR/system" "$MODDIR/patched" "$MODDIR/optional" \
           "$MODDIR/apply.sh" "$MODDIR/post-fs-data.sh" "$MODDIR/oit-font"

cat > "$MODDIR/module.prop" <<'EOF'
id=oit-senty-font
name=OIT Senty Chalk Original Font
version=v3.0
versionCode=3
author=oit-net-portal
description=用汉仪新蒂黑板报体底字(Hanyi Senty Chalk Original)替换全局 sans-serif / zh-Hans / zh-Hant 字体，支持 chalk/optional/stock 三种模式切换
EOF

# Magisk: 存在 update 文件 = 模块待启用; 删除 disable = 启用
rm -f "$MODDIR/disable" "$MODDIR/remove"
: > "$MODDIR/update"

# 默认模式：chalk（保留之前的状态则沿用）
[ -f "$MODDIR/state" ] || echo chalk > "$MODDIR/state"

# 用户脚本放到 /data/adb/，方便直接调用
cp "$MODDIR/oit-font" /data/adb/oit-font
chmod 0755 /data/adb/oit-font

echo "== 模块内容 =="
ls -l "$MODDIR" "$MODDIR/patched" "$MODDIR/optional" "$MODDIR/system/fonts"
echo
echo "OK: 模块已就绪，重启后生效。当前模式: $(cat "$MODDIR/state")"
echo "切换命令: adb shell su -c '/data/adb/oit-font chalk|optional|stock'"

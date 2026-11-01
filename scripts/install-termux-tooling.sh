#!/usr/bin/env bash
#
# install-termux-tooling.sh —— 把字体切换工具装进手机的 Termux
#
# 装完手机上就有：
#   oit-font          交互式切换字体（菜单）
#   oit-font status   查当前模式
#   fh                常用命令速查表（~/TERMUX-NOTES.md）
#   ~/.bashrc         加了 ~/bin 到 PATH + 每次开终端一行提醒
#
# 用法：
#   ./scripts/install-termux-tooling.sh [--serial <serial>]
#
# 幂等：可以重复执行。
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ADB="${ADB:-adb}"
SERIAL=""

while [ $# -gt 0 ]; do
  case "$1" in
    --serial) SERIAL="${2:?}"; shift 2 ;;
    --adb)    ADB="${2:?}"; shift 2 ;;
    -h|--help) sed -n '2,16p' "$0"; exit 0 ;;
    *) echo "未知参数: $1" >&2; exit 1 ;;
  esac
done

if [ -z "$SERIAL" ]; then
  mapfile -t DEVICES < <("$ADB" devices | awk 'NR>1 && $2=="device" {print $1}')
  [ "${#DEVICES[@]}" -eq 1 ] || { echo "需要恰好一台设备在线；用 --serial 指定" >&2; exit 1; }
  SERIAL="${DEVICES[0]}"
fi
A() { "$ADB" -s "$SERIAL" "$@"; }

A shell "su -c 'id -u'" | grep -q 0 || { echo "设备未 root" >&2; exit 1; }
A shell pm list packages | grep -q "com.termux" || { echo "设备未安装 Termux" >&2; exit 1; }

TERMUX_UID=$(A shell dumpsys package com.termux | grep -oE "userId=[0-9]+" | head -1 | cut -d= -f2)
[ -n "$TERMUX_UID" ] || { echo "取不到 Termux uid" >&2; exit 1; }

TH="/data/data/com.termux/files/home"
TP="/data/data/com.termux/files/usr"
TMP="/data/local/tmp/oit-font-tooling"

echo "==> 推送文件到 $TMP"
A shell "rm -rf $TMP && mkdir -p $TMP"
A push "$REPO_ROOT/bin/oit-font"                  "$TMP/oit-font"                  >/dev/null
A push "$REPO_ROOT/bin/font-help"                 "$TMP/font-help"                 >/dev/null
A push "$REPO_ROOT/bin/fnote"                     "$TMP/fnote"                     >/dev/null
A push "$REPO_ROOT/share/TERMUX-NOTES.md"         "$TMP/TERMUX-NOTES.md"            >/dev/null
A push "$REPO_ROOT/share/bashrc-block.sh"         "$TMP/bashrc-block.sh"            >/dev/null
A push "$REPO_ROOT/scripts/patch-termux-bashrc.sh" "$TMP/patch-termux-bashrc.sh"    >/dev/null

echo "==> 安装到 Termux"
A shell "su -c '
  set -e
  mkdir -p $TH/bin
  cp $TMP/oit-font        $TP/bin/oit-font
  cp $TMP/font-help       $TP/bin/font-help
  cp $TMP/fnote           $TP/bin/fnote
  cp $TMP/oit-font        $TH/bin/oit-font
  cp $TMP/font-help       $TH/bin/font-help
  cp $TMP/fnote           $TH/bin/fnote
  cp $TMP/TERMUX-NOTES.md $TH/TERMUX-NOTES.md
  chmod 0755 $TP/bin/oit-font $TP/bin/font-help $TP/bin/fnote \
            $TH/bin/oit-font $TH/bin/font-help $TH/bin/fnote
  chmod 0600 $TH/TERMUX-NOTES.md
  sh $TMP/patch-termux-bashrc.sh $TH $TMP/bashrc-block.sh
  chown $TERMUX_UID:$TERMUX_UID $TP/bin/oit-font $TP/bin/font-help $TP/bin/fnote \
        $TH/bin/oit-font $TH/bin/font-help $TH/bin/fnote $TH/TERMUX-NOTES.md \
        $TH/.bashrc $TH/.profile 2>/dev/null || true
  rm -rf $TMP
'"

echo
echo "已安装："
echo "  $TP/bin/oit-font        （全局黑板报 / 可选字体 / 原厂 三档）"
echo "  $TP/bin/font-help       （速查表：目录 / 按节 / 搜索）"
echo "  $TP/bin/fnote           （往速查表里追加自己的笔记）"
echo "  $TH/TERMUX-NOTES.md     （速查表内容，可自行编辑）"
echo "  $TH/.bashrc             （加了 ~/bin 到 PATH + 开终端一行提醒）"
echo
echo "手机上打开 Termux，输入："
echo "  oit-font    → 交互菜单"
echo "  fh          → 速查表目录（fh <章节> 看某一节，fh -s <词> 搜索）"
echo "  fnote <内容> → 记一条自己的笔记"
echo
echo "提示：如果 Termux 已经开着，重开一个终端（或执行 exec bash）让 .bashrc 生效。"

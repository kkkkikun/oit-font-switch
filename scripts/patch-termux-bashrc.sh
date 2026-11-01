#!/system/bin/sh
#
# patch-termux-bashrc.sh —— 在设备上幂等地给 Termux 的 ~/.bashrc / ~/.profile 打补丁
#
# 用法（在设备上以 root 执行）：
#   sh patch-termux-bashrc.sh <Termux_HOME_DIR> <block_file>
#
# 行为：
#   1. 把 <block_file> 的内容以标记块的形式写进 ~/.bashrc
#      （先删掉旧的同名块，再追加新块 —— 可重复执行，不会重复堆积）
#   2. 确保 ~/.profile 存在，且会让 login shell 也读到 ~/.bashrc
#
MARK_START='# >>> oit-font tooling >>>'
MARK_END='# <<< oit-font tooling <<<'

HOME_DIR="${1:?需要 Termux home 目录}"
BLOCK_FILE="${2:?需要 block 文件}"

BASHRC="$HOME_DIR/.bashrc"
PROFILE="$HOME_DIR/.profile"

[ -d "$HOME_DIR" ] || { echo "home 目录不存在: $HOME_DIR" >&2; exit 1; }
[ -f "$BLOCK_FILE" ] || { echo "block 文件不存在: $BLOCK_FILE" >&2; exit 1; }

# ---- 1. ~/.bashrc ----
if [ -f "$BASHRC" ]; then
  awk -v s="$MARK_START" -v e="$MARK_END" '
    index($0, s) { skip=1; next }
    index($0, e) { skip=0; next }
    !skip { print }
  ' "$BASHRC" > "$BASHRC.new"
else
  : > "$BASHRC.new"
fi
cat "$BLOCK_FILE" >> "$BASHRC.new"
mv "$BASHRC.new" "$BASHRC"
echo "已更新 $BASHRC"

# ---- 2. ~/.profile ----
# bash 只有在 login shell 时才会读 ~/.profile，而 Termux 的 shell
# 启动方式可能是 login 也可能不是，所以两边都保证能读到同一份配置。
if [ ! -f "$PROFILE" ]; then
  cat > "$PROFILE" <<'PROFILE_EOF'
# ~/.profile: executed by Bourne-compatible login shells.

if [ -n "$BASH_VERSION" ]; then
    if [ -f "$HOME/.bashrc" ]; then
        . "$HOME/.bashrc"
    fi
fi

mesg n 2> /dev/null || true
PROFILE_EOF
  echo "已创建 $PROFILE"
elif grep -q 'HOME/.bashrc' "$PROFILE"; then
  echo "$PROFILE 已会加载 ~/.bashrc，保持不变"
else
  cat >> "$PROFILE" <<'PROFILE_EOF'

# 让 login shell 也读到 ~/.bashrc（含 oit-font tooling 段）
if [ -n "$BASH_VERSION" ] && [ -f "$HOME/.bashrc" ]; then
    . "$HOME/.bashrc"
fi
PROFILE_EOF
  echo "已更新 $PROFILE（补上加载 ~/.bashrc）"
fi

exit 0

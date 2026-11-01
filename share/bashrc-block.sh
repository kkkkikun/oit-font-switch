# >>> oit-font tooling >>>
# 由 scripts/install-termux-tooling.sh 自动写入（幂等，可重复执行）
# 本段作用：把 ~/bin 放进 PATH、注册 fh 速查表别名、开终端时提醒一行

export PATH="$HOME/bin:$PATH"

alias fh='font-help'

# 防忘提醒：每次开一个交互式终端提示一行
if [ -n "$PS1" ]; then
    echo "[字体切换] oit-font 打开菜单   fh 看常用命令速查"
fi
# <<< oit-font tooling <<<

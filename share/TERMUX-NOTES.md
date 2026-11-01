# Termux 速查表

> 用法（手机上打开 Termux）：
>
> ```
> fh                # 目录：列出所有分类
> fh 字体切换        # 打印某一章（支持中文/英文关键字）
> fh -s 网络         # 全文搜索
> fh -a             # 全部内容
> fnote <内容>       # 追加一条我自己的笔记
> fnote -c 分类 <内容>  # 追加到指定分类
> ```
>
> `fh` 和 `fnote` 读的就是这个文件（`~/TERMUX-NOTES.md`），**你可以随便编辑**。
> 想加内容直接改这个文件，或者用 `fnote` 追加。

---

## 字体切换

```bash
oit-font              # 交互菜单（1=全局黑板报 2=可选字体 3=恢复原厂）
oit-font chalk        # 全局黑板报体底字
oit-font optional     # 系统默认 MiSans + 注册具名可选字体
oit-font stock        # 完全恢复原厂
oit-font status       # 当前模式 / bind 数 / 命中数 / sans-serif 落点
```

切换后系统界面重启一次，约 20 秒生效；**Termux 终端会短暂断开**（正常现象）。
开关机后仍按上次的模式自动生效。

| 模式 | 含义 | 适合 |
|---|---|---|
| `chalk` | 系统所有文字都是黑板报体 | 看小说、整套换风格 |
| `optional` | 系统默认 MiSans，额外注册 `Hanyi Senty Chalk Original` | 只在阅读器里用黑板报体 |
| `stock` | 完全原厂 | 不想看黑板报体 |

## 字体模块内部

```bash
su -c 'cat /data/adb/modules/oit-senty-font/state'          # 当前模式
su -c 'ls /data/adb/modules/oit-senty-font/'                 # 模块目录
su -c 'ls /data/adb/modules/oit-senty-font/patched/'         # chalk 配置
su -c 'ls /data/adb/modules/oit-senty-font/optional/'        # optional 配置
su -c 'ls /data/adb/modules/oit-senty-font/backup/'          # 原始 XML 备份
su -c 'md5sum /system/fonts/HanyiSentyChalkOriginal.ttf'     # 字体校验
su -c 'sh /data/adb/modules/oit-senty-font/apply.sh chalk'   # 手动应用（不重启 framework）
su -c 'mount | grep -E "on /system_ext/etc/(miui|hyper)|on /product/etc/fonts_customization|on /product/fonts/MiSansVF"'
```

| 项 | 值 |
|---|---|
| 模块 id | `oit-senty-font` v3.0 |
| 切换脚本 | `/data/adb/oit-font` |
| 字体文件 | `/system/fonts/HanyiSentyChalkOriginal.ttf` |
| md5 | `4350c7a43c8d7e5e4d82c4ccceb57b86` |
| 工具仓库 | `github.com/kkkkikun/oit-font-switch`（private） |

## 我的笔记

<!-- fnote 默认追加到这里 -->

## Termux 基础

```bash
pkg install <包名>          # 安装
pkg upgrade                 # 升级全部
pkg list-installed           # 看已装的
pkg search <关键词>          # 搜索
apt install <包名>           # apt 直装（不推荐，会让 pkg 状态错乱）

termux-setup-storage        # 开启共享存储 → /sdcard
termux-info                 # 看环境信息（版本、SDK、架构）
termux-open <文件>           # 用外部 App 打开
termux-open-url <url>       # 用浏览器打开
termux-wake-lock            # 保持屏幕常亮
termux-wake-unlock          # 取消常亮
termux-reload-settings      # 重载设置（改了 ~/termux/ 下的配置后）
termux-change-repo          # 换软件源

nohup <命令> &               # 后台跑，关终端也不死
jobs                        # 看后台任务
fg / bg                     # 切回 / 切到后台
```

已装且可用的基础包：`bash pkg apt nano git python pip curl ssh scp tar unzip
dos2unix diff patch lsof netstat traceroute dialog make clang openssl`。

**没装**（需要的话 `pkg install`）：`vim wget jq tmux fzf ripgrep rsync zip htop zsh`。
**没装 Termux:API**（所以 `termux-toast`、`termux-battery-status` 不能用），
**没装 Termux:Widget**（所以桌面没有 Termux 小组件）。
装了 **Termux:Boot**（`~/.termux/boot/` 放脚本，开机自动跑）。

## Termux 文件与编辑

```bash
nano <文件>                 # 编辑，Ctrl+O 保存，Ctrl+X 退出，Ctrl+W 删词
cat <文件>                  # 看内容
less <文件>                 # 翻页看（q 退出）
cp -r a b                   # 复制
mv a b                      # 移动/改名
rm -rf a                    # 删（-rf 慎用）
find . -name "*.txt"        # 找文件
du -sh <目录>               # 看大小
df -h                       # 看磁盘
chmod +x <文件>              # 加执行权限
dos2unix <文件>             # Windows 换行 → Unix（从 Windows 拷来的脚本必做）
diff a b                    # 比较
patch -p1 < fix.patch       # 打补丁
tar czf out.tar.gz <目录>    # 打包
tar xzf out.tar.gz          # 解压
unzip <文件>.zip            # 解 zip
lsof <文件>                 # 谁占着这个文件（Termux 的 lsof 不支持 -i）
```

路径速查：

| 路径 | 是什么 |
|---|---|
| `~` | `/data/data/com.termux/files/home` |
| `$PREFIX` | `/data/data/com.termux/files/usr` |
| `$TMPDIR` | `/data/data/com.termux/files/usr/tmp` |
| `~/bin` | 自己放脚本的地方（已在 PATH 里） |
| `~/.termux/boot/` | 开机自启脚本（Termux:Boot） |
| `/sdcard` | 手机共享存储（先跑 `termux-setup-storage`） |

## Termux 远程与网络

```bash
ssh 用户@主机                  # 连别人
scp 文件 用户@主机:/目标路径      # 传过去
scp 用户@主机:/文件 .          # 拉回来
ssh-keygen -t ed25519          # 生成密钥
ssh-copy-id 用户@主机           # 把公钥装过去（免密）

python3 -m http.server 8000    # 在当前目录开临时 HTTP 服务
curl http://127.0.0.1:8000/文件  # 取
curl -I <url>                  # 只看响应头
ssh -L 8080:127.0.0.1:80 主机    # 本地端口转发
ssh -R 8080:127.0.0.1:80 主机    # 反向端口转发

ping -c4 10.3.116.1            # 连通性（/system/bin/ping，免 root 可用）
traceroute <主机>               # 路由路径
netstat -tlnp                  # 看监听端口
```

## 系统命令（免 root，实测可用）

```bash
getprop ro.product.model        # 机型
getprop ro.build.version.release # Android 版本
getprop ro.build.version.sdk     # SDK 号
pm list packages                # 全部包
pm list packages -3             # 第三方包
pm path com.oitnetportal         # APK 路径
am start -a android.settings.SETTINGS          # 打开设置
am start -n <包名>/<Activity>                   # 打开指定界面
settings get system screen_off_timeout          # 读系统设置
ping -c4 <主机>                                 # 连通性
logcat -d                                       # 只能看自己 App 的日志
```

## 系统命令（需要 root）

```bash
su -c 'dumpsys font | grep -c HanyiSentyChalkOriginal'   # 字体命中数
su -c 'dumpsys battery'                                  # 电池
su -c 'screencap -p /data/local/tmp/s.png'               # 截图
su -c 'input keyevent 26'                                # 电源键
su -c 'input text "hello"'                               # 模拟输入
su -c 'svc power stayon true'                            # 充电时保持常亮
su -c 'settings put system screen_brightness 255'       # 改亮度
su -c 'settings put system screen_brightness_mode 1'     # 亮度改自动
su -c 'settings put system screen_off_timeout 30000'     # 息屏 30 秒
su -c 'pm install -r /data/local/tmp/x.apk'              # 装包
su -c 'mount | grep fonts'                               # 看字体挂载
su -c 'logcat -d | grep -i xxx'                         # 全量日志
su -c 'wm size && wm density'                            # 分辨率/密度
su -c 'cat /proc/meminfo | head -3'                      # 内存
su -c 'uptime'                                           # 开机时长
```

> 免 root 时 `dumpsys` / `screencap` / `svc` 都会被系统拒掉
> （实测报 `Permission Denial` / `Failed to take screenshot`），所以一律走 `su -c`。

## 屏幕与显示

```bash
# 截图（电脑端）
adb shell screencap -p /data/local/tmp/s.png
adb pull /data/local/tmp/s.png D:/tmp/s.png       # 二进制必须 pull，别用 exec-out

# 录屏
adb shell screenrecord --time-limit 30 /data/local/tmp/v.mp4
adb pull /data/local/tmp/v.mp4 D:/tmp/v.mp4

# 亮度 / 息屏 / 常亮
su -c 'settings put system screen_brightness_mode 1'   # 自动亮度
su -c 'settings put system screen_off_timeout 30000'   # 息屏 30 秒
su -c 'svc power stayon true'                          # 充电常亮
su -c 'input keyevent 26'                              # 手动息屏/点亮
```

## 无线 ADB（免 USB 线）

Android 11+（本机 SDK 35）两种方式：

```bash
# 方式一：开发者选项 → 无线调试 → 用配对码配对（推荐）
adb pair <手机IP>:<配对端口>
adb connect <手机IP>:<调试端口>
adb devices

# 方式二：先插一次 USB，然后
adb tcpip 5555
adb connect <手机IP>:5555
```

查手机 IP：设置 → WLAN → 点已连的网 → IP 地址；或 Termux 里
`ip -4 addr show wlan0 | grep inet`（需要 root）。

断开：`adb disconnect <手机IP>:端口`。

## 常用 adb 命令

```bash
adb devices -l                       # 设备列表
adb -s <serial> <命令>               # 指定设备
adb shell <命令>                      # 普通 shell
adb shell su -c '<命令>'              # root shell
adb push <本地> <设备>                # 推
adb pull <设备> <本地>                # 拉
adb install -r <apk>                  # 覆盖安装（-g 一并授予运行时权限）
adb uninstall <包名>                   # 卸载
adb logcat                           # 实时日志
adb reboot                           # 重启
adb reverse tcp:8000 tcp:8000        # 反向端口（手机 → 电脑）
adb forward tcp:8000 tcp:8000        # 正向端口（电脑 → 手机）
```

## 设备信息速查

```bash
getprop ro.product.model             # 22081212C
getprop ro.build.version.release     # 15
getprop ro.build.version.sdk         # 35
su -c 'wm size'                      # 分辨率
su -c 'wm density'                   # 密度
su -c 'dumpsys battery'              # 电池
su -c 'cat /proc/meminfo | head -3'  # 内存
su -c 'cat /proc/cpuinfo | head -20' # CPU
df -h                                # 存储
uptime                               # 运行时长
ip -4 addr show wlan0                # 本机 IP（需 root）
```

## Magisk / Root

```bash
su -c id                            # 确认 root 生效
su                                  # 进 root shell（exit 退出）
ls /data/adb/modules/               # 所有模块
ls /data/adb/modules/<id>/          # 模块内容
su -c 'touch /data/adb/modules/<id>/disable'   # 停用某模块
su -c 'rm -rf /data/adb/modules/<id>/'         # 删模块
```

- 管理器 App：**Kitsune Mask**（包名 `io.github.huskydg.magisk`）
- 模块里的 `action.sh` 会在管理器里显示「操作」按钮，但该管理器**没有终端**，
  只能跑固定脚本弹输出框，做不了交互菜单 —— 所以交互切换走 Termux。
- 装了 LSPosed（`org.lsposed.manager`）和 Shizuku（`moe.shizuku.privileged.api`）。

## 校园网 OIT-Net-Portal

```bash
oit-portal status     # 三态探测
oit-portal once       # 完整登录（退出码 0/1/2/3）
oit-portal daemon     # 守护循环
oit-portal capture    # 抓包向导，自动发现协议
oit-portal configure  # 交互配置账号
```

| 项 | 值 |
|---|---|
| Android App 包名 | `com.oitnetportal`（已装在红米） |
| 配置目录 | `~/.config/oit-portal/`（凭据 + 抓包协议） |
| 文件 | `credentials.toml` `protocol.json` `session.json` `config.toml` |
| 仓库 | `github.com/kkkkikun/OIT-Net-Portal` |

> 旧的 Termux Python 脚本已卸载（`~/.termux/boot/oit-portal` 也删了，否则会复活），
> 但 `~/.config/oit-portal/` 凭据与协议**保留**着，迁移到 App 还要用。
> 安全约定：密码只存 `credentials.toml` 或 `OIT_PORTAL_PASSWORD`，日志只走 `log.fingerprint()`。

## 看小说的 App

手机上已装：`com.aareader`（阅读）、`com.dragon.read`（番茄免费小说）、
`com.linovelib.webapp`（轻之国度）、`com.manchuan.tools`（漫客）。

切到 `optional` 模式后，这些 App 的「字体」设置里可以选到
**`Hanyi Senty Chalk Original`**（系统 UI 仍是 MiSans）。

> 注意：只有 App 自己支持字体列表才行。有些阅读器只跟随系统字体，
> 那就得用 `chalk` 全局模式。

## 效率技巧

```bash
history                 # 历史
history | grep 字体      # 翻历史
!!                      # 重复上一条
!$                      # 上一条命令的最后一个参数
Ctrl+R                  # 反向搜索历史
Ctrl+A / Ctrl+E         # 行首 / 行尾
Ctrl+W                  # 删一个词
Ctrl+L                  # 清屏
alias ll='ls -alF'      # 别名
cmd | tee out.txt       # 边看边存
sh -c 'a && b'          # 串起来跑
```

## 故障排查

| 现象 | 处理 |
|---|---|
| `oit-font` 提示 command not found | 没装或不在 PATH。跑 `scripts/install-termux-tooling.sh` 重装 |
| `oit-font` 提示找不到字体模块 | Magisk 模块没了，跑 `scripts/bootstrap.sh` 重装 |
| 切换后终端直接断 | 正常 —— framework 重启会杀掉 Termux，重开即可 |
| `su` 弹授权框 | 点「永久允许」 |
| 切到 stock 后中文还是黑板报 | 是 App 自带字体。系统层已原厂（`oit-font status` 看 sans-serif 落点） |
| `dumpsys` 报 Permission Denial | 免 root 不行，改 `su -c 'dumpsys ...'` |
| `screencap` 报 Failed to take screenshot | 同上，改 `su -c` |
| `ping` 不通但 `adb` 能连 | adb 走 USB/无线通道，ping 走 wlan0，路由不同 |
| Termux 里 `pip install` 报错 | 外部管理的环境（PEP 668）。用 `pip install --break-system-packages` 或建 venv |
| 字体改了但某个 App 不变 | 该 App 硬编码了自己的字体，或缓存了 typeface |

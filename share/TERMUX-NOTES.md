# Termux 常用命令速查

> 这张表就是用来防忘的。在 Termux 里输入 `fh` 随时调出来。
> 表格文件就在 `~/TERMUX-NOTES.md`，想加内容直接编辑它。

---

## 一、字体切换（汉仪新蒂黑板报体底字）

```bash
oit-font              # 交互菜单：1=全局黑板报 2=可选字体 3=恢复原厂
oit-font chalk        # 直接切到全局黑板报体
oit-font optional     # 系统默认 MiSans + 注册一个可选字体供 App 按名选用
oit-font stock        # 完全恢复原厂
oit-font status       # 看当前模式 / bind 数 / 命中数 / sans-serif 落点
fh                    # 调出这张速查表
```

切换后系统界面会重启一次，**约 20 秒生效**；本终端会短暂断开，属正常现象。
开关机后仍按上次的模式自动生效。

---

## 二、字体模块本身

| 项 | 值 |
|---|---|
| Magisk 模块 | `/data/adb/modules/oit-senty-font/` |
| 当前模式 | `cat /data/adb/modules/oit-senty-font/state` |
| 切换脚本 | `/data/adb/oit-font {chalk\|optional\|stock\|status}` |
| 字体文件 | `/system/fonts/HanyiSentyChalkOriginal.ttf` |
| 命令本体 | `~/bin/oit-font`（另有副本在 `$PREFIX/bin/oit-font`） |

想看模块原始配置（`patched/` 是 chalk 模式，`optional/` 是可选字体模式）：

```bash
su -c 'cat /data/adb/modules/oit-senty-font/patched/miui_fonts.xml' | head -40
```

---

## 三、电脑端 ADB（手机没连电脑时用不了）

```bash
adb devices -l                                  # 看设备
adb shell su -c '/data/adb/oit-font chalk'      # 切换
adb shell su -c '/data/adb/oit-font status'     # 查状态
adb shell 'dumpsys font' | grep -c HanyiSentyChalkOriginal   # 命中数
adb shell su -c 'mount | grep -cE "on /system_ext/etc/(miui|hyper)|on /product/etc/fonts_customization|on /product/fonts/MiSansVF"'
```

> ADB 必须用 Windows 版 `adb.exe`（WSL 原生 adb 服务端起不来）。
> `adb pull` 拉二进制文件必须用 `pull`，不能用 `exec-out`（会把 LF 转成 CRLF）。

---

## 四、校园网 App（OIT-Net-Portal）

| 项 | 值 |
|---|---|
| 包名 | `com.oitnetportal` |
| 状态 | 已装在红米 K50 Ultra，验收暂缓 |
| 旧方案 | Termux Python 脚本已卸载；凭据与抓包协议保留在 `~/.config/oit-portal/` |

---

## 五、看小说的 App

手机上已装：`com.aareader`（阅读）、`com.dragon.read`（番茄免费小说）、
`com.linovelib.webapp`（轻之国度）、`com.manchuan.tools`（漫客）。

切到 `optional` 模式后，这些 App 的「字体」设置里可以选到
**`Hanyi Senty Chalk Original`**（系统 UI 仍是 MiSans）。

---

## 六、杂项

```bash
termux-wake-lock      # 保持屏幕常亮（Termux:API）
termux-open <url>     # 用默认浏览器打开
pkg search <关键词>    # 搜包
pkg install <包名>     # 装包
exit                  # 退出（Termux 会在后台保留会话）
```

---

## 七、常见问题

| 现象 | 原因 / 处理 |
|---|---|
| 输入 `oit-font` 提示 command not found | 脚本没装或 PATH 里没有；跑 `scripts/install-termux-tooling.sh` 重装 |
| 提示「找不到字体模块」 | Magisk 模块没装或被删；跑 `scripts/bootstrap.sh` 重装 |
| 切换后终端直接断 | 正常 —— framework 重启会杀掉 Termux，重新打开即可 |
| `su` 弹授权 | 点「永久允许」 |
| 切到 stock 后中文还是黑板报 | 有 App 自带字体；系统层已是原厂（`oit-font status` 看 sans-serif 落点） |

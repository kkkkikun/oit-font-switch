# 验收记录

- 日期：2026-10-31 ~ 2026-11-01
- 设备：Redmi K50 Ultra（22081212C / diting），HyperOS 2，Android 15（SDK 35）
- Root：Kitsune Mask 27001
- 模块：`oit-senty-font` v3.0（versionCode=3）
- 字体本体 md5：`4350c7a43c8d7e5e4d82c4ccceb57b86`

---

## 一、验收总表

| # | 项目 | 结果 |
|---|---|---|
| 1 | 定位运行时真正生效的字体配置 | ✅ |
| 2 | 排除 `/system/etc/fonts.xml`（不被采用） | ✅ |
| 3 | 6 个生效点 bind 覆盖 | ✅ |
| 4 | 全局渲染生效（`dumpsys font` 20 处命中） | ✅ |
| 5 | `mitype*` / `miuiex*` 13 个家族全部改写 | ✅ |
| 6 | 垂直度量修正（位置偏下） | ✅ |
| 7 | 三模式切换（chalk / optional / stock） | ✅ |
| 8 | 开机自动应用（post-fs-data 读 state） | ✅ |
| 9 | 「可选字体」注册具名家族 | ✅ |
| 10 | 手机端直接切换（Termux `oit-font`） | ✅ |
| 11 | 加入 MIUI 字体列表 | ❌ 技术不可行（见 MECHANISM §8） |
| 12 | 回滚方案 | ✅ |

---

## 二、三模式切换实测

命令：`adb shell su -c '/data/adb/oit-font {chalk|optional|stock}'`，每次切换后等 28 秒复测。

| 模式 | `state` | bind 数 | Hanyi 命中 | `sans-serif` 落点 | 具名家族 `Hanyi Senty Chalk Original` |
|---|---|---|---|---|---|
| `chalk` | chalk | 6 | **20** | `/system/fonts/HanyiSentyChalkOriginal.ttf` | 0 |
| `optional` | optional | 2 | 1 | `/system/fonts/Roboto-Regular.ttf`（原厂） | **1 ✅** |
| `stock` | stock | 0 | 0 | `/system/fonts/Roboto-Regular.ttf`（原厂） | 0 |

切换方式：改挂载 → `stop; start` 重启系统界面，约 20 秒生效，不用重启手机。

### 2.1 `chalk` 模式 20 处命中的家族

`sans-serif`、`sans-serif-condensed`、无名拉丁默认族、`lang=""`、`lang="zh"`、
`lang="zh-Hans"`、`lang="zh-Hant"`，以及 `mitype` × 11 + `miuiex` × 2。

其余 150+ 个 Noto / 各文字族（emoji、阿拉伯语、藏文等）**一律未动**，回退链正常。

### 2.2 刻意未改的家族

`mitype-mono-*`（等宽）、`mitype-clock*`、`miclock-*`（锁屏艺术字 Beihaibei / SilkSerif 等）。
锁屏时钟数字仍为 MIUI 原造型，锁屏日期正文已是黑板报体。

### 2.3 开机自愈

重启后复核：`state=chalk`、6 个 bind、20 处 Hanyi 命中、
`/system/etc/fonts.xml` 仍是符号链接 → `/data/system/fonts/theme_webview/fonts.xml`（未被覆盖）。

---

## 三、手机端直接切换（Termux）

设备上已装 Termux v0.119.0-beta.3（F-Droid 版，DEBUGGABLE），
其 `su` 封装能拿到 root：`uid=0(root) gid=0(root) groups=0(root) context=u:r:magisk:s0`。

部署位置：

| 路径 | 说明 |
|---|---|
| `/data/data/com.termux/files/usr/bin/oit-font` | 主脚本（Termux 默认 PATH 内的 `$PREFIX/bin`） |
| `/data/data/com.termux/files/home/bin/oit-font` | 同一份副本（`~/bin` 惯例） |

实测（ADB 模拟真人输入）：

| 步骤 | 结果 |
|---|---|
| 从 Termux 身份跑 `oit-font status` | 正确读出当前模式 / bind 数 / 命中数 / sans-serif 落点 |
| 打开 Termux，输入 `oit-font` + 回车 | 菜单正常渲染 |
| 菜单输入 `1` | state → chalk，bind 2→6，命中 1→20，sans-serif → Hanyi |
| `Ctrl+C` 取消菜单 | 终端回到干净提示符 |
| 从 Termux 身份执行 `apply.sh` + 分离式重启 | state chalk→optional，bind 6→2，命中 20→1，systemui pid 变更（框架确实重启） |

### 3.7 速查表升级为真 CLI（2026-11-01）

原来的速查表只是一张静态 markdown。现在改成：**数据源就是可编辑的
`~/TERMUX-NOTES.md`，`fh` 解析它的 `##` 章节** —— 所以用户改完文件立刻生效。

| 命令 | 行为 | 本地实测 |
|---|---|---|
| `fh` | 章节目录（17 类） | ✅ |
| `fh <章节>` | 按序号 / 中文 / 英文关键字取节（精确 → 包含两级匹配） | ✅ |
| `fh -s <关键字>` | 全文搜索（按章节分组命中行） | ✅ |
| `fh -t` | 只看「我的笔记」 | ✅ |
| `fh -a` | 全部内容 | ✅ |
| `fnote <内容>` | 追加到「我的笔记」 | ✅ |
| `fnote -t <内容>` | 带时间戳追加 | ✅ |
| `fnote -c <章节> <内容>` | 追加到指定章节（**模糊匹配已有标题**，不存在则新建） | ✅ |
| `fnote -l` / `fnote -d` | 看 / 清空笔记（清空需确认） | ✅ |

### 3.8 速查表内容按设备实测分级

只读盘点设备后按**实际可用性**写，不收录没装的包：

| 结论 | 依据 |
|---|---|
| Termux 装了 `pkg/apt/git/python/pip/curl/ssh/scp/nano/dialog/lsof/netstat/traceroute/dos2unix/diff/patch/make/clang` | dpkg status 清单 |
| **没装** Termux:API（无 `termux-toast`/`termux-battery-status`） | `pm list packages` 只有 `com.termux` + `com.termux.boot` |
| **没装** Termux:Widget（无桌面小组件） | 同上 |
| 装了 Termux:Boot（开机自启） | `com.termux.boot` 在列 |
| `dumpsys` / `screencap` / `svc` **免 root 被拒** | 实测 `Permission Denial` / `Failed to take screenshot` / `Killed` |
| `getprop` / `pm` / `settings get` / `am start` / `ping` **免 root 可用** | 实测全部成功 |
| `lsof -i` 不支持（Termux 的 lsof 是精简版） | 实测 `Unknown option 'i'` |

速查表因此分成「系统命令（免 root，实测可用）」和「系统命令（需要 root）」两节，
避免照着敲却撞权限错误。

### 3.9 本地验证（未触碰设备）

| 验证项 | 方法 | 结果 |
|---|---|---|
| bashrc 补丁幂等 | 全新 home / 重复执行 3 次 / 带用户原有配置 / 已有 `.profile` | ✅ 4/4 |
| `fh` / `fnote` 全部子命令 | 用 `TERMUX_NOTES` 环境变量指向临时文件 | ✅ |
| 章节模糊匹配 | `-c "无线 ADB"` 正确命中「无线 ADB（免 USB 线）」 | ✅ |
| 新建章节 / 连续追加不破坏结构 | 追加 3 次后章节结构完好 | ✅ |
| 安装器设备端操作 | 用假目录复刻 `install-termux-tooling.sh` 的设备端命令块 | ✅ 产物齐全且可运行 |

> **设备侧状态**：`oit-font` 已装且实测可用；
> `fh` / `fnote` / 速查表 / `~/.bashrc` 提醒**尚未安装** ——
> 当时设备已让给另一个 Agent，只做了离线准备。
> 补装命令：`cd /mnt/d/oit-font-switch && ./scripts/install-termux-tooling.sh`（幂等）。

---

## 四、位置偏下问题的量化验收

| 指标 | 修正前 | 修正后 | 判定 |
|---|---|---|---|
| TextView 高度 | 115 px | 74 px | ✅ 收紧 41 px |
| 顶部留白 | 52 px | 11 px | ✅ 几乎消除 |
| 「我的设备」文字墨迹中心 | 1108 | **928** | ✅ |
| 同行图标中心 | 1089 | 929 | — |
| **文字 vs 图标中心差** | **+19 px（偏下）** | **−1 px（对齐）** | ✅ 与原厂 MiSans 排版一致 |

---

## 五、字体度量基准

| 字体 | asc | desc | 行高 | 中文墨迹 top / bottom |
|---|---|---|---|---|
| 黑板报底字（原版） | 1700 | -650 | 1.147em | 0.687 / -0.173 em |
| 黑板报底字（**修正版**） | 1797 | -826 | 1.281em | 同上（轮廓未动） |
| Noto Sans CJK SC（index 2） | 1.160em | -0.288em | 1.448em | 0.830 / -0.079 em |
| MiSansC 3.005 | 1.000em | -0.200em | 1.200em | 0.735 / +0.005 em |
| MitypeVF.ttf | — | — | — | 10,548 字节、107 个 cmap（仅拉丁，中文本就来自 Noto CJK） |

---

## 六、遗留说明

- MIUI 字体列表无法加入自定义条目 —— 替代方案（`optional` 模式 + `oit-font`）已落地。
- `miclock-*` 锁屏艺术字刻意未改。
- 授权：商业字体，个人非商业使用免费；商用须另行取得授权。

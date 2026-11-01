# oit-font-switch

在 **已 root 的 HyperOS / MIUI 设备**上一键把「汉仪新蒂黑板报体底字」设为全局系统字体，
并支持在**手机上直接切换**（黑板报体 / 原厂 / 只注册成可选字体三档）。

```
手机上：打开 Termux，输入  oit-font  →  交互菜单选 1 / 2 / 3
电脑上：adb shell su -c '/data/adb/oit-font chalk'
```

---

## 特性

- **全局生效**：`sans-serif` / `sans-serif-condensed` / `zh` / `zh-Hans` / `zh-Hant` /
  11 个 `mitype-*` / 2 个 `miuiex-*` 家族全部命中，覆盖系统设置、桌面、通知栏、系统 UI。
- **三档可切**：`chalk`（全局黑板报体）/ `optional`（系统默认仍是 MiSans，但注册一个具名
  可选字体供 App 按名选用）/ `stock`（完全恢复原厂）。切换约 20 秒生效，不用重启手机。
- **手机端入口**：在 Termux 里敲 `oit-font`，交互菜单切换，**不需要装任何新 App**。
- **垂直度量修正**：修正原字体 `^` 字形悬空导致的「文字整体偏下」，让文字与图标重新居中。
- **全 systemless**：Magisk 模块 + `mount -o bind`，不改动任何分区；删模块即完全还原。

---

## 环境要求

| 项 | 要求 |
|---|---|
| 系统 | Android 13+ / HyperOS 2 / MIUI（实测红米 K50 Ultra，HyperOS 2 / Android 15） |
| Root | Magisk 或 Kitsune Mask（需 `su`） |
| 手机端入口 | Termux（可选，用于交互切换；ADB 方式不需要） |
| 字体本体 | **需自行获取**，见下方「字体获取」 |

---

## 快速开始

### 1. 准备字体本体

**本仓库不包含字体文件。** 汉仪新蒂黑板报体底字是商业字体，
新蒂字体官网条款为「**个人非商业使用免费下载**」，商用须另行取得授权。

官网下载：`http://font.sentywed.com/index_htm_files/HanyiSentyChalk%202018.ttf`
（family `Hanyi Senty Chalk Original`，PostScript name `HanyiSentyChalkOriginal`）

> 注意区分：同目录另有 `SentyChalk.ttf`（family `SentyCHALK`）是「黑板报**体**」（素描描边风），
> **不是**「底字」，别用错。

### 2. 修正垂直度量（推荐）

原字体有个悬空的 `^` 字形，会把字体边界撑高，让 Android 在每行文字上方多留一大段空白，
表现为「文字整体偏下、与图标不同心」。`tools/fix_font_vertical_metrics.py` 只改度量表
（`head` / `hhea` / `OS/2`），**不翻译、不平移任何字形轮廓**：

```bash
pip install fonttools
python3 tools/fix_font_vertical_metrics.py HanyiSentyChalkOriginal.ttf HanyiSentyChalkOriginal.fixed.ttf
```

修正后：`head` bbox `y[-826, 1797]`，`hhea` asc 1797 / desc -826 / gap 0，行高 1.147em → 1.281em。
实测 TextView 高度 115px → 74px，顶部留白 52px → 11px，文字中心与图标中心偏差 +19px → −1px。

### 3. 部署

```bash
./scripts/bootstrap.sh --font /path/to/HanyiSentyChalkOriginal.fixed.ttf
```

脚本会：拉取设备上的 5 份运行时配置 → 打补丁 → 推送 → 安装 Magisk 模块 → 重启。

### 4. 手机上切换字体

```bash
./scripts/install-termux-tooling.sh
```

然后在手机上打开 **Termux**，输入：

```
oit-font
```

```
========================================
         黑 板 报 体  字 体 切 换
========================================
  当前模式: chalk  —— 全局黑板报体底字（系统所有文字都是黑板报体）

  1) chalk     全局黑板报体底字
  2) optional  系统默认仍是 MiSans，额外注册一个可选字体
               （阅读器等 App 可按名选用
                 "Hanyi Senty Chalk Original"）
  3) stock     完全恢复原厂字体

  切换后系统界面会重启一次，约 20 秒生效。
  （本终端会短暂断开，属正常现象）

请输入 1 / 2 / 3 后回车:
```

也可以直接带参数：

```bash
oit-font chalk       # 全局黑板报体
oit-font optional    # 系统默认 MiSans + 注册具名可选字体
oit-font stock       # 恢复原厂
oit-font status      # 当前模式 / bind 数 / 命中数 / sans-serif 落点
```

---

## 三种模式

| 模式 | 含义 | 适用场景 |
|---|---|---|
| `chalk` | 系统所有文字都是黑板报体 | 看小说、想要整套 UI 换风格 |
| `optional` | 系统默认仍是 MiSans，**额外注册**具名家族 `Hanyi Senty Chalk Original` | 只在支持自定义字体的 App（阅读器等）里用黑板报体，系统 UI 保持原厂 |
| `stock` | 完全恢复原厂 | 不想看到黑板报体 |

> `optional` 模式下，注册的是字体 `name` 表里的真实 family 名，
> 支持自定义字体的 App 可以在自己的「字体」设置里直接选到它。

---

## 卸载 / 回滚

```bash
# 轻度：切回原厂，不用卸载
adb shell su -c '/data/adb/oit-font stock'

# 彻底卸载模块
adb shell su -c 'rm -rf /data/adb/modules/oit-senty-font'
adb shell su -c 'rm -f /data/adb/oit-font'
adb reboot
```

因为全程 systemless + bind mount，**卸载模块后系统自动恢复原状**，无需手动还原任何文件。

---

## 目录结构

```
.
├── bin/
│   ├── oit-font                        # Termux 侧的切换命令（手机上用它）
│   └── font-help                       # 打印速查表（alias: fh）
├── magisk/install_magisk_module.sh     # Magisk 模块安装脚本（v3，三模式）
├── tools/
│   ├── patch_font_config.py            # 改写运行时字体配置（chalk / optional）
│   ├── patch_font_customization.py     # 移除 customization 里的同名家族
│   └── fix_font_vertical_metrics.py    # 修正垂直度量（位置偏下问题）
├── scripts/
│   ├── bootstrap.sh                    # 从零部署（拉配置→打补丁→装机）
│   ├── install-termux-tooling.sh       # 把 oit-font + 速查表装进手机的 Termux
│   └── patch-termux-bashrc.sh          # 设备端：幂等补丁 ~/.bashrc / ~/.profile
├── share/
│   ├── TERMUX-NOTES.md                 # 速查表内容（装到手机后可直接编辑）
│   └── bashrc-block.sh                 # 要写进 ~/.bashrc 的那一段
└── docs/
    ├── MECHANISM.md                    # 运行时机制逆向（踩坑记录）
    └── VALIDATION.md                   # 验收记录
```

### 防忘机制

`install-termux-tooling.sh` 会在手机上做三件事：

1. `oit-font` / `font-help` 装进 `$PREFIX/bin` 与 `~/bin`
2. 速查表落到 `~/TERMUX-NOTES.md` —— **你自己就能编辑**，想加什么加什么
3. 幂等地给 `~/.bashrc` 写一段（标记块，重复执行不会堆积）：
   把 `~/bin` 加进 PATH、注册 `alias fh='font-help'`、
   并且**每次开一个交互式终端时打印一行提醒**：

   ```
   [字体切换] oit-font 打开菜单   fh 看常用命令速查
   ```

`~/.profile` 也会被补上加载 `~/.bashrc` 的语句，
保证 bash 以 login shell 启动时同样生效。

---

## 原理速览

Android 15 / HyperOS 上真正被 FontManagerService 解析的是这几份配置：

| 文件 | 作用 | 字体文件解析目录 |
|---|---|---|
| `/system_ext/etc/miui_font_fallback.xml` | fallback 家族清单 | `/system/fonts/` |
| `/system_ext/etc/miui_fonts.xml` | 命名家族清单 | `/system/fonts/` |
| `/system_ext/etc/hyper_font_fallback.xml` | WebView / 主题用 | `/system/fonts/` |
| `/system_ext/etc/hyper_fonts.xml` | WebView / 主题用 | `/system/fonts/` |
| `/product/etc/fonts_customization.xml` | `mitype*` / `miuiex*` 原始注册处 | **仅 `/product/fonts/`** |
| `/product/fonts/MiSansVF.ttf` | MIUI 主题引擎「系统字体」链路终点 | — |

三个关键坑（都实测过，详见 `docs/MECHANISM.md`）：

1. **`/system/etc/fonts.xml` 不被采用** —— 存在 `font_fallback.xml` 时它被忽略。
   改它没有任何效果。
2. **`fonts_customization.xml` 只在 `/product/fonts/` 里解析字体文件** ——
   把家族内容换成装在 `/system/fonts/` 的字体会让这些家族**整族静默丢弃**。
   正确做法是从 customization 移除、改由主配置注册同名家族。
3. **Kitsune Mask 不支持 `system_ext/` 覆盖** —— 必须用
   `post-fs-data.sh` 里的 `mount -o bind`。

---

## 免责声明

- 本工具只操作**你自己设备**上的字体配置。
- 字体本体**不在本仓库内**，需自行从官网获取；商业使用须取得授权。
- 修改系统字体配置可能导致部分 App 显示异常；`stock` 模式可随时还原。

## License

MIT（仅覆盖本仓库的脚本与文档，不含任何字体文件）。

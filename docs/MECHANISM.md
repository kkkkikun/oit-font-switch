# 运行时机制逆向（HyperOS 2 / Android 15）

> 实机：红米 K50 Ultra（22081212C / diting）、HyperOS 2、Android 15（SDK 35）、Kitsune Mask 27001。
> 本文记录的是**实测结论**，不是推测；每条都附验证方式。

---

## 1. 真正被解析的是哪几份配置

Android 13+ 的 FontManagerService 在存在 `font_fallback.xml` 时走**新格式**，
`fonts.xml` 被忽略。HyperOS 2 上真正生效的是：

```
/system_ext/etc/miui_font_fallback.xml     ← fallback 家族清单
/system_ext/etc/miui_fonts.xml             ← 命名家族清单
/system_ext/etc/hyper_font_fallback.xml    ← WebView / 主题用
/system_ext/etc/hyper_fonts.xml            ← WebView / 主题用
/product/etc/fonts_customization.xml       ← mitype* / miuiex* 的原始注册处
/product/fonts/MiSansVF.ttf                ← MIUI 主题引擎「系统字体」链路终点
```

### 1.1 验证方法

`dumpsys font` 的「Named Family List」和「Dump Fallback Families」两段，
和 `miui_*` 两份文件里的家族**逐条吻合**（sans-serif→Roboto+wdth100、zh-Hans→NotoSansCJK、
und-Arab→NotoNaskhArabic…）；而 `hyper_*` 那份的 MiSans*/Noto* 内容完全对不上。

### 1.2 坑 1：`/system/etc/fonts.xml` 不被采用

**首轮方案就是死在这。** 当时改写了 `/system/etc/fonts.xml`（连带覆盖
`/system_ext/etc/hyper_fonts.xml`），重启后：

```
$ adb shell dumpsys font | grep -c HanyiSentyChalkOriginal
0
```

`sans-serif` 仍然是 Roboto —— 因为存在 `font_fallback.xml` 时 `fonts.xml` 被忽略。

**副作用（意外的好处）**：不覆盖 `/system/etc/fonts.xml`，
MIUI 主题商店的「系统字体」切换功能就保持原状，不会被这个模块破坏。

---

## 2. `fonts_customization.xml` 只认 `/product/fonts/`

AOSP 的 `customizationType="new-named-family"` 机制**只在 `/product/fonts/` 里解析字体文件**。

### 2.1 探针实验

往 customization 里塞两个一次性探针家族：

```xml
<family customizationType="new-named-family" name="oit-test-prod">
    <font weight="400" style="normal" postScriptName="MIUITypeface-M">MitypeVF.ttf</font>
</family>
<family customizationType="new-named-family" name="oit-test-sys">
    <font weight="400" style="normal" postScriptName="HanyiSentyChalkOriginal">HanyiSentyChalkOriginal.ttf</font>
</family>
```

- `MitypeVF.ttf` → 存在于 `/product/fonts/`
- `HanyiSentyChalkOriginal.ttf` → 存在于 `/system/fonts/`

重启后看 `dumpsys font`：**`oit-test-prod` 存活，`oit-test-sys` 消失**。

### 2.2 坑 2：整族静默丢弃

如果把 customization 里 `mitype*` / `miuiex*` 的字体内容直接换成黑板报体
（它装在 `/system/fonts/`），这 13 个家族会被**整族静默丢弃** ——
`dumpsys` 里 `mitype` / `miuiex` 直接消失，而不是「变成新字体」。

### 2.3 正确解法

1. 从 `fonts_customization.xml` **移除**这 13 个家族（`mitype-mono-*`、`mitype-clock*`、
   `miclock-*` 一律保留）；
2. 由**主配置**（`miui_font_fallback.xml` / `miui_fonts.xml`）注册同名家族 ——
   主配置的字体文件在 `/system/fonts/` 解析，指向黑板报体。

---

## 3. 字体文件解析目录

| 配置 | 解析目录 | 结论 |
|---|---|---|
| `miui_*` / `hyper_*`（主配置） | `/system/fonts/` | 黑板报体放这里即可 |
| `fonts_customization.xml` | **仅** `/product/fonts/` | 放 `/system/fonts/` 会整族丢失 |

MIUI 主题引擎的「系统字体」链路：

```
/system/fonts/MiSansVF_Overlay.ttf → /data/system/fonts/theme_webview/Roboto-Regular.ttf
                                   → /system/fonts/MiSansVF.ttf → /product/fonts/MiSansVF.ttf
```

主题商店换字体时改的是 `theme_webview/` 里的符号链接。本方案把
`/product/fonts/MiSansVF.ttf` 一并 bind 成黑板报体，切断这条链路。

---

## 4. 坑 3：Kitsune Mask 不支持 `system_ext/` 覆盖

实测重启后 `/system_ext/etc/hyper_fonts.xml` 仍是原始大小（90,506 字节），覆盖没生效。

**解决**：`post-fs-data.sh` 里用 `mount -o bind` 把改写版挂到目标路径。
`/data/adb/modules/<id>/post-fs-data.sh` 在 zygote 启动前执行，时机足够。

---

## 5. 家族压成单条 weight=400

原配置里 `sans-serif` 等是**可变字体**（MiSansVF + `wght` 轴），共 11 条 100~950 字重记录。

静态字体没有 `wght` 轴。如果保留 11 条记录，粗体请求会**精确命中 weight=700 那条**
而不做合成加粗 —— 粗体就废了。

压缩成单条 weight=400 后，系统对没有更粗字重的家族会自行合成粗体：

```xml
<family name="sans-serif">
    <font weight="400" style="normal" postScriptName="HanyiSentyChalkOriginal">HanyiSentyChalkOriginal.ttf</font>
</family>
```

（vivo 上 `sans-serif` 同样只有一条 weight=400，是一致的惯例。）

---

## 6. 垂直度量修正（「文字偏下」的根因）

### 6.1 症状

全局换成黑板报体后，文字整体偏下，与旁边的图标不同心。

### 6.2 根因

字体里 `^`（U+005E）的墨迹悬在基线上方 **1.52~1.60em**，把 `head` 表的字体边界撑到
`y[-826, 3271]`（upem 2048）。

Android 的 TextView 高度与基线位置按 `fTop` / `fBottom`（来自字体边界）计算，
而不是 `hhea` 的 ascent/descent，且默认 `includeFontPadding=true`：

```
TextView 高度   = fTop - fBottom
首行基线位置    = fTop
```

于是每个 TextView 顶部凭空多出 `3271 - 1406 = 1865` 单位 ≈ **0.91em ≈ 51px** 的空白，
正文被推到行的下沿。

### 6.3 修正

只改度量表，**不翻译、不平移任何字形轮廓**（`^` 这个异常字形除外）：

1. 把悬空的 `^` 平移回 em 框内（dy = -1889）
2. `head` bbox 收紧到 `y[-826, 1797]`
3. 同步 `hhea` / `OS/2`（asc 1797 / desc -826 / gap 0）

行高由 1.147em 调整为 1.281em。

### 6.4 效果

| 指标 | 修正前 | 修正后 |
|---|---|---|
| TextView 高度 | 115 px | **74 px** |
| 顶部留白 | 52 px | **11 px** |
| 「我的设备」文字墨迹中心 | 1108 | **928** |
| 同行图标中心 | 1089 | 929 |
| **差值** | **+19 px（偏下）** | **−1 px（对齐）** |

---

## 7. 三个生效点的分工

| 生效点 | 负责什么 |
|---|---|
| `miui_font_fallback.xml` | 无名默认家族、`lang=""`、`lang="zh"`、`zh-Hans`、`zh-Hant` 等语言族 |
| `miui_fonts.xml` | `sans-serif`、`sans-serif-condensed` 等命名家族 |
| `fonts_customization.xml` | 移除 `mitype*` / `miuiex*`（改由上面两份注册） |

三个都改，才能覆盖 MIUI 系统应用显式请求的家族（它们不走系统默认 `sans-serif`）。

---

## 8. 为什么进不了 MIUI 的「系统个性化 → 字体」列表

逐条实测：

| 尝试 | 结果 |
|---|---|
| 设置 → 系统个性化 → 字体 | 列表**写死**为 `MiSans` / `小米兰亭Pro` / `更多` |
| 点「更多」 | 跳主题商店「字体」分类，提示「网络不可用 点击屏幕重新加载」（需联网下载） |
| 设备唯一的字体类 overlay `com.android.theme.font.notoserifsource`（category=`android.theme.customization.font`） | 启用后列表**未出现新条目** → 列表不枚举任意 overlay |
| 设备是否有「小米兰亭Pro」字体文件 | **不存在**；点击后 `settings global` 无变化 |
| AOSP 可下载字体 provider 协议（`FontsContract.java`） | 系统以 `query = ?` 查 `content://<authority>/`，列 `_id/file_id/font_ttc_index/font_variation_settings/font_weight/font_italic/result_code`，再 `openFileDescriptor` 取可 mmap 的真实文件；非系统应用需证书校验 |
| 改写签名系统 APK | 不可行：签名不一致会导致系统启动失败 |
| `/system/xbin/setfont`、`loadfont` | 只是 busybox 符号链接（控制台字体），与 MIUI 字体切换无关 |

**结论**：MIUI 字体列表 = 内置写死项 + 主题商店**在线下载**。
要塞进自定义字体，唯一路径是自建主题商店 APK 并替换 `com.android.thememanager`
（需重签名 + 绕过签名校验），属高风险改动。

**替代方案**：`optional` 模式注册具名家族 + `oit-font` 一键切换。

---

## 9. 手机端入口为什么走 Termux

Magisk / Kitsune 管理器的模块「操作」按钮**不能**做交互菜单：
Kitsune 管理器（`io.github.huskydg.magisk`）的 manifest 里只有
`MainActivity` 和 `SuRequestActivity`，**没有 TerminalActivity**，
模块 action 只能跑固定脚本并弹输出框。

Termux 则可以：它的 `su` 封装能直接拿到 root（`uid=0(root) context=u:r:magisk:s0`），
交互式 shell 的 stdin 可用，天然适合做菜单。

### 9.1 实现上的两个坑

1. **模块存在性检查必须走 su**：`/data/adb` 只有 root 能 `stat`，
   非 root 上下文里 `[ -d /data/adb/modules/... ]` 恒为假。
2. **framework 重启会连带杀掉 Termux**：重启动作必须分离执行 ——
   `nohup sh -c 'sleep 2; stop; start' &`。
   Magisk 的 `su` 会把 shell 挂在自己的守护进程下，杀掉 Termux 不会影响它。

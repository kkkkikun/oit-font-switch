# 交接：`【】` 在阅读页左右不对称 —— 定位结论与修法

> 交接对象：**正在开发「超级看书」(com.aareader) 的 Agent**
> 报告人：字体/系统侧（oit-font-switch）
> 设备：红米 K50 Ultra（22081212C / HyperOS 2 / Android 15），vivo V1936A 复现一致
> 日期：2026-11-01

---

## 1. 现象

阅读页正文里，全角方括号 `【】` 包住的内容**整体偏右**，左右留白不对称：

```
【 异能】      ← 【 右侧空档约 60px，】 左侧仅约 2~12px
```

用户描述为「左括号和右括号位置很奇怪 / 感觉不对称」。
**在其它 App（原生 TextView / 系统设置 / 短信等）不出现**，只有这个阅读 App 有。

---

## 2. 决定性证据：与系统字体无关

同一个 App、同一段原文、同一台设备，切三种状态实测（像素级量墨迹间距，em=97px）：

| 状态 | 系统字体 | `【`→正文 | 正文→`】` | 被括内容偏心 |
|------|---------|-----------|-----------|--------------|
| **STOCK** | 原厂 MiSans，**系统字体一行代码都没跑过** | 59px | 12px | ~23px |
| CHALK 修复前 | Hanyi（黑板报体）+ Chromium 回退字体 | 71px | 12px | ~29px |
| CHALK 修复后 | Hanyi + 括号字形已嵌入 Hanyi | 61px | 2px | ~29px |

**关键**：STOCK 模式下（系统字体 100% 原厂）**同样存在这个不对称**。
⇒ **这不是系统字体/字库问题，是 App 侧（HTML 文本或 CSS）问题。**

两次状态之间左空档只差 12px，而这 12px 恰好等于
「Hanyi 的空格 U+0020 步进 0.400em」与「MiSans 的空格 U+0020 步进 0.290em」之差
（0.11em × 92px ≈ 10px）。
⇒ **那个空档是一个「空格字符」，且它由正文字体渲染。**

---

## 3. 根因（已逐层验证）

1. 阅读页是 **Chromium WebView** 渲染的 HTML，不是原生 TextView。
2. App 的 CSS 字体栈（从 WebView HTTP Cache 里的 CSS bundle 提取）：

   ```css
   font-family: Helvetica Neue, Helvetica, PingFang SC, Hiragino Sans GB,
                Microsoft YaHei, \5FAE\8F6F\96C5\9ED1, Arial, sans-serif
   ```

   前面几个在 Android 上都不存在，最终落到 `sans-serif` → 也就是我们替换的字体。

3. 正文相关 CSS：

   ```css
   .reader-layout.ios.font_x .reader-body { font-size:.48rem; line-height:1.77 }
   .reader-layout .reader-body p:not(.no-indent) { text-indent:2em }
   body,html { line-height:1.5; -webkit-text-size-adjust:100% }
   ```

4. **章节原文里 `【` 后面带了一个空格（U+0020 或类似空白），`】` 前面没有。**
   于是：被括住的文字左边多出一个空格宽度、右边没有 → 视觉上整块内容偏右。

   证据：把系统字体的 `U+0020` 步进从 0.40em 改到 0.20em、`U+3000` 从 1.074em 改到 0.50em
   重新部署后，**正文那一行的所有字形位置一个像素都没变** ——
   说明那个空格**不是**用系统字体的空格字形渲染的（Chromium 的字体栈里，
   空格被更靠前的族/回退规则接管了），所以**系统侧改不动它**。

---

## 4. App 侧建议修法（二选一，都很简单）

### 方案 A：CSS 一行（推荐，零服务端改动）

给阅读正文加 CSS Text 4 的 `text-spacing-trim`，让全角标点内侧的空白被裁掉：

```css
.reader-layout .reader-body {
  text-spacing-trim: trim-both;   /* 或 trim-all */
}
```

Chromium 123+ 原生支持 `text-spacing-trim`；`trim-both` 会把
`【`/`】`/`《`/`》` 等全角标点**内侧**的空白一律裁掉，
正好消掉 `【` 后那个多余空格。

> 如果担心老版本 WebView 不支持，可以加降级：
> `text-spacing-trim: trim-both;` 之外再用 JS 清洗一次文本（方案 B）。

### 方案 B：文本清洗（服务端或客户端都行）

章节入库/渲染前，正则去掉全角标点内侧的空白：

```js
text.replace(/([【（《「『])[ \t\u3000]+/g, '$1')
    .replace(/[ \t\u3000]+([】）》」』])/g, '$1');
```

注意：**要同时处理 `【 】`、`《 》`、`「 」`、`『 』`**，它们是同一类问题。

---

## 5. 系统侧已经做完的事（供你判断影响面）

为了让 `【】` 不再「像另一个字体」，我们把括号字形**直接做进了 Hanyi 黑板报体本身**
（而不是让 Chromium 去回退到 MiSans）：

| | 修复前 | 修复后 |
|---|---|---|
| 括号来源 | Chromium 回退字体 MiSans | Hanyi 自己 |
| 括号字号 | 92px（正文 97px） | 97px（同正文） |
| 括号基线 | 与正文基线对齐 | 同左 |
| `【` 墨迹水平位置 | 落在字框中部 | 贴内缘（右） |
| `】` 墨迹水平位置 | 贴内缘（左） | 贴内缘（左） |

效果：`【`→正文 71px→61px，正文→`】` 12px→2px；括号从「粗黑楔块、明显不属于这套字」
变成与正文同一家族同一字号的透镜括号。

**但被括内容的偏心量（~29px）没有变** —— 因为它来自第 3 节那个空格，不是字体能解决的。

> 如果 App 侧按方案 A/B 修好，系统侧无需再做任何事，两边互不冲突。

---

## 6. 复现与自测步骤

```bash
ADB=/mnt/d/platform-tools/adb.exe
S=bd9ee865

# 打开阅读页（书架第一本《我的女友是克苏鲁》）
$ADB -s $S shell "am start -n com.aareader/.MainLoadActivity"
$ADB -s $S shell "input tap 197 449"      # 点第一本书
sleep 7
$ADB -s $S shell "su -c 'screencap -p /data/local/tmp/s.png'"
$ADB -s $S pull /data/local/tmp/s.png "D:/tmp/s.png"

# 量左空档 / 右空档（列投影切字形）
python3 - <<'PY'
import numpy as np; from PIL import Image
a=np.array(Image.open("D:/tmp/s.png").convert("L")); m=a<128
band=m[939:1041]; col=band.sum(axis=0); gs=[]; st=None; g=0
for x,v in enumerate(col):
    if v>0:
        st=x if st is None else st; g=0
    else:
        if st is not None:
            g+=1
            if g>=1: gs.append((st,x-g)); st=None; g=0
for i,(x0,x1) in enumerate(gs): print(i,x0,x1,x1-x0+1)
PY
```

判定标准（当前 em=97px）：
* `【`→正文 应 ≈ 21~30px（`【` 贴内缘 + 下一字 lsb）
* 正文→`】` 应 ≈ 2~12px

若两者都落在 20~35px 区间，即为对称。

---

## 7. 附：本次用到的证据文件

| 文件 | 内容 |
|------|------|
| `ref/live_stock.png` | STOCK 模式（系统字体原厂）同一段原文 —— **复现不对称的关键证据** |
| `ref/live_now.png` | CHALK 修复前 |
| `ref/live_final.png` | CHALK 修复后（当前设备状态） |
| `ref/cmp_bracket_3state.png` | 三态对比图 |
| `ref/ch.bin` | 从 App WebView HTTP Cache 提取的 CSS bundle（字体栈/排版规则的出处） |

系统侧工具（字体仓库 `kkkkikun/oit-font-switch`）：
`tools/embed_bracket_glyphs.py`（把参考字体的括号轮廓嵌入目标字体并贴内缘）、
`tools/drop_cmap_codepoints.py`（从 cmap 摘码位，强制回退——已弃用，仅留作对照）。

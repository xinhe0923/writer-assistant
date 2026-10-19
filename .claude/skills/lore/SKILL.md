---
description: 查设定。在设定、摘要、正文、大纲、灵感箱里搜索，回答不超过 100 字，每条事实注明 文件:行号。
argument-hint: "<问题>"
model: sonnet
disable-model-invocation: true
allowed-tools: Read Grep Glob
---

# /lore 查设定

只查不改：不修改任何文件，不编造设定。

问题：$ARGUMENTS

1. 在 设定/ 摘要/ 正文/ 大纲.md 灵感箱.md 里搜索（用 Grep 带行号，按需读上下文）。
2. 回答不超过 100 字，每条事实后面都注明 `文件:行号`。
3. 找到互相矛盾的说法：都列出来（各自带 文件:行号），标「设定冲突」。
4. 找不到：说「没查到」，并建议应该记在哪个文件。

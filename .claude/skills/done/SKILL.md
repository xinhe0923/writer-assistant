---
description: 收工。统计字数、更新摘要和设定、重写断点，分两次提交（正文 / 记忆）并 push。
argument-hint: "[下一句开头，可选]"
model: sonnet
disable-model-invocation: true
allowed-tools: Read Grep Glob Edit(设定/**) Edit(摘要/**) Edit(大纲.md) Edit(断点.md) Bash(python3 tools/wordcount.py *) Bash(git status *) Bash(git diff *) Bash(git add *) Bash(git commit *) Bash(git push *) Bash(git remote *)
---

# /done 收工

先遵守 CLAUDE.md 的铁律：不修改 正文/ 下的任何文件，不写正文。

参数（下一句开头）：$ARGUMENTS

1. 运行 `python3 tools/wordcount.py --log`。它会打印本次各文件的新增字数和累计字数，并写入 日志.csv。记下这两个数。
2. 运行 `git diff HEAD -- 正文/` 看这次写了什么；还没提交过的新章节不在 diff 里，用 `git status --short -- 正文/` 找到后直接读。没有任何正文改动就跳过第 3–4 步。
3. 对每个有改动的章节，更新 `摘要/<章>.md`（如 正文/003.md → 摘要/003.md）：第一行是 `# <章> <一个短标题>`，下面不超过 200 字，只写正文里已经发生的事。
4. 只根据正文里的事实更新：
   - 设定/人物.md 中相关人物的「当前状态」和「读者已知」；
   - 有新伏笔或回收时，更新 设定/伏笔账本.md（写明 文件:行）；
   - 大纲.md 节拍表的「状态」列：正文里已经写完的节拍标「已写」，写到一半的标「进行中」。只改状态列。
   拿不准的地方标「待确认」，不要追问我。
5. 下一句开头：有参数就原样使用参数。没有就问我一次；我说「跳过」或不给，就写一句方向，并在前面标「（方向，不是句子）」。
6. 重写 断点.md（按原模板的格式）：位置 = 当前章 + 停在哪一幕；下一句开头 = 第 5 步的结果；下一个小任务 = 大纲.md 里第一个状态不是「已写」的节拍；没解决 = 保留还没解决的条目；今日字数 = 日志.csv 里今天所有 done 行的 delta 之和；更新时间 = 现在。
7. 两次提交：
   - 正文提交：只 `git add 正文/`，信息为「正文：<文件> +<N>字」（多个文件用顿号分开），不加 Co-Authored-By。正文没有改动就跳过。
   - 记忆提交：`git add` 其余改动（摘要/ 设定/ 大纲.md 断点.md 日志.csv 等，不含 正文/），信息为「记忆：<简述>」，结尾加 Co-Authored-By 行。
   - `git remote -v` 有远程就 `git push`；失败就提示一句。
8. 输出不超过 5 行：
```
今天 +N 字（累计 M）
下次从：<文件> ·「<下一句开头>」
下一个小任务：<…>
```

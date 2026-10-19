#!/usr/bin/env python3
"""正文字数统计。只用标准库，支持 Python 3.9+。

口径（见 README「字数口径」）：正文/*.md 里的非空白字符，
去掉 Markdown 标记（标题的 #、强调的 * _、链接语法）、HTML 注释和【待定：…】占位；标点算字。

用法：
    python3 tools/wordcount.py              # 比较工作区和 HEAD，打印各文件新增字数
    python3 tools/wordcount.py --log        # 同上，并把每个有变动的文件写进 日志.csv（event=done）
    python3 tools/wordcount.py --event go --file 正文/001.md
                                            # 向 日志.csv 追加一行 go/stuck 事件（delta=0）
"""

import argparse
import csv
import datetime
import re
import subprocess
import sys
from pathlib import Path

TEXT_DIR = "正文"
LOG_FILE = "日志.csv"
LOG_HEADER = ["date", "time", "event", "file", "delta", "total"]

_COMMENT = re.compile(r"<!--.*?-->", re.S)
_PENDING = re.compile(r"【待定[：:][^】]*】")
_IMAGE_OR_LINK = re.compile(r"!?\[([^\]]*)\]\([^)]*\)")
_WIKI_LINK = re.compile(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]")
_HEADING = re.compile(r"^[ \t]*#{1,6}[ \t]*", re.M)
_EMPHASIS = re.compile(r"[*_]")
_SPACE = re.compile(r"\s")


def count_chars(text):
    """按口径统计一段 Markdown 的字数。"""
    text = _COMMENT.sub("", text)
    text = _PENDING.sub("", text)
    text = _IMAGE_OR_LINK.sub(r"\1", text)
    text = _WIKI_LINK.sub(r"\1", text)
    text = _HEADING.sub("", text)
    text = _EMPHASIS.sub("", text)
    return len(_SPACE.sub("", text))


def _git(root, *args):
    return subprocess.run(
        ["git", "-c", "core.quotepath=false", *args],
        cwd=str(root),
        capture_output=True,
    )


def _has_head(root):
    return _git(root, "rev-parse", "--verify", "--quiet", "HEAD").returncode == 0


def _is_text_file(rel):
    parts = rel.split("/")
    return len(parts) == 2 and parts[0] == TEXT_DIR and parts[1].endswith(".md")


def head_counts(root):
    """HEAD 里 正文/*.md 的字数；没有 HEAD 时为空。"""
    if not _has_head(root):
        return {}
    res = _git(root, "ls-tree", "-z", "--name-only", "HEAD", TEXT_DIR + "/")
    if res.returncode != 0:
        return {}
    counts = {}
    for rel in res.stdout.decode("utf-8").split("\0"):
        if not _is_text_file(rel):
            continue
        show = _git(root, "show", "HEAD:" + rel)
        if show.returncode == 0:
            counts[rel] = count_chars(show.stdout.decode("utf-8", errors="replace"))
    return counts


def work_counts(root):
    """工作区里 正文/*.md 的字数。"""
    counts = {}
    text_dir = Path(root) / TEXT_DIR
    if text_dir.is_dir():
        for path in sorted(text_dir.glob("*.md")):
            if path.is_file():
                rel = TEXT_DIR + "/" + path.name
                counts[rel] = count_chars(path.read_text(encoding="utf-8", errors="replace"))
    return counts


def diff(root):
    """返回 (变动列表 [(文件, 增量)], 改动后 正文/ 总字数)。删除的文件增量为负。"""
    old = head_counts(root)
    new = work_counts(root)
    changes = []
    for rel in sorted(set(old) | set(new)):
        delta = new.get(rel, 0) - old.get(rel, 0)
        if delta != 0 or (rel in old) != (rel in new):
            changes.append((rel, delta))
    return changes, sum(new.values())


def _now():
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d"), now.strftime("%H:%M")


def append_log(root, rows):
    """向 日志.csv 追加行；文件不存在时先写表头。"""
    log_path = Path(root) / LOG_FILE
    need_header = not log_path.exists() or log_path.stat().st_size == 0
    if not need_header:
        with log_path.open("rb") as f:
            f.seek(-1, 2)
            if f.read(1) not in (b"\n", b"\r"):
                with log_path.open("a", encoding="utf-8") as g:
                    g.write("\n")
    with log_path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        if need_header:
            writer.writerow(LOG_HEADER)
        writer.writerows(rows)


def _signed(n):
    return "%+d" % n


def main(argv=None):
    parser = argparse.ArgumentParser(description="正文字数统计")
    parser.add_argument("--log", action="store_true", help="把本次变动写进 日志.csv（event=done）")
    parser.add_argument("--event", help="只追加一行事件（如 go、stuck），delta 为 0")
    parser.add_argument("--file", default="", help="与 --event 一起用：当前章文件")
    parser.add_argument("--root", default=None, help="仓库根目录（默认是本脚本的上一级目录）")
    args = parser.parse_args(argv)

    root = Path(args.root) if args.root else Path(__file__).resolve().parent.parent
    date, time = _now()

    if args.event:
        total = sum(work_counts(root).values())
        append_log(root, [[date, time, args.event, args.file, 0, total]])
        print("已记录 %s（累计 %d 字）" % (args.event, total))
        return 0

    changes, total = diff(root)
    for rel, delta in changes:
        print("%s %s字" % (rel, _signed(delta)))
    net = sum(d for _, d in changes)
    print("本次 %s字，累计 %d字" % (_signed(net), total))
    if args.log and changes:
        append_log(root, [[date, time, "done", rel, delta, total] for rel, delta in changes])
    return 0


if __name__ == "__main__":
    sys.exit(main())

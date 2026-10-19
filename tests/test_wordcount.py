# 测试数据：本文件里的中文字符串只用于测试字数统计，不是小说正文。
"""tools/wordcount.py 的测试。运行：python3 -m unittest"""

import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import wordcount  # noqa: E402


def git(root, *args):
    subprocess.run(
        ["git", "-c", "user.name=test", "-c", "user.email=test@example.com", *args],
        cwd=str(root),
        check=True,
        capture_output=True,
    )


class CountCharsTest(unittest.TestCase):
    def test_plain_text_and_punctuation(self):
        self.assertEqual(wordcount.count_chars("甲乙丙，丁。"), 6)

    def test_whitespace_not_counted(self):
        self.assertEqual(wordcount.count_chars("甲 乙\n\t丙　丁"), 4)

    def test_markdown_marks_not_counted(self):
        text = "# 标题\n\n**甲乙** _丙_ *丁*\n[戊己](https://example.com/x)\n![庚](a.png)\n[[辛|壬]]"
        # 标题 甲乙 丙 丁 戊己 庚 壬
        self.assertEqual(wordcount.count_chars(text), 10)

    def test_html_comment_not_counted(self):
        self.assertEqual(wordcount.count_chars("甲<!-- 注释\n多行 -->乙"), 2)

    def test_pending_placeholder_not_counted(self):
        self.assertEqual(wordcount.count_chars("甲【待定：这里以后补】乙【待定:半角】丙"), 3)


class DiffTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        git(self.root, "init", "-q")
        (self.root / "正文").mkdir()

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, name, text):
        (self.root / "正文" / name).write_text(text, encoding="utf-8")

    def commit(self):
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "测试提交")

    def test_no_head_counts_everything(self):
        self.write("001.md", "甲乙丙")
        changes, total = wordcount.diff(self.root)
        self.assertEqual(changes, [("正文/001.md", 3)])
        self.assertEqual(total, 3)

    def test_new_file(self):
        self.write("001.md", "甲乙丙")
        self.commit()
        self.write("002.md", "丁戊")
        changes, total = wordcount.diff(self.root)
        self.assertEqual(changes, [("正文/002.md", 2)])
        self.assertEqual(total, 5)

    def test_modified_file(self):
        self.write("001.md", "甲乙丙")
        self.commit()
        self.write("001.md", "甲乙丙丁戊")
        changes, total = wordcount.diff(self.root)
        self.assertEqual(changes, [("正文/001.md", 2)])
        self.assertEqual(total, 5)

    def test_deleted_file_is_negative(self):
        self.write("001.md", "甲乙丙")
        self.write("002.md", "丁戊")
        self.commit()
        (self.root / "正文" / "002.md").unlink()
        changes, total = wordcount.diff(self.root)
        self.assertEqual(changes, [("正文/002.md", -2)])
        self.assertEqual(total, 3)

    def test_unchanged_reports_nothing(self):
        self.write("001.md", "甲乙丙")
        self.commit()
        changes, total = wordcount.diff(self.root)
        self.assertEqual(changes, [])
        self.assertEqual(total, 3)

    def test_chinese_filename(self):
        self.write("第一章.md", "甲乙")
        self.commit()
        self.write("第一章.md", "甲乙丙")
        changes, _ = wordcount.diff(self.root)
        self.assertEqual(changes, [("正文/第一章.md", 1)])

    def test_only_md_directly_under_text_dir(self):
        self.write("note.txt", "甲乙丙")
        (self.root / "正文" / "子目录").mkdir()
        (self.root / "正文" / "子目录" / "x.md").write_text("丁", encoding="utf-8")
        self.write(".gitkeep", "")
        changes, total = wordcount.diff(self.root)
        self.assertEqual(changes, [])
        self.assertEqual(total, 0)

    def read_log(self):
        with (self.root / "日志.csv").open(encoding="utf-8") as f:
            return list(csv.reader(f))

    def test_log_appends_done_rows(self):
        (self.root / "日志.csv").write_text("date,time,event,file,delta,total\n", encoding="utf-8")
        self.write("001.md", "甲乙丙")
        self.commit()
        self.write("001.md", "甲乙丙丁")
        self.write("002.md", "戊己")
        wordcount.main(["--log", "--root", str(self.root)])
        rows = self.read_log()
        self.assertEqual(rows[0], wordcount.LOG_HEADER)
        self.assertEqual([r[2:] for r in rows[1:]], [
            ["done", "正文/001.md", "1", "6"],
            ["done", "正文/002.md", "2", "6"],
        ])

    def test_log_creates_header_when_missing(self):
        self.write("001.md", "甲")
        wordcount.main(["--log", "--root", str(self.root)])
        rows = self.read_log()
        self.assertEqual(rows[0], wordcount.LOG_HEADER)
        self.assertEqual(rows[1][2:], ["done", "正文/001.md", "1", "1"])

    def test_event_row(self):
        (self.root / "日志.csv").write_text("date,time,event,file,delta,total", encoding="utf-8")
        self.write("001.md", "甲乙")
        wordcount.main(["--event", "go", "--file", "正文/001.md", "--root", str(self.root)])
        rows = self.read_log()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1][2:], ["go", "正文/001.md", "0", "2"])


if __name__ == "__main__":
    unittest.main()

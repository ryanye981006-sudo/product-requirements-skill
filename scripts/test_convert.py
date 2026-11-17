"""Stdlib regression tests; no customer documents or network access needed."""

from html.parser import HTMLParser
from pathlib import Path
import tempfile
import unittest
import subprocess
import sys

from convert import ConversionError, convert, render_markdown


class Tables(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables, self.current, self.row, self.cell = [], None, None, None

    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            self.current = []
            self.tables.append(self.current)
        elif tag == 'tr':
            self.row = []
            self.current.append(self.row)
        elif tag in ('td', 'th'):
            self.cell = []
            self.row.append(self.cell)

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag in ('td', 'th'):
            self.cell = None


class ConversionTests(unittest.TestCase):
    def test_example_content_and_columns(self):
        example = Path(__file__).resolve().parent.parent / 'assets' / 'example.md'
        html, stats = convert(example.read_text(encoding='utf-8'), '示例')
        self.assertEqual(stats, {'tables': 2, 'rows': 4})
        parser = Tables()
        parser.feed(html)
        cells = [[[''.join(c) for c in row] for row in table] for table in parser.tables]
        self.assertEqual(cells[0][1], ['查询', '输入关键字，点击【查询】。展示匹配结果，保留原有顺序。无匹配项时显示空提示。', '', '复制本行'])
        self.assertEqual(cells[1][1], ['名称', '保留原文，不增加字段。', '复制本行'])
        self.assertIn('A|B', cells[0][3][1])
        self.assertIn('<li>输入<strong>关键字</strong>', html)

    def test_untrusted_markup_is_text(self):
        html, _ = convert('| 名称 | 描述 |\n| --- | --- |\n| <script>x</script> | <img src=x onerror=alert(1)> |', '</title><script>bad()</script>')
        self.assertNotIn('<script>bad()', html)
        self.assertNotIn('<img src=x', html)
        self.assertIn('&lt;script&gt;x&lt;/script&gt;', html)

    def test_malformed_table_fails_before_output(self):
        with self.assertRaises(ConversionError):
            render_markdown('| A | B |\n| --- | --- |\n| one |')
        with self.assertRaises(ConversionError):
            render_markdown('| A | B |\n| wrong | wrong |\n| one | two |')

    def test_unsupported_code_and_numbered_start(self):
        with self.assertRaises(ConversionError):
            render_markdown('```html\n<table>\n```')
        with self.assertRaises(ConversionError):
            render_markdown('| A |\n| --- |\n| 3. step |')

    def test_cli_preserves_source_and_existing_output(self):
        with tempfile.TemporaryDirectory() as folder:
            source, output = Path(folder) / '输入.md', Path(folder) / '结果.html'
            original = '| 功能项 | 描述 | 图例 |\n| --- | --- | --- |\n| 项目 | 1. **第一步**<br>2. 第二步 | |'
            source.write_text(original, encoding='utf-8')
            command = [sys.executable, str(Path(__file__).with_name('convert.py')), str(source), '-o', str(output)]
            first = subprocess.run(command, capture_output=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(source.read_text(encoding='utf-8'), original)
            previous = output.read_bytes()
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 2)
            self.assertEqual(output.read_bytes(), previous)


if __name__ == '__main__':
    unittest.main()

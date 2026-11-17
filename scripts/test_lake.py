import unittest
from validate_lake import validate


HEADER = ('<!doctype lake><title>示例需求</title>'
          '<meta name="doc-version" content="1" />'
          '<meta name="viewport" content="adapt" />'
          '<meta name="typography" content="classic" />'
          '<meta name="paragraphSpacing" content="relax" />')
TABLE = ('<table id="table01" data-lake-id="table01"><colgroup>'
         '<col width="200"><col width="640"></colgroup><tbody><tr>'
         '<td><p><span>功能项</span></p></td><td><ol list="L01">'
         '<li><span>第一条</span></li></ol><ol list="L01" data-lake-indent="1">'
         '<li><span>子项</span></li></ol><ol list="L01" start="2">'
         '<li><span>第二条</span></li></ol></td></tr></tbody></table>')


class LakeTests(unittest.TestCase):
    def test_valid_nested_numbering_and_variable_columns(self):
        self.assertEqual(validate(HEADER + TABLE), [])

    def test_metadata_and_title(self):
        self.assertTrue(validate(HEADER.replace('paragraphSpacing', 'missing') + TABLE))
        self.assertTrue(validate(HEADER.replace('示例需求', '') + TABLE))

    def test_ids_and_table_columns(self):
        self.assertTrue(validate(HEADER + TABLE + TABLE))
        self.assertTrue(validate(HEADER + TABLE.replace('<col width="200">', '')))

    def test_closing_tags_and_copy_controls(self):
        self.assertTrue(validate(HEADER + TABLE.replace('</td>', '', 1)))
        self.assertTrue(validate(HEADER + TABLE + '<button>复制</button>'))

    def test_list_attributes_and_spacing(self):
        self.assertTrue(validate(HEADER + TABLE.replace('start="2"', 'start="0"')))
        self.assertTrue(validate(HEADER + TABLE.replace('</ol><ol', '</ol>\n<ol')))
        self.assertTrue(validate(HEADER + TABLE.replace('list="L01"', '')))

    def test_invalid_numeric_attributes_report_errors(self):
        for attribute in ['start="²"', 'start', 'data-lake-indent="²"']:
            with self.subTest(attribute=attribute):
                self.assertTrue(validate(HEADER + TABLE.replace('start="2"', attribute)))


if __name__ == '__main__':
    unittest.main()

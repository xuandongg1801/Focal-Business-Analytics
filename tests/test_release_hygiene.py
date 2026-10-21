"""Release gates tested with positive and adversarial temporary trees."""
from pathlib import Path
import sys
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from release_checks import check_text, check_source, check_clean_tree, release_files


class HygieneTests(unittest.TestCase):
    def test_personal_paths_in_all_text_types(self):
        paths = [chr(67)+':/'+'Users/Someone/model', '/'+'home/person/project', '/'+'Users/person/project', 'One'+'Drive/file']
        for extension in ['.py','.md','.json','.yaml','.yml','.toml','.txt','.log']:
            for path in paths:
                with self.subTest(extension=extension,path=path):
                    with self.assertRaisesRegex(AssertionError,'absolute path'):
                        check_text('test'+extension,path)

    def test_scientific_time_language_is_allowed(self):
        check_text('method.md','previous month; previous observation; holdout_has_prior_analyst_exposure')
        check_text('test.py','from streamlit.testing.'+'v'+'1 import AppTest')

    def test_project_narrative_is_rejected(self):
        for text in ['previous '+'project','prior_'+'experiments','old '+'version','phiên bản '+'cũ']:
            with self.assertRaisesRegex(AssertionError,'narrative'):
                check_text('method.md',text)

    def test_removed_integration_is_rejected(self):
        with self.assertRaisesRegex(AssertionError,'integration'):
            check_text('file.md','Power'+' BI')

    def test_cache_and_logs_cannot_enter_release(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'.cache').mkdir();(root/'kept.py').write_text('x=1')
            (root/'.cache/a.py').write_text('x=2');(root/'runtime.log').write_text('diagnostic')
            self.assertEqual([p.name for p in release_files(root)],['kept.py'])
            with self.assertRaisesRegex(AssertionError,'junk'):
                check_clean_tree(root)

    def test_broken_doc_links_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'README.md').write_text('[file](absent.csv)')
            with self.assertRaisesRegex(AssertionError,'Broken document link'):
                check_source(root)

    def test_syntax_errors_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'bad.py').write_text('def :')
            with self.assertRaises(SyntaxError):
                check_source(root)

    def test_retired_target_semantics_and_deleted_feature_are_rejected(self):
        for text in ['pro'+'xy', 'approval '+'probability', 'nhãn đại'+' diện']:
            with self.assertRaisesRegex(AssertionError, 'Retired target semantic'):
                check_text('method.md', text)
        for text in ['re'+'port/file.md', 'RE'+'PORT_DIR', 're'+'port_path']:
            with self.assertRaisesRegex(AssertionError, 'Removed feature reference'):
                check_text('method.md', text)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/('re'+'port')).mkdir()
            with self.assertRaisesRegex(AssertionError, 'Removed feature directory'):
                check_source(root)

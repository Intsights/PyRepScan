import unittest
import tempfile
import git

import pyrepscan


class RulesManagerTestCase(
    unittest.TestCase,
):
    def test_should_scan_file_ignored_extensions(
        self,
    ):
        rules_manager = pyrepscan.RulesManager()

        should_scan = rules_manager.should_scan_file_path('file.txt')
        self.assertTrue(
            expr=should_scan,
        )
        rules_manager.add_ignored_file_extension('txt')
        should_scan = rules_manager.should_scan_file_path('file.txt')
        self.assertFalse(
            expr=should_scan,
        )

        rules_manager.add_ignored_file_extension('pdf')
        should_scan = rules_manager.should_scan_file_path('file.txt')
        self.assertFalse(
            expr=should_scan,
        )
        should_scan = rules_manager.should_scan_file_path('file.pdf')
        self.assertFalse(
            expr=should_scan,
        )
        should_scan = rules_manager.should_scan_file_path('file.doc')
        self.assertTrue(
            expr=should_scan,
        )

    def test_should_scan_file_ignored_file_paths(
        self,
    ):
        rules_manager = pyrepscan.RulesManager()

        should_scan = rules_manager.should_scan_file_path('/site-packages/file.txt')
        self.assertTrue(
            expr=should_scan,
        )
        rules_manager.add_ignored_file_path('site-packages')
        should_scan = rules_manager.should_scan_file_path('/site-packages/file.txt')
        self.assertFalse(
            expr=should_scan,
        )
        should_scan = rules_manager.should_scan_file_path('/folder_one/subfolder/file.txt')
        self.assertTrue(
            expr=should_scan,
        )

        rules_manager.add_ignored_file_path('folder_one/subfolder')
        should_scan = rules_manager.should_scan_file_path('/folder_one/subfolder/file.txt')
        self.assertFalse(
            expr=should_scan,
        )
        should_scan = rules_manager.should_scan_file_path('/folder_one/sub/file.txt')
        self.assertTrue(
            expr=should_scan,
        )

    def test_add_rule_one(
        self,
    ):
        rules_manager = pyrepscan.RulesManager()

        rules_manager.add_rule(
            name='rule_one',
            regex_pattern=r'([a-z]+)',
            regex_blacklist_patterns=[],
        )
        rules_manager.compile_rules()

        matches = rules_manager.scan_content(
            content='first line\nsecond line\nthird line',
        )
        self.assertEqual(
            first=matches,
            second=[
                {
                    'match': 'first',
                    'rule_name': 'rule_one',
                },
                {
                    'match': 'line',
                    'rule_name': 'rule_one',
                },
                {
                    'match': 'second',
                    'rule_name': 'rule_one',
                },
                {
                    'match': 'line',
                    'rule_name': 'rule_one',
                },
                {
                    'match': 'third',
                    'rule_name': 'rule_one',
                },
                {
                    'match': 'line',
                    'rule_name': 'rule_one',
                },
            ],
        )

    def test_add_rule_two(
        self,
    ):
        rules_manager = pyrepscan.RulesManager()

        rules_manager.add_rule(
            name='rule_one',
            regex_pattern=r'([a-z]+)',
            regex_blacklist_patterns=[
                r'line',
            ],
        )
        rules_manager.compile_rules()

        matches = rules_manager.scan_content(
            content='first line\nsecond line\nthird line',
        )
        self.assertEqual(
            first=matches,
            second=[
                {
                    'match': 'first',
                    'rule_name': 'rule_one',
                },
                {
                    'match': 'second',
                    'rule_name': 'rule_one',
                },
                {
                    'match': 'third',
                    'rule_name': 'rule_one',
                },
            ],
        )

    def test_add_rule_three(
        self,
    ):
        rules_manager = pyrepscan.RulesManager()

        with self.assertRaises(
            expected_exception=RuntimeError,
        ) as context:
            rules_manager.add_rule(
                name='rule_one',
                regex_pattern=r'(',
                regex_blacklist_patterns=[],
            )

        self.assertEqual(
            first='Invalid matching regex pattern: "("',
            second=str(context.exception),
        )

        with self.assertRaises(
            expected_exception=RuntimeError,
        ) as context:
            rules_manager.add_rule(
                name='rule_one',
                regex_pattern=r'regex_pattern_without_capturing_group',
                regex_blacklist_patterns=[],
            )

        self.assertEqual(
            first='Matching regex pattern must have exactly one capturing group: "regex_pattern_without_capturing_group"',
            second=str(context.exception),
        )

        with self.assertRaises(
            expected_exception=RuntimeError,
        ) as context:
            rules_manager.add_rule(
                name='rule_two',
                regex_pattern=r'(content)',
                regex_blacklist_patterns=[
                    '(',
                ],
            )

        self.assertEqual(
            first='Invalid blacklist regex pattern: "("',
            second=str(context.exception),
        )

        with self.assertRaises(
            expected_exception=RuntimeError,
        ) as context:
            rules_manager.add_rule(
                name='rule_two',
                regex_pattern=r'(content)',
                regex_blacklist_patterns=[
                    '(blacklist_regex_with_capturing_group)',
                ],
            )

        self.assertEqual(
            first='Blacklist regex pattern must not have a capturing group: "(blacklist_regex_with_capturing_group)"',
            second=str(context.exception),
        )


class GitRepositoryScannerTestCase(
    unittest.TestCase,
):
    def test_scan(
        self,
    ):
        grs = pyrepscan.GitRepositoryScanner()
        grs.add_rule(
            name='First Rule',
            regex_pattern=r'''(content)''',
            regex_blacklist_patterns=[],
        )
        grs.compile_rules()

        grs.add_ignored_file_extension('py')
        grs.add_ignored_file_path('test_')

        with tempfile.TemporaryDirectory() as tmpdir:
            bare_repo = git.Repo.init(
                path=tmpdir,
            )
            test_author = git.Actor(
                name='Author Name',
                email='test@author.email',
            )

            with open(f'{tmpdir}/file.txt', 'w') as tmpfile:
                tmpfile.write('content')
            with open(f'{tmpdir}/file.py', 'w') as tmpfile:
                tmpfile.write('content')
            with open(f'{tmpdir}/file.other', 'w') as tmpfile:
                tmpfile.write('nothing special')
            with open(f'{tmpdir}/test_file.cpp', 'w') as tmpfile:
                tmpfile.write('content')
            bare_repo.index.add(
                items=[
                    f'{tmpdir}/file.txt',
                    f'{tmpdir}/file.py',
                    f'{tmpdir}/file.other',
                    f'{tmpdir}/test_file.cpp',
                ],
            )
            bare_repo.index.commit(
                message='initial commit',
                author=test_author,
            )

            with open(f'{tmpdir}/file.txt', 'w') as tmpfile:
                tmpfile.write('new content')
            bare_repo.index.add(
                items=[
                    f'{tmpdir}/file.txt',
                ],
            )
            bare_repo.index.commit(
                message='edited file',
                author=test_author,
            )

            new_branch = bare_repo.create_head('new_branch')
            with open(f'{tmpdir}/file.txt', 'w') as tmpfile:
                tmpfile.write('new content from new branch')
            bare_repo.index.add(
                items=[
                    f'{tmpdir}/file.txt',
                ],
            )
            bare_repo.index.commit(
                message='edited file in new branch',
                author=test_author,
            )
            bare_repo.head.reference = bare_repo.heads.master
            bare_repo.head.reset(
                index=True,
                working_tree=True,
            )

            merge_base = bare_repo.merge_base(
                new_branch,
                bare_repo.heads.master,
            )
            bare_repo.index.merge_tree(
                rhs=bare_repo.heads.master,
                base=merge_base,
            )
            bare_repo.index.commit(
                message='merge from new branch',
                author=test_author,
                parent_commits=(
                    new_branch.commit,
                    bare_repo.heads.master.commit,
                ),
            )

            results = grs.scan(
                repository_path=tmpdir,
            )
            for result in results:
                result.pop('commit_id')

            self.assertCountEqual(
                first=results,
                second=[
                    {
                        'author_email': 'test@author.email',
                        'author_name': 'Author Name',
                        'commit_message': 'edited file in new branch',
                        'content': 'new content from new branch',
                        'file_path': 'file.txt',
                        'match': 'content',
                        'rule_name': 'First Rule'
                    },
                    {
                        'author_email': 'test@author.email',
                        'author_name': 'Author Name',
                        'commit_message': 'edited file',
                        'content': 'new content',
                        'file_path': 'file.txt',
                        'match': 'content',
                        'rule_name': 'First Rule'
                    },
                    {
                        'author_email': 'test@author.email',
                        'author_name': 'Author Name',
                        'commit_message': 'initial commit',
                        'content': 'content',
                        'file_path': 'file.txt',
                        'match': 'content',
                        'rule_name': 'First Rule'
                    },
                ],
            )

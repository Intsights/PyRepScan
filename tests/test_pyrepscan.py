import unittest
import tempfile
import git
import datetime

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

    def test_add_content_rule_one(
        self,
    ):
        rules_manager = pyrepscan.RulesManager()

        rules_manager.add_content_rule(
            rule=pyrepscan.ContentRule(
                name='rule_one',
                regex_pattern=r'([a-z]+)',
                whitelist_regex_patterns=[],
                blacklist_regex_patterns=[],
            ),
        )

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

    def test_add_content_rule_two(
        self,
    ):
        rules_manager = pyrepscan.RulesManager()

        rules_manager.add_content_rule(
            rule=pyrepscan.ContentRule(
                name='rule_one',
                regex_pattern=r'([a-z]+)',
                whitelist_regex_patterns=[],
                blacklist_regex_patterns=[
                    r'line',
                ],
            ),
        )

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

    def test_add_content_rule_three(
        self,
    ):
        rules_manager = pyrepscan.RulesManager()

        rules_manager.add_content_rule(
            rule=pyrepscan.ContentRule(
                name='rule_one',
                regex_pattern=r'([a-z]+)',
                whitelist_regex_patterns=[
                    'second',
                    'third',
                ],
                blacklist_regex_patterns=[
                    r'line',
                ],
            ),
        )

        matches = rules_manager.scan_content(
            content='first line\nsecond line\nthird line',
        )
        self.assertEqual(
            first=matches,
            second=[
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

    def test_add_content_rule_four(
        self,
    ):
        rules_manager = pyrepscan.RulesManager()

        with self.assertRaises(
            expected_exception=RuntimeError,
        ) as context:
            rules_manager.add_content_rule(
                rule=pyrepscan.ContentRule(
                    name='rule_one',
                    regex_pattern=r'(',
                    whitelist_regex_patterns=[],
                    blacklist_regex_patterns=[],
                ),
            )

        self.assertEqual(
            first='Invalid regex pattern: (\nError: missing ): (',
            second=str(context.exception),
        )

        with self.assertRaises(
            expected_exception=RuntimeError,
        ) as context:
            rules_manager.add_content_rule(
                rule=pyrepscan.ContentRule(
                    name='rule_one',
                    regex_pattern=r'regex_pattern_without_capturing_group',
                    whitelist_regex_patterns=[],
                    blacklist_regex_patterns=[],
                ),
            )

        self.assertEqual(
            first='Matching regex pattern must have exactly one capturing group: regex_pattern_without_capturing_group',
            second=str(context.exception),
        )

        with self.assertRaises(
            expected_exception=RuntimeError,
        ) as context:
            rules_manager.add_content_rule(
                rule=pyrepscan.ContentRule(
                    name='rule_two',
                    regex_pattern=r'(content)',
                    whitelist_regex_patterns=[],
                    blacklist_regex_patterns=[
                        '(',
                    ],
                ),
            )

        self.assertEqual(
            first='Invalid blacklist regex pattern: (\nError: missing ): (',
            second=str(context.exception),
        )

        with self.assertRaises(
            expected_exception=RuntimeError,
        ) as context:
            rules_manager.add_content_rule(
                rule=pyrepscan.ContentRule(
                    name='rule_two',
                    regex_pattern=r'(content)',
                    whitelist_regex_patterns=[],
                    blacklist_regex_patterns=[
                        '(blacklist_regex_with_capturing_group)',
                    ],
                ),
            )

        self.assertEqual(
            first='Blacklist regex pattern must not have a capturing group: (blacklist_regex_with_capturing_group)',
            second=str(context.exception),
        )

        with self.assertRaises(
            expected_exception=RuntimeError,
        ) as context:
            rules_manager.add_content_rule(
                rule=pyrepscan.ContentRule(
                    name='rule_two',
                    regex_pattern=r'(content)',
                    whitelist_regex_patterns=[
                        '(',
                    ],
                    blacklist_regex_patterns=[
                        'blacklist_regex_with_capturing_group',
                    ],
                ),
            )

        self.assertEqual(
            first='Invalid whitelist regex pattern: (\nError: missing ): (',
            second=str(context.exception),
        )

        with self.assertRaises(
            expected_exception=RuntimeError,
        ) as context:
            rules_manager.add_content_rule(
                rule=pyrepscan.ContentRule(
                    name='rule_two',
                    regex_pattern=r'(content)',
                    whitelist_regex_patterns=[
                        '(sub)',
                    ],
                    blacklist_regex_patterns=[
                        'blacklist_regex_with_capturing_group',
                    ],
                ),
            )

        self.assertEqual(
            first='Whitelist regex pattern must not have a capturing group: (sub)',
            second=str(context.exception),
        )

    def test_add_file_name_rule_one(
        self,
    ):
        rules_manager = pyrepscan.RulesManager()

        rules_manager.add_file_name_rule(
            rule=pyrepscan.FileNameRule(
                name='rule_one',
                regex_pattern=r'(prod|dev|stage).+key',
            ),
        )

        self.assertIsNone(
            obj=rules_manager.scan_file_name(
                file_name='workdir/prod/some_file',
            ),
        )

        self.assertEqual(
            first=rules_manager.scan_file_name(
                file_name='workdir/prod/some_file.key',
            ),
            second=[
                {
                    'match': 'workdir/prod/some_file.key',
                    'rule_name': 'rule_one',
                },
            ],
        )

    def test_check_pattern(
        self,
    ):
        rules_manager = pyrepscan.RulesManager()

        with self.assertRaises(
            expected_exception=RuntimeError,
        ) as context:
            rules_manager.check_pattern(
                content='some content to check',
                pattern=r'content',
            )

        self.assertEqual(
            first='Matching regex pattern must have exactly one capturing group: content',
            second=str(context.exception),
        )

        with self.assertRaises(
            expected_exception=RuntimeError,
        ) as context:
            rules_manager.check_pattern(
                content='some content to check',
                pattern=r'(content',
            )

        self.assertEqual(
            first='Invalid regex pattern: (content\nError: missing ): (content',
            second=str(context.exception),
        )

        self.assertEqual(
            first=rules_manager.check_pattern(
                content='some content to check, another content in the same line\nanother content in another line\n',
                pattern=r'(content)',
            ),
            second=[
                'content',
                'content',
                'content',
            ],
        )

        self.assertEqual(
            first=rules_manager.check_pattern(
                content='some content1 to check, another content2 in the same line\nanother content3 in another line\n',
                pattern=r'(content\d)',
            ),
            second=[
                'content1',
                'content2',
                'content3',
            ],
        )


class GitRepositoryScannerTestCase(
    unittest.TestCase,
):
    def setUp(
        self,
    ):
        self.tmpdir = tempfile.TemporaryDirectory()
        bare_repo = git.Repo.init(
            path=self.tmpdir.name,
        )
        test_author = git.Actor(
            name='Author Name',
            email='test@author.email',
        )

        with open(f'{self.tmpdir.name}/file.txt', 'w') as tmpfile:
            tmpfile.write('content')
        with open(f'{self.tmpdir.name}/file.py', 'w') as tmpfile:
            tmpfile.write('content')
        with open(f'{self.tmpdir.name}/prod_env.key', 'w') as tmpfile:
            tmpfile.write('')
        with open(f'{self.tmpdir.name}/file.other', 'w') as tmpfile:
            tmpfile.write('nothing special')
        with open(f'{self.tmpdir.name}/test_file.cpp', 'w') as tmpfile:
            tmpfile.write('content')
        bare_repo.index.add(
            items=[
                f'{self.tmpdir.name}/file.txt',
                f'{self.tmpdir.name}/file.py',
                f'{self.tmpdir.name}/prod_env.key',
                f'{self.tmpdir.name}/file.other',
                f'{self.tmpdir.name}/test_file.cpp',
            ],
        )

        bare_repo.index.commit(
            message='initial commit',
            author=test_author,
            commit_date='2000-01-01T00:00:00',
            author_date='2000-01-01T00:00:00',
        )

        with open(f'{self.tmpdir.name}/file.txt', 'w') as tmpfile:
            tmpfile.write('new content')
        bare_repo.index.add(
            items=[
                f'{self.tmpdir.name}/file.txt',
            ],
        )
        bare_repo.index.commit(
            message='edited file',
            author=test_author,
            commit_date='2001-01-01T00:00:00',
            author_date='2001-01-01T00:00:00',
        )

        new_branch = bare_repo.create_head('new_branch')
        bare_repo.head.reference = bare_repo.heads[1]
        with open(f'{self.tmpdir.name}/file.txt', 'w') as tmpfile:
            tmpfile.write('new content from new branch')
        bare_repo.index.add(
            items=[
                f'{self.tmpdir.name}/file.txt',
            ],
        )
        bare_repo.index.commit(
            message='edited file in new branch',
            author=test_author,
            commit_date='2002-01-01T00:00:00',
            author_date='2002-01-01T00:00:00',
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
            commit_date='2003-01-01T00:00:00',
            author_date='2003-01-01T00:00:00',
            parent_commits=(
                new_branch.commit,
                bare_repo.heads.master.commit,
            ),
        )

        new_branch = bare_repo.create_head('non_merged_branch')
        bare_repo.head.reference = bare_repo.heads[2]
        with open(f'{self.tmpdir.name}/file.txt', 'w') as tmpfile:
            tmpfile.write('new content from non_merged_branch')
        bare_repo.index.add(
            items=[
                f'{self.tmpdir.name}/file.txt',
            ],
        )
        bare_repo.index.commit(
            message='edited file in non_merged_branch',
            author=test_author,
            commit_date='2004-01-01T00:00:00',
            author_date='2004-01-01T00:00:00',
        )

        bare_repo.head.reference = bare_repo.heads.master

    def tearDown(
        self,
    ):
        self.tmpdir.cleanup()

    def test_scan_regular(
        self,
    ):
        grs = pyrepscan.GitRepositoryScanner()
        grs.add_content_rule(
            name='First Rule',
            regex_pattern=r'''(content)''',
            whitelist_regex_patterns=[],
            blacklist_regex_patterns=[],
        )

        grs.add_ignored_file_extension('py')
        grs.add_ignored_file_path('test_')

        results = grs.scan(
            repository_path=self.tmpdir.name,
            branch_glob_pattern='*master',
            from_timestamp=0,
        )
        for result in results:
            result.pop('commit_id')
        self.assertCountEqual(
            first=results,
            second=[
                {
                    'author_email': 'test@author.email',
                    'author_name': 'Author Name',
                    'commit_message': 'edited file',
                    'commit_time': '2001-01-01T00:00:00',
                    'file_oid': '47d2739ba2c34690248c8f91b84bb54e8936899a',
                    'file_path': 'file.txt',
                    'match': 'content',
                    'rule_name': 'First Rule'
                },
                {
                    'author_email': 'test@author.email',
                    'author_name': 'Author Name',
                    'commit_message': 'edited file in new branch',
                    'commit_time': '2002-01-01T00:00:00',
                    'file_oid': '0407a18f7c6802c7e7ddc5c9e8af4a34584383ff',
                    'file_path': 'file.txt',
                    'match': 'content',
                    'rule_name': 'First Rule'
                },
                {
                    'author_email': 'test@author.email',
                    'author_name': 'Author Name',
                    'commit_message': 'initial commit',
                    'commit_time': '2000-01-01T00:00:00',
                    'file_oid': '6b584e8ece562ebffc15d38808cd6b98fc3d97ea',
                    'file_path': 'file.txt',
                    'match': 'content',
                    'rule_name': 'First Rule'
                },
            ],
        )

        results = grs.scan(
            repository_path=self.tmpdir.name,
            branch_glob_pattern='*',
            from_timestamp=0,
        )
        for result in results:
            result.pop('commit_id')
        self.assertCountEqual(
            first=results,
            second=[
                {
                    'author_email': 'test@author.email',
                    'author_name': 'Author Name',
                    'commit_message': 'edited file',
                    'commit_time': '2001-01-01T00:00:00',
                    'file_oid': '47d2739ba2c34690248c8f91b84bb54e8936899a',
                    'file_path': 'file.txt',
                    'match': 'content',
                    'rule_name': 'First Rule'
                },
                {
                    'author_email': 'test@author.email',
                    'author_name': 'Author Name',
                    'commit_message': 'edited file in new branch',
                    'commit_time': '2002-01-01T00:00:00',
                    'file_oid': '0407a18f7c6802c7e7ddc5c9e8af4a34584383ff',
                    'file_path': 'file.txt',
                    'match': 'content',
                    'rule_name': 'First Rule'
                },
                {
                    'author_email': 'test@author.email',
                    'author_name': 'Author Name',
                    'commit_message': 'initial commit',
                    'commit_time': '2000-01-01T00:00:00',
                    'file_oid': '6b584e8ece562ebffc15d38808cd6b98fc3d97ea',
                    'file_path': 'file.txt',
                    'match': 'content',
                    'rule_name': 'First Rule'
                },
                {
                    'author_email': 'test@author.email',
                    'author_name': 'Author Name',
                    'commit_message': 'edited file in non_merged_branch',
                    'commit_time': '2004-01-01T00:00:00',
                    'file_oid': '057032a2108721ad1de6a9240fd1a8f45bc3f2ef',
                    'file_path': 'file.txt',
                    'match': 'content',
                    'rule_name': 'First Rule'
                },
            ],
        )

        self.assertEqual(
            first=b'new content',
            second=grs.get_file_content(
                repository_path=self.tmpdir.name,
                file_oid='47d2739ba2c34690248c8f91b84bb54e8936899a',
            ),
        )
        self.assertEqual(
            first=b'new content from new branch',
            second=grs.get_file_content(
                repository_path=self.tmpdir.name,
                file_oid='0407a18f7c6802c7e7ddc5c9e8af4a34584383ff',
            ),
        )
        self.assertEqual(
            first=b'content',
            second=grs.get_file_content(
                repository_path=self.tmpdir.name,
                file_oid='6b584e8ece562ebffc15d38808cd6b98fc3d97ea',
            ),
        )

    def test_scan_from_timestamp(
        self,
    ):
        grs = pyrepscan.GitRepositoryScanner()
        grs.add_content_rule(
            name='First Rule',
            regex_pattern=r'''(content)''',
            whitelist_regex_patterns=[],
            blacklist_regex_patterns=[],
        )

        grs.add_ignored_file_extension('py')
        grs.add_ignored_file_path('test_')

        results = grs.scan(
            repository_path=self.tmpdir.name,
            branch_glob_pattern='*',
            from_timestamp=int(
                datetime.datetime(
                    year=2004,
                    month=1,
                    day=1,
                    hour=0,
                    minute=0,
                    second=0,
                    tzinfo=datetime.timezone.utc,
                ).timestamp()
            ),
        )
        for result in results:
            result.pop('commit_id')
        self.assertCountEqual(
            first=results,
            second=[
                {
                    'author_email': 'test@author.email',
                    'author_name': 'Author Name',
                    'commit_message': 'edited file in non_merged_branch',
                    'commit_time': '2004-01-01T00:00:00',
                    'file_oid': '057032a2108721ad1de6a9240fd1a8f45bc3f2ef',
                    'file_path': 'file.txt',
                    'match': 'content',
                    'rule_name': 'First Rule'
                },
            ],
        )

        results = grs.scan(
            repository_path=self.tmpdir.name,
            branch_glob_pattern='*',
            from_timestamp=int(
                datetime.datetime(
                    year=2004,
                    month=1,
                    day=1,
                    hour=0,
                    minute=0,
                    second=1,
                    tzinfo=datetime.timezone.utc,
                ).timestamp()
            ),
        )
        for result in results:
            result.pop('commit_id')
        self.assertListEqual(
            list1=results,
            list2=[],
        )

    def test_scan_file_name(
        self,
    ):
        grs = pyrepscan.GitRepositoryScanner()
        grs.add_file_name_rule(
            name='First Rule',
            regex_pattern=r'(prod|dev|stage).+key',
        )

        results = grs.scan(
            repository_path=self.tmpdir.name,
            branch_glob_pattern='*',
        )
        for result in results:
            result.pop('commit_id')
        self.assertCountEqual(
            first=results,
            second=[
                {
                    'author_email': 'test@author.email',
                    'author_name': 'Author Name',
                    'commit_message': 'initial commit',
                    'commit_time': '2000-01-01T00:00:00',
                    'file_oid': 'e69de29bb2d1d6434b8b29ae775ad8c2e48c5391',
                    'file_path': 'prod_env.key',
                    'match': 'prod_env.key',
                    'rule_name': 'First Rule'
                },
            ],
        )

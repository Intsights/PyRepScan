import unittest

import pyrepscan


class RulesManagerTestCase(
    unittest.TestCase,
):
    def test_should_scan_file_ignored_extensions(
        self,
    ):
        rules_manager = pyrepscan.RulesManager()

        self.assertTrue(
            expr=rules_manager.should_scan_file_path('file.txt'),
        )
        rules_manager.add_file_extension_to_skip('txt')
        self.assertFalse(
            expr=rules_manager.should_scan_file_path('file.txt'),
        )

        rules_manager.add_file_extension_to_skip('pdf')
        self.assertFalse(
            expr=rules_manager.should_scan_file_path('file.txt'),
        )
        self.assertFalse(
            expr=rules_manager.should_scan_file_path('file.pdf'),
        )
        self.assertFalse(
            expr=rules_manager.should_scan_file_path('file.other.pdf'),
        )
        self.assertTrue(
            expr=rules_manager.should_scan_file_path('file.pdf.other'),
        )
        self.assertTrue(
            expr=rules_manager.should_scan_file_path('file.doc'),
        )

    def test_should_scan_file_ignored_file_paths(
        self,
    ):
        rules_manager = pyrepscan.RulesManager()

        self.assertTrue(
            expr=rules_manager.should_scan_file_path('/site-packages/file.txt'),
        )

        rules_manager.add_file_path_to_skip('site-packages')
        self.assertFalse(
            expr=rules_manager.should_scan_file_path('/site-packages/file.txt'),
        )
        self.assertTrue(
            expr=rules_manager.should_scan_file_path('/folder_one/subfolder/file.txt'),
        )

        rules_manager.add_file_path_to_skip('folder_one/subfolder')
        self.assertFalse(
            expr=rules_manager.should_scan_file_path('/folder_one/subfolder/file.txt'),
        )
        self.assertTrue(
            expr=rules_manager.should_scan_file_path('/folder_one/sub/file.txt'),
        )

        rules_manager.add_file_path_to_skip('part/name')
        self.assertFalse(
            expr=rules_manager.should_scan_file_path('some_part/name_some'),
        )

    def test_add_content_rule_one(
        self,
    ):
        rules_manager = pyrepscan.RulesManager()
        rules_manager.add_content_rule(
            name='rule_one',
            pattern=r'([a-z]+)',
            whitelist_patterns=[],
            blacklist_patterns=[],
        )

        self.assertEqual(
            first=rules_manager.scan_file(
                file_path='',
                content='first line\nsecond line\nthird line',
            ),
            second=[
                {
                    'match_text': 'first',
                    'rule_name': 'rule_one',
                },
                {
                    'match_text': 'line',
                    'rule_name': 'rule_one',
                },
                {
                    'match_text': 'second',
                    'rule_name': 'rule_one',
                },
                {
                    'match_text': 'line',
                    'rule_name': 'rule_one',
                },
                {
                    'match_text': 'third',
                    'rule_name': 'rule_one',
                },
                {
                    'match_text': 'line',
                    'rule_name': 'rule_one',
                },
            ],
        )

    def test_add_content_rule_two(
        self,
    ):
        rules_manager = pyrepscan.RulesManager()
        rules_manager.add_content_rule(
            name='rule_one',
            pattern=r'([a-z]+)',
            whitelist_patterns=[],
            blacklist_patterns=[
                r'line',
            ],
        )

        self.assertEqual(
            first=rules_manager.scan_file(
                file_path='',
                content='first line\nsecond line\nthird line',
            ),
            second=[
                {
                    'match_text': 'first',
                    'rule_name': 'rule_one',
                },
                {
                    'match_text': 'second',
                    'rule_name': 'rule_one',
                },
                {
                    'match_text': 'third',
                    'rule_name': 'rule_one',
                },
            ],
        )

    def test_add_content_rule_three(
        self,
    ):
        rules_manager = pyrepscan.RulesManager()
        rules_manager.add_content_rule(
            name='rule_one',
            pattern=r'([a-z]+)',
            whitelist_patterns=[
                'second',
                'third',
            ],
            blacklist_patterns=[],
        )

        self.assertEqual(
            first=rules_manager.scan_file(
                file_path='',
                content='first line\nsecond line\nthird line',
            ),
            second=[
                {
                    'match_text': 'second',
                    'rule_name': 'rule_one',
                },
                {
                    'match_text': 'third',
                    'rule_name': 'rule_one',
                },
            ],
        )

    def test_add_content_rule_four(
        self,
    ):
        rules_manager = pyrepscan.RulesManager()
        rules_manager.add_content_rule(
            name='rule_one',
            pattern=r'([a-z]+)',
            whitelist_patterns=[
                'second',
                'third',
            ],
            blacklist_patterns=[
                r'nd$',
            ],
        )

        self.assertEqual(
            first=rules_manager.scan_file(
                file_path='',
                content='first line\nsecond line\nthird line',
            ),
            second=[
                {
                    'match_text': 'third',
                    'rule_name': 'rule_one',
                },
            ],
        )

    def test_add_content_rule_five(
        self,
    ):
        rules_manager = pyrepscan.RulesManager()
        rules_manager.add_content_rule(
            name='rule_one',
            pattern=r'(nothing)',
            whitelist_patterns=[],
            blacklist_patterns=[],
        )

        self.assertIsNone(
            obj=rules_manager.scan_file(
                file_path='',
                content='first line\nsecond line\nthird line',
            ),
        )

    def test_add_content_rule_exceptions(
        self,
    ):
        rules_manager = pyrepscan.RulesManager()

        with self.assertRaises(
            expected_exception=RuntimeError,
        ):
            rules_manager.add_content_rule(
                name='',
                pattern=r'regex',
                whitelist_patterns=[],
                blacklist_patterns=[],
            )

        with self.assertRaises(
            expected_exception=RuntimeError,
        ):
            rules_manager.add_content_rule(
                name='rule_one',
                pattern=r'',
                whitelist_patterns=[],
                blacklist_patterns=[],
            )

        with self.assertRaises(
            expected_exception=RuntimeError,
        ):
            rules_manager.add_content_rule(
                name='rule_one',
                pattern=r'(',
                whitelist_patterns=[],
                blacklist_patterns=[],
            )

        with self.assertRaises(
            expected_exception=RuntimeError,
        ):
            rules_manager.add_content_rule(
                name='rule_one',
                pattern=r'regex_pattern_without_capturing_group',
                whitelist_patterns=[],
                blacklist_patterns=[],
            )

        with self.assertRaises(
            expected_exception=RuntimeError,
        ):
            rules_manager.add_content_rule(
                name='rule_two',
                pattern=r'(content)',
                whitelist_patterns=[],
                blacklist_patterns=[
                    '(',
                ],
            )

        with self.assertRaises(
            expected_exception=RuntimeError,
        ):
            rules_manager.add_content_rule(
                name='rule_two',
                pattern=r'(content)',
                whitelist_patterns=[],
                blacklist_patterns=[
                    '(blacklist_regex_with_capturing_group)',
                ],
            )

        with self.assertRaises(
            expected_exception=RuntimeError,
        ):
            rules_manager.add_content_rule(
                name='rule_two',
                pattern=r'(content)',
                whitelist_patterns=[
                    '(',
                ],
                blacklist_patterns=[],
            )

        with self.assertRaises(
            expected_exception=RuntimeError,
        ):
            rules_manager.add_content_rule(
                name='rule_two',
                pattern=r'(content)',
                whitelist_patterns=[
                    '(whitelist_regex_with_capturing_group)',
                ],
                blacklist_patterns=[],
            )

    def test_add_file_path_rule_one(
        self,
    ):
        rules_manager = pyrepscan.RulesManager()
        rules_manager.add_file_path_rule(
            name='rule_one',
            pattern=r'(prod|dev|stage).+key',
        )

        self.assertIsNone(
            obj=rules_manager.scan_file(
                file_path='workdir/prod/some_file',
                content=None,
            ),
        )
        self.assertEqual(
            first=rules_manager.scan_file(
                file_path='workdir/prod/some_file.key',
                content=None,
            ),
            second=[
                {
                    'match_text': 'workdir/prod/some_file.key',
                    'rule_name': 'rule_one',
                },
            ],
        )

        rules_manager.add_file_path_rule(
            name='rule_two',
            pattern=r'prod.+key',
        )

        self.assertIsNone(
            obj=rules_manager.scan_file(
                file_path='workdir/prod/some_file',
                content=None,
            ),
        )
        self.assertEqual(
            first=rules_manager.scan_file(
                file_path='workdir/prod/some_file.key',
                content=None,
            ),
            second=[
                {
                    'match_text': 'workdir/prod/some_file.key',
                    'rule_name': 'rule_one',
                },
                {
                    'match_text': 'workdir/prod/some_file.key',
                    'rule_name': 'rule_two',
                },
            ],
        )

    def test_add_file_path_rule_exceptions(
        self,
    ):
        rules_manager = pyrepscan.RulesManager()

        with self.assertRaises(
            expected_exception=RuntimeError,
        ):
            rules_manager.add_file_path_rule(
                name='',
                pattern=r'regex',
            )

        with self.assertRaises(
            expected_exception=RuntimeError,
        ):
            rules_manager.add_file_path_rule(
                name='rule_one',
                pattern=r'',
            )

    def test_add_file_extension_to_skip_exceptions(
        self,
    ):
        rules_manager = pyrepscan.RulesManager()

        with self.assertRaises(
            expected_exception=RuntimeError,
        ):
            rules_manager.add_file_extension_to_skip(
                file_extension='',
            )

    def test_add_file_path_to_skip_exceptions(
        self,
    ):
        rules_manager = pyrepscan.RulesManager()

        with self.assertRaises(
            expected_exception=RuntimeError,
        ):
            rules_manager.add_file_path_to_skip(
                file_path='',
            )

    def test_scan_file_one(
        self,
    ):
        rules_manager = pyrepscan.RulesManager()

        self.assertIsNone(
            obj=rules_manager.scan_file(
                file_path='/path/to/file.txt',
                content=None,
            ),
        )

    def test_scan_file_two(
        self,
    ):
        rules_manager = pyrepscan.RulesManager()

        rules_manager.add_content_rule(
            name='rule_one',
            pattern=r'(some_text)',
            whitelist_patterns=[],
            blacklist_patterns=[],
        )
        self.assertIsNone(
            obj=rules_manager.scan_file(
                file_path='/path/to/file.txt',
                content=None,
            ),
        )
        self.assertIsNone(
            obj=rules_manager.scan_file(
                file_path='/path/to/file.txt',
                content='',
            ),
        )
        self.assertIsNone(
            obj=rules_manager.scan_file(
                file_path='/path/to/file.txt',
                content='other_text',
            ),
        )
        self.assertEqual(
            first=rules_manager.scan_file(
                file_path='/path/to/file.txt',
                content='some_text',
            ),
            second=[
                {
                    'rule_name': 'rule_one',
                    'match_text': 'some_text',
                },
            ],
        )

        rules_manager.add_content_rule(
            name='rule_two',
            pattern=r'(some)',
            whitelist_patterns=[],
            blacklist_patterns=[],
        )
        self.assertEqual(
            first=rules_manager.scan_file(
                file_path='/path/to/file.txt',
                content='some_text',
            ),
            second=[
                {
                    'rule_name': 'rule_one',
                    'match_text': 'some_text',
                },
                {
                    'rule_name': 'rule_two',
                    'match_text': 'some',
                },
            ],
        )

    def test_scan_file_three(
        self,
    ):
        rules_manager = pyrepscan.RulesManager()

        rules_manager.add_content_rule(
            name='rule_one',
            pattern=r'(some_.+)',
            whitelist_patterns=[],
            blacklist_patterns=[
                r'text',
            ],
        )
        self.assertIsNone(
            obj=rules_manager.scan_file(
                file_path='/path/to/file.txt',
                content='some_text',
            ),
        )
        self.assertEqual(
            first=rules_manager.scan_file(
                file_path='/path/to/file.txt',
                content='some_other',
            ),
            second=[
                {
                    'rule_name': 'rule_one',
                    'match_text': 'some_other',
                },
            ],
        )

    def test_scan_file_four(
        self,
    ):
        rules_manager = pyrepscan.RulesManager()

        rules_manager.add_content_rule(
            name='rule_one',
            pattern=r'(some_.+)',
            whitelist_patterns=[],
            blacklist_patterns=[
                r'text',
                r'other',
            ],
        )
        self.assertIsNone(
            obj=rules_manager.scan_file(
                file_path='/path/to/file.txt',
                content='some_text',
            ),
        )
        self.assertIsNone(
            obj=rules_manager.scan_file(
                file_path='/path/to/file.txt',
                content='some_other',
            ),
        )
        self.assertEqual(
            first=rules_manager.scan_file(
                file_path='/path/to/file.txt',
                content='some_diff',
            ),
            second=[
                {
                    'rule_name': 'rule_one',
                    'match_text': 'some_diff',
                },
            ],
        )

    def test_scan_file_five(
        self,
    ):
        rules_manager = pyrepscan.RulesManager()

        rules_manager.add_content_rule(
            name='rule_one',
            pattern=r'(some_.+)',
            whitelist_patterns=[
                'diff',
            ],
            blacklist_patterns=[],
        )
        self.assertIsNone(
            obj=rules_manager.scan_file(
                file_path='/path/to/file.txt',
                content='some_text',
            ),
        )
        self.assertIsNone(
            obj=rules_manager.scan_file(
                file_path='/path/to/file.txt',
                content='some_other',
            ),
        )
        self.assertEqual(
            first=rules_manager.scan_file(
                file_path='/path/to/file.txt',
                content='some_diff',
            ),
            second=[
                {
                    'rule_name': 'rule_one',
                    'match_text': 'some_diff',
                },
            ],
        )

    def test_scan_file_six(
        self,
    ):
        rules_manager = pyrepscan.RulesManager()

        rules_manager.add_content_rule(
            name='rule_one',
            pattern=r'(some_.+)',
            whitelist_patterns=[
                'diff',
                'other',
            ],
            blacklist_patterns=[],
        )
        self.assertIsNone(
            obj=rules_manager.scan_file(
                file_path='/path/to/file.txt',
                content='some_text',
            ),
        )
        self.assertEqual(
            first=rules_manager.scan_file(
                file_path='/path/to/file.txt',
                content='some_other',
            ),
            second=[
                {
                    'rule_name': 'rule_one',
                    'match_text': 'some_other',
                },
            ],
        )
        self.assertEqual(
            first=rules_manager.scan_file(
                file_path='/path/to/file.txt',
                content='some_diff',
            ),
            second=[
                {
                    'rule_name': 'rule_one',
                    'match_text': 'some_diff',
                },
            ],
        )

    def test_scan_file_seven(
        self,
    ):
        rules_manager = pyrepscan.RulesManager()

        rules_manager.add_file_path_rule(
            name='rule_one',
            pattern=r'dev\.txt',
        )
        self.assertIsNone(
            obj=rules_manager.scan_file(
                file_path='/path/to/file.txt',
                content=None,
            ),
        )
        self.assertIsNone(
            obj=rules_manager.scan_file(
                file_path='/path/to/file.txt',
                content='',
            ),
        )
        self.assertIsNone(
            obj=rules_manager.scan_file(
                file_path='/path/to/file.txt',
                content='other_text',
            ),
        )
        self.assertEqual(
            first=rules_manager.scan_file(
                file_path='/path/to/dev.txt',
                content='',
            ),
            second=[
                {
                    'rule_name': 'rule_one',
                    'match_text': '/path/to/dev.txt',
                },
            ],
        )

        rules_manager.add_file_path_rule(
            name='rule_two',
            pattern=r'(\.txt)',
        )
        self.assertEqual(
            first=rules_manager.scan_file(
                file_path='/path/to/dev.txt',
                content='some_text',
            ),
            second=[
                {
                    'rule_name': 'rule_one',
                    'match_text': '/path/to/dev.txt',
                },
                {
                    'rule_name': 'rule_two',
                    'match_text': '/path/to/dev.txt',
                },
            ],
        )

    def test_check_pattern(
        self,
    ):
        rules_manager = pyrepscan.RulesManager()

        with self.assertRaises(
            expected_exception=RuntimeError,
        ):
            rules_manager.check_pattern(
                content='',
                pattern=r'(',
            )

        with self.assertRaises(
            expected_exception=RuntimeError,
        ):
            rules_manager.check_pattern(
                content='',
                pattern=r'no_capturing_group',
            )

        with self.assertRaises(
            expected_exception=RuntimeError,
        ):
            rules_manager.check_pattern(
                content='',
                pattern=r'(?:\:)',
            )

        self.assertEqual(
            first=rules_manager.check_pattern(
                content='some sentence',
                pattern=r'([^ ]+)',
            ),
            second=[
                'some',
                'sentence',
            ]
        )

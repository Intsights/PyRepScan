import unittest
import tempfile
import git
import datetime

import pyrepscan


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
        with open(f'{self.tmpdir.name}/prod_env_with_content.key', 'w') as tmpfile:
            tmpfile.write('some_key')
        with open(f'{self.tmpdir.name}/file.other', 'w') as tmpfile:
            tmpfile.write('nothing special')
        with open(f'{self.tmpdir.name}/test_file.cpp', 'w') as tmpfile:
            tmpfile.write('content')
        bare_repo.index.add(
            items=[
                f'{self.tmpdir.name}/file.txt',
                f'{self.tmpdir.name}/file.py',
                f'{self.tmpdir.name}/prod_env.key',
                f'{self.tmpdir.name}/prod_env_with_content.key',
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
        bare_repo.close()

    def test_scan_regular(
        self,
    ):
        grs = pyrepscan.GitRepositoryScanner()
        grs.add_content_rule(
            name='First Rule',
            pattern=r'''(content)''',
            whitelist_patterns=[],
            blacklist_patterns=[],
        )

        grs.add_file_extension_to_skip('py')
        grs.add_file_path_to_skip('test_')

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
                    'match_text': 'content',
                    'rule_name': 'First Rule'
                },
                {
                    'author_email': 'test@author.email',
                    'author_name': 'Author Name',
                    'commit_message': 'edited file in new branch',
                    'commit_time': '2002-01-01T00:00:00',
                    'file_oid': '0407a18f7c6802c7e7ddc5c9e8af4a34584383ff',
                    'file_path': 'file.txt',
                    'match_text': 'content',
                    'rule_name': 'First Rule'
                },
                {
                    'author_email': 'test@author.email',
                    'author_name': 'Author Name',
                    'commit_message': 'initial commit',
                    'commit_time': '2000-01-01T00:00:00',
                    'file_oid': '6b584e8ece562ebffc15d38808cd6b98fc3d97ea',
                    'file_path': 'file.txt',
                    'match_text': 'content',
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
                    'match_text': 'content',
                    'rule_name': 'First Rule'
                },
                {
                    'author_email': 'test@author.email',
                    'author_name': 'Author Name',
                    'commit_message': 'edited file in new branch',
                    'commit_time': '2002-01-01T00:00:00',
                    'file_oid': '0407a18f7c6802c7e7ddc5c9e8af4a34584383ff',
                    'file_path': 'file.txt',
                    'match_text': 'content',
                    'rule_name': 'First Rule'
                },
                {
                    'author_email': 'test@author.email',
                    'author_name': 'Author Name',
                    'commit_message': 'initial commit',
                    'commit_time': '2000-01-01T00:00:00',
                    'file_oid': '6b584e8ece562ebffc15d38808cd6b98fc3d97ea',
                    'file_path': 'file.txt',
                    'match_text': 'content',
                    'rule_name': 'First Rule'
                },
                {
                    'author_email': 'test@author.email',
                    'author_name': 'Author Name',
                    'commit_message': 'edited file in non_merged_branch',
                    'commit_time': '2004-01-01T00:00:00',
                    'file_oid': '057032a2108721ad1de6a9240fd1a8f45bc3f2ef',
                    'file_path': 'file.txt',
                    'match_text': 'content',
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
            pattern=r'''(content)''',
            whitelist_patterns=[],
            blacklist_patterns=[],
        )

        grs.add_file_extension_to_skip('py')
        grs.add_file_path_to_skip('test_')

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
                    'match_text': 'content',
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
        grs.add_file_path_rule(
            name='First Rule',
            pattern=r'(prod|dev|stage).+key',
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
                    'file_oid': 'ec3741ea9c00bc5cd88564e49fd81d2340a5582f',
                    'file_path': 'prod_env_with_content.key',
                    'match_text': 'prod_env_with_content.key',
                    'rule_name': 'First Rule'
                },
            ],
        )

    def test_get_file_content(
        self,
    ):
        grs = pyrepscan.GitRepositoryScanner()

        self.assertEqual(
            first=grs.get_file_content(
                repository_path=self.tmpdir.name,
                file_oid='0407a18f7c6802c7e7ddc5c9e8af4a34584383ff',
            ),
            second=b'new content from new branch',
        )

    def test_scan_exceptions(
        self,
    ):
        grs = pyrepscan.GitRepositoryScanner()

        with self.assertRaises(
            expected_exception=RuntimeError,
        ):
            grs.scan(
                repository_path='/non/existent/path',
            )

    def test_add_content_rule_exceptions(
        self,
    ):
        grs = pyrepscan.GitRepositoryScanner()

        with self.assertRaises(
            expected_exception=RuntimeError,
        ):
            grs.add_content_rule(
                name='',
                pattern=r'regex',
                whitelist_patterns=[],
                blacklist_patterns=[],
            )

    def test_add_file_path_rule_exceptions(
        self,
    ):
        grs = pyrepscan.GitRepositoryScanner()

        with self.assertRaises(
            expected_exception=RuntimeError,
        ):
            grs.add_file_path_rule(
                name='',
                pattern=r'regex',
            )

    def test_add_file_extension_to_skip_exceptions(
        self,
    ):
        grs = pyrepscan.GitRepositoryScanner()

        with self.assertRaises(
            expected_exception=RuntimeError,
        ):
            grs.add_file_extension_to_skip(
                file_extension='',
            )

    def test_add_file_path_to_skip_exceptions(
        self,
    ):
        grs = pyrepscan.GitRepositoryScanner()

        with self.assertRaises(
            expected_exception=RuntimeError,
        ):
            grs.add_file_path_to_skip(
                file_path='',
            )

    def test_get_file_content_exceptions(
        self,
    ):
        grs = pyrepscan.GitRepositoryScanner()

        with self.assertRaises(
            expected_exception=RuntimeError,
        ):
            grs.get_file_content(
                repository_path=self.tmpdir.name,
                file_oid='',
            )

        with self.assertRaises(
            expected_exception=RuntimeError,
        ):
            grs.get_file_content(
                repository_path=self.tmpdir.name,
                file_oid='aaaaaaaaa',
            )

        with self.assertRaises(
            expected_exception=RuntimeError,
        ):
            grs.get_file_content(
                repository_path=self.tmpdir.name,
                file_oid='0407a18f7c6802c7e7ddc5c9e8af4a34584383fa',
            )

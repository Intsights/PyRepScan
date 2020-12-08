import pyrepscan


grs = pyrepscan.GitRepositoryScanner()
grs.add_content_rule(
    name='AWS Manager ID',
    pattern=r'(A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}',
    whitelist_patterns=[],
    blacklist_patterns=[],
)
results = grs.scan(
    repository_path='/path/to/repository',
    branch_glob_pattern='*',
)

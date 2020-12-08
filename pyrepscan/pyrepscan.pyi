import typing


class GitRepositoryScanner:
    def __init__(
        self,
    ) -> None: ...

    def add_content_rule(
        self,
        name: str,
        pattern: str,
        whitelist_patterns: typing.List[str],
        blacklist_patterns: typing.List[str],
    ) -> None: ...

    def add_file_path_rule(
        self,
        name: str,
        pattern: str,
    ) -> None: ...

    def add_file_extension_to_skip(
        self,
        file_extension: str,
    ) -> None: ...

    def add_file_path_to_skip(
        self,
        file_path: str,
    ) -> None: ...

    def scan(
        self,
        repository_path: str,
        branch_glob_pattern: typing.Optional[str],
        from_timestamp: typing.Optional[int],
    ) -> typing.List[typing.Dict[str, str]]: ...

    def get_file_content(
        self,
        repository_path: str,
        file_oid: str,
    ) -> bytes: ...


class RulesManager:
    def __init__(
        self,
    ) -> None: ...

    def add_content_rule(
        self,
        name: str,
        pattern: str,
        whitelist_patterns: typing.List[str],
        blacklist_patterns: typing.List[str],
    ) -> None: ...

    def add_file_path_rule(
        self,
        name: str,
        pattern: str,
    ) -> None: ...

    def add_file_extension_to_skip(
        self,
        file_extension: str,
    ) -> None: ...

    def add_file_path_to_skip(
        self,
        file_path: str,
    ) -> None: ...

    def should_scan_file_path(
        self,
        file_path: str,
    ) -> bool: ...

    def scan_file(
        self,
        file_path: str,
        content: typing.Optional[str],
    ) -> typing.Optional[typing.List[typing.Dict[str, str]]]: ...

    def check_pattern(
        self,
        content: str,
        pattern: str,
    ) -> typing.List[str]: ...

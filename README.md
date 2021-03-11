<p align="center">
    <a href="https://github.com/intsights/PyRepScan">
        <img src="https://raw.githubusercontent.com/intsights/PyRepScan/master/images/logo.png" alt="Logo">
    </a>
    <h3 align="center">
        A Git Repository Secrets Scanner written in Rust
    </h3>
</p>

![license](https://img.shields.io/badge/MIT-License-blue)
![Python](https://img.shields.io/badge/Python-3.6%20%7C%203.7%20%7C%203.8%20%7C%203.9-blue)
![Build](https://github.com/intsights/PyRepScan/workflows/Build/badge.svg)
[![PyPi](https://img.shields.io/pypi/v/PyRepScan.svg)](https://pypi.org/project/PyRepScan/)

## Table of Contents

- [Table of Contents](#table-of-contents)
- [About The Project](#about-the-project)
  - [Built With](#built-with)
  - [Performance](#performance)
    - [CPU](#cpu)
  - [Installation](#installation)
- [Documentation](#documentation)
- [Usage](#usage)
- [License](#license)
- [Contact](#contact)


## About The Project

PyRepScan is a python library written in Rust. The library uses [git2-rs](https://github.com/rust-lang/git2-rs) for repository parsing and traversing, [regex](https://github.com/rust-lang/regex) for regex pattern matching and [rayon](https://github.com/rayon-rs/rayon) for concurrency. The library was written to achieve high performance and python bindings.


### Built With

* [git2-rs](https://github.com/rust-lang/git2-rs)
* [regex](https://github.com/rust-lang/regex)
* [rayon](https://github.com/rayon-rs/rayon)


### Performance

#### CPU
| Library | Time | Peak Memory |
| ------------- | ------------- | ------------- |
| [PyRepScan](https://github.com/intsights/PyRepScan) | 4s | 501,708 kb |
| [gitleaks](https://github.com/zricethezav/gitleaks) | 507s | 823,016 kb |


### Installation

```sh
pip3 install PyRepScan
```


## Documentation

```python
class GitRepositoryScanner:
    def __init__(
      self,
    ) -> None
```
This class holds all the added rules for fast reuse.


```python
def add_content_rule(
    self,
    name: str,
    pattern: str,
    whitelist_patterns: typing.List[str],
    blacklist_patterns: typing.List[str],
) -> None
```
The `add_content_rule` function adds a new rule to an internal list of rules that could be reused multiple times against different repositories. The same name can be used multiple times and would lead to results which can hold the same name. Content rule means that the regex pattern would be tested against the content of the files.
- `name` - The name of the rule so it can be identified.
- `pattern` - The regex pattern (Rust Regex syntax) to match against the content of the commited files.
- `whitelist_patterns` - A list of regex patterns (Rust Regex syntax) to match against the content of the committed file to filter in results. Only one of the patterns should be matched to pass through the result. There is an OR relation between the patterns.
- `blacklist_patterns` - A list of regex patterns (Rust Regex syntax) to match against the content of the committed file to filter out results. Only one of the patterns should be matched to omit the result. There is an OR relation between the patterns.


```python
def add_file_path_rule(
    self,
    name: str,
    pattern: str,
) -> None
```
The `add_file_path_rule` function adds a new rule to an internal list of rules that could be reused multiple times against different repositories. The same name can be used multiple times and would lead to results which can hold the same name. File name rule means that the regex pattern would be tested against the file paths.
- `name` - The name of the rule so it can be identified.
- `pattern` - The regex pattern (Rust Regex syntax) to match against the file paths of the commited files.


```python
def add_file_extension_to_skip(
    self,
    file_extension: str,
) -> None
```
The `add_file_extension_to_skip` function adds a new file extension to the filtering phase to reduce the amount of inspected files and to increase the performance of the scan.
- `file_extension` - A file extension, without a leading dot, to filter out from the scan.


```python
def add_file_path_to_skip(
    self,
    file_path: str,
) -> None
```
The `add_file_path_to_skip` function adds a new file path pattern to the filtering phase to reduce the amount of inspected files and to increase the performance of the scan. Every file path that would include the `file_path` substring would be left out of the scanned files.
- `file_path` - If the inspected file path would include this substring, it won't be scanned. This parameter is a free text.


```python
def scan(
    self,
    repository_path: str,
    branch_glob_pattern: typing.Optional[str],
    from_timestamp: typing.Optional[int],
) -> typing.List[typing.Dict[str, str]]
```
The `scan` function is the main function in the library. Calling this function would trigger a new scan that would return a list of matches. The scan function is a multithreaded operation, that would utilize all the available core in the system. The results would not include the file content but only the regex matching group. To retrieve the full file content one should take the `results['oid']` and to call `get_file_content` function.
- `repository_path` - The git repository folder path.
- `branch_glob_pattern` - A glob pattern to filter branches for the scan. If None is sent, defaults to `*`.
- `from_timestamp` - A UTC timestamp (Int) that only commits that were created after this timestamp would be included in the scan. If None is sent, defaults to `0`.

A sample result would look like this:
```python
{
    'rule_name': 'First Rule',
    'author_email': 'author@email.email',
    'author_name': 'Author Name',
    'commit_id': '1111111111111111111111111111111111111111',
    'commit_message': 'The commit message',
    'commit_time': '2020-01-01T00:00:00e',
    'file_path': 'full/file/path',
    'file_oid': '47d2739ba2c34690248c8f91b84bb54e8936899a',
    'match': 'The matched group',
}
```


```python
def scan_from_url(
    self,
    url: str,
    repository_path: str,
    branch_glob_pattern: typing.Optional[str],
    from_timestamp: typing.Optional[int],
) -> typing.List[typing.Dict[str, str]]
```
The same as `scan` function but also clones a repository from a given URL into the provided repository path.
- `url` - URL of a git repository.
- `repository_path` - The path to clone the repository to
- `branch_glob_pattern` - A glob pattern to filter branches for the scan. If None is sent, defaults to `*`.
- `from_timestamp` - A UTC timestamp (Int) that only commits that were created after this timestamp would be included in the scan. If None is sent, defaults to `0`.


```python
def get_file_content(
    self,
    repository_path: str,
    file_oid: str,
) -> bytes
```
The `get_file_content` function exists to retrieve the content of a file that was previously matched. The full file content is omitted from the results to reduce the results list size and to deliver better performance.
- `repository_path` - The git repository folder path.
- `file_oid` - A string representing the file oid. This parameter exists in the results dictionary returned by the `scan` function.


## Usage

```python
import pyrepscan

grs = pyrepscan.GitRepositoryScanner()

# Adds a specific rule, can be called multiple times or none
grs.add_content_rule(
    name='First Rule',
    pattern=r'(-----BEGIN PRIVATE KEY-----)',
    whitelist_patterns=[],
    blacklist_patterns=[],
)
grs.add_file_path_rule(
    name='Second Rule',
    pattern=r'.+\.pem',
)
grs.add_file_path_rule(
    name='Third Rule',
    pattern=r'(prod|dev|stage).+key',
)

# Add file extensions to ignore during the search
grs.add_file_extension_to_skip(
    file_extension='bin',
)
grs.add_file_extension_to_skip(
    file_extension='jpg',
)

# Add file paths to ignore during the search. Free text is allowed
grs.add_file_path_to_skip(
    file_path='site-packages',
)
grs.add_file_path_to_skip(
    file_path='node_modules',
)

# Scans a repository
results = grs.scan(
    repository_path='/repository/path',
    branch_glob_pattern='*',
)

# Results is a list of dicts. Each dict is in the following format:
{
    'rule_name': 'First Rule',
    'author_email': 'author@email.email',
    'author_name': 'Author Name',
    'commit_id': '1111111111111111111111111111111111111111',
    'commit_message': 'The commit message',
    'commit_time': '2020-01-01T00:00:00e',
    'file_path': 'full/file/path',
    'file_oid': '47d2739ba2c34690248c8f91b84bb54e8936899a',
    'match': 'The matched group',
}

# Fetch the file_oid full content
file_content = grs.get_file_content(
    repository_path='/repository/path',
    file_oid='47d2739ba2c34690248c8f91b84bb54e8936899a',
)

# file_content
b'binary data'

# Creating a RulesManager directly
rules_manager = pyrepscan.RulesManager()

# For testing purposes, check your regexes pattern using check_pattern function
rules_manager.check_pattern(
    content='some content1 to check, another content2 in the same line\nanother content3 in another line\n',
    pattern=r'(content\d)',
)

# Results are the list of captured matches
[
    'content1',
    'content2',
    'content3',
]
```


## License

Distributed under the MIT License. See `LICENSE` for more information.


## Contact

Gal Ben David - gal@intsights.com

Project Link: [https://github.com/intsights/PyRepScan](https://github.com/intsights/PyRepScan)

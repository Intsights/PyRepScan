<p align="center">
    <a href="https://github.com/intsights/PyRepScan">
        <img src="https://raw.githubusercontent.com/intsights/PyRepScan/master/images/logo.png" alt="Logo">
    </a>
    <h3 align="center">
        A Git Repository Leaks Scanner Python library written in C++
    </h3>
</p>

![license](https://img.shields.io/badge/MIT-License-blue)
![Python](https://img.shields.io/badge/Python-3.6%20%7C%203.7%20%7C%203.8%20%7C%20pypy3-blue)
![Build](https://github.com/intsights/PyRepScan/workflows/Build/badge.svg)
[![PyPi](https://img.shields.io/pypi/v/PyRepScan.svg)](https://pypi.org/project/PyRepScan/)

## Table of Contents

- [Table of Contents](#table-of-contents)
- [About The Project](#about-the-project)
  - [Built With](#built-with)
  - [Performance](#performance)
    - [CPU](#cpu)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Documentation](#documentation)
- [Usage](#usage)
- [License](#license)
- [Contact](#contact)


## About The Project

PyRepScan is a python library written in C++. The library uses [libgit2](https://github.com/libgit2/libgit2) for repository parsing and traversing, [re2](https://github.com/google/re2) for regex pattern matching and [taskflow](https://github.com/taskflow/taskflow) for concurrency. The library was written to achieve high performance and python bindings.


### Built With

* [libgit2](https://github.com/libgit2/libgit2)
* [re2](https://github.com/google/re2)
* [taskflow](https://github.com/taskflow/taskflow)


### Performance

#### CPU
| Library | Time | Improvement Factor |
| ------------- | ------------- | ------------- |
| [PyRepScan](https://github.com/intsights/PyRepScan) | 2.18s | 1.0x |
| [gitleaks](https://github.com/zricethezav/gitleaks) | 63.0s | 28.9x |


### Prerequisites

In order to compile this package you should have GCC & Python development package installed.
* Fedora
```sh
sudo dnf install python3-devel gcc-c++ libgit2-devel re2-devel
```
* Ubuntu 20.04
```sh
sudo apt install python3-dev libgit2-dev libre2-dev
```

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
def add_rule(
    self,
    name: str,
    match_pattern: str,
    match_whitelist_patterns: typing.List[str],
    match_blacklist_patterns: typing.List[str],
) -> None
```
The `add_rule` function adds a new rule to an internal list of rules that could be reused multiple times against different repositories. The same name can be used multiple times and would lead to results which can hold the same name.
- `name` - The name of the rule so it can be identified.
- `match_pattern` - The regex pattern (RE2 syntax) to match against the content of the commited files.
- `match_whitelist_patterns` - A list of regex patterns (RE2 syntax) to match against the content of the committed file to filter in results. Only one of the patterns should be matched to pass through the result. There is an OR relation between the patterns.
- `match_blacklist_patterns` - A list of regex patterns (RE2 syntax) to match against the content of the committed file to filter out results. Only one of the patterns should be matched to omit the result. There is an OR relation between the patterns.


```python
def add_ignored_file_extension(
    self,
    file_extension: str,
) -> None
```
The `add_ignored_file_extension` function adds a new file extension to the filtering phase to reduce the amount of inspected files and to increase the performance of the scan.
- `file_extension` - A file extension, without a leading dot, to filter out from the scan.


```python
def add_ignored_file_path(
    self,
    file_path: str,
) -> None
```
The `add_ignored_file_path` function adds a new file pattern to the filtering phase to reduce the amount of inspected files and to increase the performance of the scan. Every file path that would include the `file_path` substring would be left out of the scanned files.
- `file_path` - If the inspected file path would include this substring, it won't be scanned. This parameter is a free text.


```python
def scan(
    self,
    repository_path: str,
    branch_glob_pattern: '*',
    from_timestamp: int,
) -> typing.List[typing.Dict[str, str]]
```
The `scan` function is the main function in the library. Calling this function would trigger a new scan that would return a list of matches. The scan function is a multithreaded operation, that would utilize all the available core in the system. The results would not include the file content but only the regex matching group. To retrieve the full file content one should take the `results['oid']` and to call `get_file_content` function.
- `repository_path` - The git repository folder path.
- `branch_glob_pattern` - A glob pattern to filter branches for the scan.
- `from_timestamp` - A UTC timestamp (Int) that only commits that were created after this timestamp would be included in the scan.

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
def get_file_content(
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
grs.add_rule(
    name='First Rule',
    match_pattern=r'''(-----BEGIN PRIVATE KEY-----)''',
    match_whitelist_patterns=[],
    match_blacklist_patterns=[],
)

# Add file extensions to ignore during the search
grs.add_ignored_file_extension(
    file_extension='bin',
)
grs.add_ignored_file_extension(
    file_extension='jpg',
)

# Add file paths to ignore during the search. Free text is allowed
grs.add_ignored_file_path(
    file_path='site-packages',
)
grs.add_ignored_file_path(
    file_path='node_modules',
)

# Scans a repository
results = grs.scan(
    repository_path='/repository/path',
    branch_glob_pattern='*',
    from_timestamp=0,
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

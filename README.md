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
- [Usage](#usage)
- [License](#license)
- [Contact](#contact)


## About The Project

PyRepScan is a python library written in C++. The library uses [libgit2](https://github.com/libgit2/libgit2) for repository parsing and traversing, [re2](https://github.com/google/re2) for regex pattern matching and [cpp-taskflow](https://github.com/cpp-taskflow/cpp-taskflow) for concurrency. The library was written to achieve high performance and python bindings.


### Built With

* [libgit2](https://github.com/libgit2/libgit2)
* [re2](https://github.com/google/re2)
* [cpp-taskflow](https://github.com/cpp-taskflow/cpp-taskflow)


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
* Ubuntu 18.04
```sh
sudo apt install python3-dev g++-9 libgit2-dev libre2-dev
```

### Installation

```sh
pip3 install PyRepScan
```


## Usage

```python
import pyrepscan

grs = pyrepscan.GitRepositoryScanner()

# Adds a specific rule, can be called multiple times or none
grs.add_rule(
    name='First Rule',
    regex_pattern=r'''(-----BEGIN PRIVATE KEY-----)''',
    regex_blacklist_patterns=[],
)
# Compiles the rules. Should be called only once after all the rules were added
grs.compile_rules()

# Add file extensions to ignore during the search
grs.add_ignored_file_extension('bin')
grs.add_ignored_file_extension('jpg')

# Add file paths to ignore during the search. Free text is allowed
grs.add_ignored_file_path('site-packages')
grs.add_ignored_file_path('node_modules')

# Scans a repository
results = grs.scan('/repository/path')

# Results is a list of dicts. Each dict is in the following format:
# {
#     'author_email': 'author@email.email',
#     'author_name': 'Author Name',
#     'commit_id': '1111111111111111111111111111111111111111',
#     'commit_message': 'The commit message',
#     'content': 'The content of the file that has been matched',
#     'file_path': 'full/file/path',
#     'match': 'The matched group',
#     'rule_name': 'First Rule'
# },
```


## License

Distributed under the MIT License. See `LICENSE` for more information.


## Contact

Gal Ben David - gal@intsights.com

Project Link: [https://github.com/intsights/PyRepScan](https://github.com/intsights/PyRepScan)

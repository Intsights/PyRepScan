mod git_repository_scanner;
mod rules_manager;

use git2::Repository;
use parking_lot::Mutex;
use pyo3::exceptions;
use pyo3::prelude::*;
use pyo3::types::PyBytes;
use std::collections::HashMap;
use std::sync::Arc;

/// GitRepositoryScanner class
/// A git repository scanner object
///
/// input:
///     None
///
/// example:
///     grs = pyrepscan.GitRepositoryScanner()
#[pyclass]
#[text_signature = "()"]
#[derive(Default)]
struct GitRepositoryScanner {
    rules_manager: rules_manager::RulesManager,
}

#[pymethods]
impl GitRepositoryScanner {
    #[new]
    fn new() -> Self {
        Self::default()
    }

    /// Adding a new content rule. A content rule is a rule that will be applied to the content of
    /// the commit changes. For every commit, each file will be scanned and its content will be scanned
    /// with the content rules.
    ///
    /// input:
    ///     name: str -> The name of the rules. This will help to identify which rule has been matched.
    ///     pattern: str -> The regex pattern. The pattern should be in Rust regex syntax.
    ///     whitelist_patterns: list[str] -> A list of regex patterns. If this list is empty nothing happens.
    ///         If the list contains one or more regex patterns, each regex pattern will be applied to to the
    ///         matched content. There should be at least one regex pattern that matched to approve the secret.
    ///     blacklist_patterns: list[str] -> A list of regex patterns. If this list is empty nothing happens.
    ///         If the list contains one or more regex patterns, each regex pattern will be applied to to the
    ///         matched content. There should be at least one regex pattern that matched to reject the secret.
    ///
    /// returns:
    ///     None
    ///
    /// example:
    ///     grs.add_content_rule(
    ///         name="Rule #1",
    ///         pattern=r"password=([\d\w]+)",
    ///         whitelist_patterns=[],
    ///         blacklist_patterns=[
    ///             "(?:test|example|xxx|empty)",
    ///         ],
    ///     )
    #[text_signature = "(name, pattern, whitelist_patterns, blacklist_patterns, /)"]
    fn add_content_rule(
        &mut self,
        name: String,
        pattern: String,
        whitelist_patterns: Vec<String>,
        blacklist_patterns: Vec<String>,
    ) -> PyResult<()> {
        self.rules_manager.add_content_rule(
            name,
            pattern,
            whitelist_patterns,
            blacklist_patterns,
        )
    }

    /// Adding a new file path rule. A file path rule is a rule that will be applied to the file path of
    /// the commit changes. For every commit, each file will be scanned.
    ///
    /// input:
    ///     name: str -> The name of the rules. This will help to identify which rule has been matched.
    ///     pattern: str -> The regex pattern. The pattern should be in Rust regex syntax.
    ///
    /// returns:
    ///     None
    ///
    /// example:
    ///     grs.add_file_path_rule(
    ///         name="Rule #2",
    ///         pattern=r".*\.(?:pem|cer)",
    ///     )
    #[text_signature = "(name, pattern, /)"]
    fn add_file_path_rule(
        &mut self,
        name: String,
        pattern: String
    ) -> PyResult<()> {
        self.rules_manager.add_file_path_rule(
            name,
            pattern,
        )
    }

    /// Adding a file extension to ignore during the scan.
    /// Every file with this extension would not be scanned.
    ///
    /// input:
    ///     file_extension: str -> A file extension string. During a scan, the file path will be matched
    ///         using an ends_with function meaning that it can be partial extension, with a dot, or without
    ///
    /// returns:
    ///     None
    ///
    /// example:
    ///     grs.add_file_extension_to_skip(
    ///         file_extension="rar",
    ///     )
    ///     grs.add_file_extension_to_skip(
    ///         file_extension="tar.gz",
    ///     )
    #[text_signature = "(file_extension, /)"]
    fn add_file_extension_to_skip(
        &mut self,
        file_extension: String,
    ) -> PyResult<()> {
        self.rules_manager.add_file_extension_to_skip(file_extension)
    }

    /// Adding a file path pattern to skip during the scan. The pattern should be in a free text format.
    ///
    /// input:
    ///     file_path: str ->  A free text pattern to skip during the scan. If the scanned file path would contain
    ///         this pattern, the scan will skip the file.
    ///
    /// returns:
    ///     None
    ///
    /// example:
    ///     grs.add_file_path_to_skip(
    ///         file_extension="test",
    ///     )
    ///     grs.add_file_path_to_skip(
    ///         file_extension="example",
    ///     )
    #[text_signature = "(file_path, /)"]
    fn add_file_path_to_skip(
        &mut self,
        file_path: String,
    ) -> PyResult<()> {
        self.rules_manager.add_file_path_to_skip(file_path)
    }

    /// Retrieves a file content using its ObjectID.
    ///
    /// input:
    ///     repository_path: str ->  Absolute path of the git repository directory.
    ///     file_oid: str ->  The file OID in a string representation
    ///
    /// returns:
    ///     bytes -> The file content in a binary representation
    ///
    /// example:
    ///     grs.get_file_content(
    ///         repository_path="/path/to/repository",
    ///         file_oid="6b584e8ece562ebffc15d38808cd6b98fc3d97ea",
    ///     )
    #[text_signature = "(repository_path, file_oid, /)"]
    fn get_file_content(
        &mut self,
        py: Python,
        repository_path: String,
        file_oid: String,
    ) -> PyResult<Py<PyBytes>> {
        match git_repository_scanner::get_file_content(&repository_path, &file_oid) {
            Ok(content) => Ok(PyBytes::new(py, &content).into()),
            Err(error) => Err(exceptions::PyRuntimeError::new_err(error.to_string())),
        }
    }

    /// Scan a git repository for secrets. Rules shuld be loaded before calling this function.
    ///
    /// input:
    ///     repository_path: str ->  Absolute path of the git repository directory.
    ///     branch_glob_pattern: str ->  A blob pattern to match against the git branches names.
    ///         Only matched branches will be scanned.
    ///     from_timestamp: int = 0 ->  Unix epoch timestamp to start the scan from.
    ///
    /// returns:
    ///     list[dict] -> List of matches
    ///
    /// example:
    ///     grs.scan(
    ///         repository_path="/path/to/repository",
    ///         branch_glob_pattern="*",
    ///     )
    #[text_signature = "(repository_path, branch_glob_pattern, from_timestamp, /)"]
    fn scan(
        &self,
        py: Python,
        repository_path: &str,
        branch_glob_pattern: Option<&str>,
        from_timestamp: Option<i64>,
    ) -> PyResult<Py<PyAny>> {
        let matches = Arc::new(Mutex::new(Vec::<HashMap<&str, String>>::with_capacity(10000)));

        if let Err(error) = git_repository_scanner::scan_repository(
            repository_path,
            branch_glob_pattern.unwrap_or("*"),
            from_timestamp.unwrap_or(0),
            &self.rules_manager,
            matches.clone(),
        ) {
            Err(exceptions::PyRuntimeError::new_err(error.to_string()))
        } else {
            Ok(matches.lock().to_object(py))
        }
    }

    /// Scan a git repository for secrets. Rules shuld be loaded before calling this function.
    ///
    /// input:
    ///     url: str -> URL of a git repository
    ///     repository_path: str ->  The path to clone the repository to
    ///     branch_glob_pattern: str ->  A blob pattern to match against the git branches names.
    ///         Only matched branches will be scanned.
    ///     from_timestamp: int = 0 ->  Unix epoch timestamp to start the scan from.
    ///
    /// returns:
    ///     list[dict] -> List of matches
    ///
    /// example:
    ///     grs.scan_from_url(
    ///         url="https://github.com/rust-lang/git2-rs",
    ///         repository_path="/path/to/repository",
    ///         branch_glob_pattern="*",
    ///     )
    #[text_signature = "(url, repository_path, branch_glob_pattern, from_timestamp, /)"]
    fn scan_from_url(
        &self,
        py: Python,
        url: &str,
        repository_path: &str,
        branch_glob_pattern: Option<&str>,
        from_timestamp: Option<i64>,
    ) -> PyResult<Py<PyAny>> {
        let matches = Arc::new(Mutex::new(Vec::<HashMap<&str, String>>::with_capacity(10000)));

        if let Err(error) = Repository::clone(url, repository_path) {
            return Err(exceptions::PyRuntimeError::new_err(error.to_string()));
        };

        if let Err(error) = git_repository_scanner::scan_repository(
            repository_path,
            branch_glob_pattern.unwrap_or("*"),
            from_timestamp.unwrap_or(0),
            &self.rules_manager,
            matches.clone(),
        ) {
            Err(exceptions::PyRuntimeError::new_err(error.to_string()))
        } else {
            Ok(matches.lock().to_object(py))
        }
    }
}

/// PyRepScan is a Python library written in Rust. The library prodives an API to scan git repositories
/// for leaked secrects via usage of rules. There are multiple types of rules that can be used to find
/// leaked files and content.
#[pymodule]
fn pyrepscan(
    _py: Python,
    m: &PyModule,
) -> PyResult<()> {
    m.add_class::<GitRepositoryScanner>()?;
    m.add_class::<rules_manager::RulesManager>()?;

    Ok(())
}

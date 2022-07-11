use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use regex::Regex;
use std::collections::{HashMap, HashSet};

struct ContentRule {
    name: String,
    regex: Regex,
    whitelist_regexes: Vec<Regex>,
    blacklist_regexes: Vec<Regex>,
}

struct FilePathRule {
    name: String,
    regex: Regex,
}

#[pyclass]
#[derive(Default)]
pub struct RulesManager {
    file_extensions_to_skip: HashSet<String>,
    file_paths_to_skip: HashSet<String>,
    content_rules: Vec<ContentRule>,
    file_path_rules: Vec<FilePathRule>,
}

#[pymethods]
impl RulesManager {
    #[new]
    pub fn new() -> Self {
        RulesManager::default()
    }

    pub fn add_content_rule(
        &mut self,
        name: String,
        pattern: String,
        whitelist_patterns: Vec<String>,
        blacklist_patterns: Vec<String>,
    ) -> PyResult<()> {
        if name.is_empty() || pattern.is_empty() {
            return Err(
                PyRuntimeError::new_err("Rule name and pattern can not be empty")
            )
        }

        let regex = match Regex::new(&pattern) {
            Ok(regex) => regex,
            Err(error) => {
                return Err(
                    PyRuntimeError::new_err(
                        format!("Invalid regex pattern: {error}")
                    )
                )
            },
        };
        if regex.captures_len() != 2 {
            return Err(
                PyRuntimeError::new_err(
                    format!("Matching regex pattern must have exactly one capturing group: {pattern}")
                )
            );
        }

        let mut whitelist_regexes = Vec::new();
        for whitelist_pattern in whitelist_patterns.iter() {
            let whitelist_regex = match Regex::new(whitelist_pattern) {
                Ok(whitelist_regex) => whitelist_regex,
                Err(error) => {
                    return Err(
                        PyRuntimeError::new_err(
                            format!("Invalid whitelist regex pattern: {error}")
                        )
                    )
                },
            };
            if whitelist_regex.captures_len() != 1 {
                return Err(
                    PyRuntimeError::new_err(
                        format!("Whitelist regex pattern must not have a capturing group: {whitelist_pattern}")
                    )
                );
            }
            whitelist_regexes.push(whitelist_regex);
        }

        let mut blacklist_regexes = Vec::new();
        for blacklist_pattern in blacklist_patterns.iter() {
            let blacklist_regex = match Regex::new(blacklist_pattern) {
                Ok(blacklist_regex) => blacklist_regex,
                Err(error) => {
                    return Err(
                        PyRuntimeError::new_err(
                            format!("Invalid blacklist regex pattern: {error}")
                        )
                    )
                },
            };
            if blacklist_regex.captures_len() != 1 {
                return Err(
                    PyRuntimeError::new_err(
                        format!("Blacklist regex pattern must not have a capturing group: {blacklist_pattern}")
                    )
                );
            }
            blacklist_regexes.push(blacklist_regex);
        }

        let content_rule = ContentRule {
            name,
            regex,
            whitelist_regexes,
            blacklist_regexes,
        };
        self.content_rules.push(content_rule);

        Ok(())
    }

    pub fn add_file_path_rule(
        &mut self,
        name: String,
        pattern: String,
    ) -> PyResult<()> {
        if name.is_empty() || pattern.is_empty() {
            return Err(
                PyRuntimeError::new_err("Rule name and pattern can not be empty")
            )
        }

        let regex = match Regex::new(&pattern) {
            Ok(regex) => regex,
            Err(error) => {
                return Err(
                    PyRuntimeError::new_err(
                        format!("Invalid regex pattern: {error}")
                    )
                )
            }
        };

        let file_path_rule = FilePathRule { name, regex };
        self.file_path_rules.push(file_path_rule);

        Ok(())
    }

    pub fn add_file_extension_to_skip(
        &mut self,
        file_extension: String,
    ) -> PyResult<()> {
        if file_extension.is_empty() {
            return Err(
                PyRuntimeError::new_err("File extension can not be empty")
            )
        }
        self.file_extensions_to_skip.insert(file_extension.to_ascii_lowercase());

        Ok(())
    }

    pub fn add_file_path_to_skip(
        &mut self,
        file_path: String,
    ) -> PyResult<()> {
        if file_path.is_empty() {
            return Err(
                PyRuntimeError::new_err("File path can not be empty")
            )
        }
        self.file_paths_to_skip.insert(file_path.to_ascii_lowercase());

        Ok(())
    }

    pub fn should_scan_file_path(
        &self,
        file_path: &str,
    ) -> bool {
        if self.file_extensions_to_skip.iter().any(
            |file_extension_to_skip| {
                file_path.ends_with(file_extension_to_skip)
            }
        ) {
            return false;
        }

        if self.file_paths_to_skip.iter().any(
            |file_path_to_skip| {
                file_path.contains(file_path_to_skip)
            }
        ) {
            return false;
        }

        true
    }

    pub fn scan_file(
        &self,
        file_path: &str,
        content: Option<&str>,
    ) -> Option<Vec<HashMap<&str, String>>> {
        let mut scan_matches = Vec::new();

        for file_path_rule in self.file_path_rules.iter() {
            if file_path_rule.regex.is_match(file_path) {
                let mut scan_match = HashMap::<&str, String>::new();
                scan_match.insert("rule_name", file_path_rule.name.clone());
                scan_match.insert("match_text", file_path.to_string());
                scan_matches.push(scan_match);
            }
        }

        if let Some(content) = content {
            for content_rule in self.content_rules.iter() {
                for match_text in content_rule.regex.find_iter(content) {
                    if content_rule.blacklist_regexes.iter().any(
                        |blacklist_regex| blacklist_regex.is_match(match_text.as_str())
                    ) {
                        continue;
                    }
                    if !content_rule.whitelist_regexes.is_empty() && !content_rule.whitelist_regexes.iter().any(
                        |whitelist_regex| whitelist_regex.is_match(match_text.as_str())
                    ) {
                        continue;
                    }

                    let mut scan_match = HashMap::<&str, String>::new();
                    scan_match.insert("rule_name", content_rule.name.clone());
                    scan_match.insert("match_text", match_text.as_str().to_string());
                    scan_matches.push(scan_match);
                }
            }
        }

        if scan_matches.is_empty() {
            None
        } else {
            Some(scan_matches)
        }
    }

    pub fn check_pattern(
        &mut self,
        content: String,
        pattern: String
    ) -> PyResult<Vec<String>> {
        let regex = match Regex::new(&pattern) {
            Ok(regex) => regex,
            Err(error) => {
                return Err(
                    PyRuntimeError::new_err(
                        format!("Invalid regex pattern: {error}")
                    )
                )
            },
        };
        if regex.captures_len() != 2 {
            return Err(
                PyRuntimeError::new_err(
                    format!("Matching regex pattern must have exactly one capturing group: {pattern}")
                )
            );
        }

        let mut matches = Vec::new();
        for matched in regex.find_iter(&content) {
            matches.push(matched.as_str().to_string());
        }

        Ok(matches)
    }
}

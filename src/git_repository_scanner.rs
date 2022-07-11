use crate::rules_manager;

use chrono::prelude::*;
use crossbeam_utils::atomic::AtomicCell;
use crossbeam_utils::thread as crossbeam_thread;
use crossbeam::queue::ArrayQueue;
use git2::{Oid, Repository, Delta};
use parking_lot::Mutex;
use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use std::collections::HashMap;
use std::path::Path;
use std::sync::Arc;
use std::thread;
use std::time;

fn scan_commit_oid(
    should_stop: &AtomicCell<bool>,
    git_repo: &Repository,
    oid: &Oid,
    rules_manager: &rules_manager::RulesManager,
    output_matches: Arc<Mutex<Vec<HashMap<&str, String>>>>,
) -> Result<(), git2::Error> {
    let commit = git_repo.find_commit(*oid)?;

    let commit_parent_count = commit.parent_count();
    if commit_parent_count > 1 {
        return Ok(());
    }

    let commit_tree = commit.tree()?;

    let commit_diff = if commit_parent_count == 0 {
        git_repo.diff_tree_to_tree(None, Some(&commit_tree), None)?
    } else {
        let parent_commit = commit.parent(0)?;
        let parent_commit_tree = parent_commit.tree()?;

        git_repo.diff_tree_to_tree(Some(&parent_commit_tree), Some(&commit_tree), None)?
    };

    for delta in commit_diff.deltas() {
        if should_stop.load() {
            break;
        }

        match delta.status() {
            Delta::Added | Delta::Modified => {},
            _ => continue,
        }

        let new_file = delta.new_file();

        let delta_new_file_path = match new_file.path() {
            Some(path) => path.to_string_lossy().to_string(),
            None => continue,
        };
        if !rules_manager.should_scan_file_path(&delta_new_file_path.to_ascii_lowercase()) {
            continue;
        }

        let delta_new_file_blob = match git_repo.find_blob(new_file.id()) {
            Ok(blob) => blob,
            Err(_) => continue,
        };

        if delta_new_file_blob.size() < 2 {
            continue;
        }

        let delta_new_file_content = if delta_new_file_blob.is_binary() || delta_new_file_blob.size() > 5000000 {
            None
        } else {
            match std::str::from_utf8(delta_new_file_blob.content()) {
                Ok(content) => Some(content),
                Err(_) => None,
            }
        };

        let scan_matches = rules_manager.scan_file(&delta_new_file_path, delta_new_file_content);
        if let Some(scan_matches) = scan_matches {
            for scan_match in scan_matches.iter() {
                let mut match_hashmap = HashMap::with_capacity(9);
                match_hashmap.insert(
                    "commit_id",
                    commit.id().to_string(),
                );
                match_hashmap.insert(
                    "commit_message",
                    commit.message().unwrap_or("").to_string(),
                );
                match_hashmap.insert(
                    "commit_time",
                    Utc.timestamp(commit.time().seconds(), 0).format("%Y-%m-%dT%H:%M:%S").to_string(),
                );
                match_hashmap.insert(
                    "author_name",
                    commit.author().name().unwrap_or("").to_string(),
                );
                match_hashmap.insert(
                    "author_email",
                    commit.author().email().unwrap_or("").to_string(),
                );
                match_hashmap.insert(
                    "file_path",
                    new_file.path().unwrap_or_else(|| Path::new("")).to_string_lossy().to_string(),
                );
                match_hashmap.insert(
                    "file_oid",
                    new_file.id().to_string(),
                );
                match_hashmap.insert(
                    "rule_name",
                    scan_match.get("rule_name").unwrap_or(&String::from("")).to_string(),
                );
                match_hashmap.insert(
                    "match_text",
                    scan_match.get("match_text").unwrap_or(&String::from("")).to_string(),
                );
                output_matches.lock().push(match_hashmap);
            }
        }
    }

    Ok(())
}

fn get_commit_oids(
    repository_path: &str,
    branch_glob_pattern: &str,
    from_timestamp: i64,
) -> Result<Vec<Oid>, git2::Error>{
    let git_repo = Repository::open(repository_path)?;

    let mut revwalk = git_repo.revwalk()?;
    revwalk.push_head()?;
    revwalk.set_sorting(git2::Sort::TIME)?;
    revwalk.push_glob(branch_glob_pattern)?;

    let mut oids = Vec::new();
    for oid in revwalk.flatten() {
        if let Ok(commit) = git_repo.find_commit(oid) {
            if commit.time().seconds() >= from_timestamp {
                oids.push(oid);
            }
        }
    }

    Ok(oids)
}

pub fn scan_repository(
    py: &Python,
    repository_path: &str,
    branch_glob_pattern: &str,
    from_timestamp: i64,
    rules_manager: &rules_manager::RulesManager,
    output_matches: Arc<Mutex<Vec<HashMap<&str, String>>>>,
) -> PyResult<()> {
    let commit_oids_queue;

    match get_commit_oids(
        repository_path,
        branch_glob_pattern,
        from_timestamp
    ) {
        Ok(commit_oids) => {
            if commit_oids.is_empty() {
               return Ok(());
            }

            commit_oids_queue = ArrayQueue::new(commit_oids.len());
            for commit_oid in commit_oids {
                commit_oids_queue.push(commit_oid).unwrap();
            }
        },
        Err(error) => {
            return Err(PyRuntimeError::new_err(error.to_string()))
        },
    }

    let mut py_signal_error: PyResult<()> = Ok(());

    let should_stop  = AtomicCell::new(false);
    let number_of_cores = std::thread::available_parallelism().unwrap().get();

    crossbeam_thread::scope(
        |scope| {
            for _ in 0..number_of_cores {
                scope.spawn(
                    |_| {
                        if let Ok(git_repo) = Repository::open(repository_path) {
                            while !should_stop.load() {
                                if let Some(commit_oid) = commit_oids_queue.pop() {
                                    scan_commit_oid(
                                        &should_stop,
                                        &git_repo,
                                        &commit_oid,
                                        rules_manager,
                                        output_matches.clone(),
                                    ).unwrap_or(());
                                } else {
                                    break;
                                }
                            }
                        };
                    }
                );
            }

            while !commit_oids_queue.is_empty() {
                py_signal_error = py.check_signals();
                if py_signal_error.is_err() {
                    should_stop.store(true);

                    break;
                }

                thread::sleep(time::Duration::from_millis(100));
            }
        }
    ).unwrap_or_default();

    py_signal_error?;

    Ok(())
}

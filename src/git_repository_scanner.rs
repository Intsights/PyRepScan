use crate::rules_manager;

use chrono::prelude::*;
use crossbeam_utils::thread as crossbeam_thread;
use crossbeam::queue::SegQueue;
use git2::{Oid, Repository, Delta};
use parking_lot::Mutex;
use pyo3::prelude::*;
use std::collections::HashMap;
use std::path::Path;
use std::sync::Arc;
use std::sync::atomic::{AtomicBool, Ordering};
use std::thread;
use std::time;

fn scan_commit_oid(
    should_stop: &AtomicBool,
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
        if should_stop.load(Ordering::Relaxed) {
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
                let commit_date = Utc.timestamp(commit.time().seconds(), 0);
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
                    commit_date.format("%Y-%m-%dT%H:%M:%S").to_string(),
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

pub fn get_file_content(
    repository_path: &str,
    file_oid: &str,
) -> Result<Vec<u8>, git2::Error> {
    let git_repo = Repository::open(repository_path)?;
    let oid = Oid::from_str(file_oid)?;
    let blob = git_repo.find_blob(oid)?;

    Ok(blob.content().to_vec())
}

fn get_oids(
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
    for oid in revwalk {
        if let Ok(oid) = oid {
            if let Ok(commit) = git_repo.find_commit(oid) {
                if commit.time().seconds() >= from_timestamp {
                    oids.push(oid);
                }
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
) -> Result<(), PyErr> {
    let oids_queue = Arc::new(SegQueue::new());
    match get_oids(
        repository_path,
        branch_glob_pattern,
        from_timestamp
    ) {
        Ok(oids) => {
            for oid in oids {
                oids_queue.push(oid);
            }
        },
        Err(error) => {
            return Err(pyo3::exceptions::PyRuntimeError::new_err(error.to_string()))
        },
    }
    py.check_signals()?;

    let mut py_signal_error: PyResult<()> = Ok(());

    crossbeam_thread::scope(
        |scope| {
            let should_stop  = Arc::new(AtomicBool::new(false));

            for _ in 0..num_cpus::get() {
                let output_matches = output_matches.clone();
                let oids_queue = oids_queue.clone();
                let should_stop = should_stop.clone();
                scope.spawn(
                    move |_| {
                        if let Ok(git_repo) = Repository::open(repository_path) {
                            while !should_stop.load(Ordering::Relaxed) {
                                if let Some(oid) = oids_queue.pop() {
                                    scan_commit_oid(
                                        &should_stop,
                                        &git_repo,
                                        &oid,
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

            while !oids_queue.is_empty() {
                py_signal_error = py.check_signals();
                if py_signal_error.is_err() {
                    should_stop.store(true, Ordering::Relaxed);

                    break;
                }

                thread::sleep(time::Duration::from_millis(100));
            }
        }
    ).unwrap_or(());

    py_signal_error?;

    Ok(())
}

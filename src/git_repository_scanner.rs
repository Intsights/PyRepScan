use crate::rules_manager;

use chrono::prelude::*;
use git2::{Oid, Repository, Delta};
use git2::Error;
use parking_lot::Mutex;
use rayon::prelude::*;
use std::collections::HashMap;
use std::path::Path;
use std::sync::Arc;

fn scan_commit_oid(
    git_repo: &Repository,
    oid: &Oid,
    rules_manager: &rules_manager::RulesManager,
    output_matches: Arc<Mutex<Vec<HashMap<&str, String>>>>,
) -> Result<(), Error> {
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
) -> Result<Vec<u8>, Error> {
    let git_repo = Repository::open(repository_path)?;
    let oid = Oid::from_str(file_oid)?;
    let blob = git_repo.find_blob(oid)?;

    Ok(blob.content().to_vec())
}

pub fn scan_repository(
    repository_path: &str,
    branch_glob_pattern: &str,
    from_timestamp: i64,
    rules_manager: &rules_manager::RulesManager,
    output_matches: Arc<Mutex<Vec<HashMap<&str, String>>>>,
) -> Result<(), Error> {
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

    let chunk_size = (oids.len() as f64 / (num_cpus::get() * 5) as f64).ceil() as usize;
    if !oids.is_empty() {
        oids.par_chunks(chunk_size).for_each(
            |oids| {
                let git_repo = Repository::open(repository_path).unwrap();
                for oid in oids {
                    scan_commit_oid(
                        &git_repo,
                        oid,
                        rules_manager,
                        output_matches.clone()
                    ).unwrap_or(());
                }
            },
        );
    }

    Ok(())
}

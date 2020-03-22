#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <vector>
#include <map>
#include <mutex>
#include <iomanip>
#include <ctime>
#include <sstream>

#include <git2.h>
#include <taskflow/taskflow.hpp>

#include "rules_manager.hpp"


class GitRepositoryScanner {
    public:
    GitRepositoryScanner() {
        git_libgit2_init();
    }

    ~GitRepositoryScanner() {
        git_libgit2_shutdown();
    }

    void add_rule(
        std::string name,
        std::string match_pattern,
        std::vector<std::string> match_whitelist_patterns,
        std::vector<std::string> match_blacklist_patterns
    ) {
        this->rules_manager.add_rule(name, match_pattern, match_whitelist_patterns, match_blacklist_patterns);
    }

    void compile_rules() {
        this->rules_manager.compile_rules();
    }

    void add_ignored_file_extension(
        std::string file_extension
    ) {
        this->rules_manager.add_ignored_file_extension(file_extension);
    }

    void add_ignored_file_path(
        std::string file_path
    ) {
        this->rules_manager.add_ignored_file_path(file_path);
    }

    std::vector<std::map<std::string, std::string>> scan(
        std::string repository_path,
        std::string branch_glob_pattern
    ) {
        git_repository * git_repo = nullptr;
        git_revwalk * repo_revwalk = nullptr;
        git_oid oid;
        std::vector<git_oid> oids;
        std::vector<std::map<std::string, std::string>> results;
        std::mutex results_mutex;

        if (0 != git_repository_open(&git_repo, repository_path.c_str())) {
            throw std::runtime_error("could not open repository");
        }

        git_revwalk_new(&repo_revwalk, git_repo);
        git_revwalk_sorting(repo_revwalk, GIT_SORT_TIME);
        git_revwalk_push_glob(repo_revwalk, branch_glob_pattern.c_str());

        while (git_revwalk_next(&oid, repo_revwalk) == 0) {
            oids.push_back(oid);
        }

        git_revwalk_free(repo_revwalk);

        tf::Taskflow taskflow;
        tf::Executor executor;
        taskflow.parallel_for(
            oids.begin(),
            oids.end(),
            [&] (git_oid &oid) {
                git_commit * parent_commit = nullptr;
                git_commit * current_commit = nullptr;
                git_tree * current_git_tree = nullptr;
                git_tree * parent_git_tree = nullptr;
                git_diff * diff = nullptr;

                git_commit_lookup(&current_commit, git_repo, &oid);

                std::uint32_t current_commit_parent_count = git_commit_parentcount(current_commit);
                if (current_commit_parent_count > 1) {
                    git_commit_free(current_commit);
                    return;
                }

                const git_oid * current_commit_id = git_commit_id(current_commit);
                char current_commit_id_string[41] = {0};
                git_oid_fmt(current_commit_id_string, current_commit_id);

                const git_signature * current_commit_author = git_commit_author(current_commit);
                const char * current_commit_message = git_commit_message(current_commit);

                git_time_t commit_time = git_commit_time(current_commit);

                if (current_commit_parent_count == 1) {
                    git_commit_parent(&parent_commit, current_commit, 0);
                    git_commit_tree(&current_git_tree, current_commit);
                    git_commit_tree(&parent_git_tree, parent_commit);

                    git_diff_tree_to_tree(&diff, git_repo, parent_git_tree, current_git_tree, NULL);

                    git_commit_free(current_commit);
                    git_commit_free(parent_commit);
                    git_tree_free(current_git_tree);
                    git_tree_free(parent_git_tree);
                } else if (current_commit_parent_count == 0) {
                    git_commit_tree(&current_git_tree, current_commit);

                    git_diff_tree_to_tree(&diff, git_repo, NULL, current_git_tree, NULL);

                    git_commit_free(current_commit);
                    git_tree_free(current_git_tree);
                }

                std::size_t num_of_deltas = git_diff_num_deltas(diff);
                for (std::size_t i = 0; i < num_of_deltas; i++) {
                    const git_diff_delta * delta = git_diff_get_delta(diff, i);
                    git_blob * blob;

                    if (!this->rules_manager.should_scan_file_path(std::string(delta->new_file.path))) {
                        continue;
                    }

                    if(0 == git_blob_lookup(&blob, git_repo, &delta->new_file.id)) {
                        if (1 == git_blob_is_binary(blob)) {
                            git_blob_free(blob);
                            continue;
                        }

                        std::string content = (const char *)git_blob_rawcontent(blob);
                        auto matches = this->rules_manager.scan_content(content);
                        if (matches.has_value()) {
                            for (auto & match : matches.value()) {
                                char new_file_oid[41] = {0};
                                git_oid_fmt(new_file_oid, &delta->new_file.id);

                                results_mutex.lock();

                                std::tm * commit_time_tm = std::gmtime(&commit_time);
                                std::ostringstream commit_time_ss;
                                commit_time_ss << std::put_time(commit_time_tm, "%FT%T");

                                results.push_back(
                                    {
                                        {"commit_id", std::string(current_commit_id_string)},
                                        {"commit_message", std::string(current_commit_message)},
                                        {"commit_time", commit_time_ss.str()},
                                        {"author_name", std::string(current_commit_author->name)},
                                        {"author_email", std::string(current_commit_author->email)},
                                        {"file_path", std::string(delta->new_file.path)},
                                        {"file_oid", std::string(new_file_oid)},
                                        {"rule_name", match["rule_name"]},
                                        {"match", match["match"]},
                                    }
                                );

                                results_mutex.unlock();
                            }
                        }
                        git_blob_free(blob);
                    }
                }

                git_diff_free(diff);
            }
        );
        executor.run(taskflow);
        executor.wait_for_all();

        git_repository_free(git_repo);

        return results;
    }

    pybind11::bytes get_file_content(
        const std::string & repository_path,
        const std::string & file_oid
    ) {
        git_repository * git_repo = nullptr;
        git_blob * blob = nullptr;
        git_oid oid;

        if(0 != git_repository_open(&git_repo, repository_path.c_str())) {
            throw std::runtime_error("could not open repository");
        }

        if (0 != git_oid_fromstr(&oid, file_oid.c_str())) {
            git_repository_free(git_repo);
            throw std::runtime_error("could not find the commit id");
        }

        if(0 != git_blob_lookup(&blob, git_repo, &oid)) {
            git_repository_free(git_repo);
            throw std::runtime_error("could not find the file oid blob");
        }

        pybind11::bytes content = (const char *)git_blob_rawcontent(blob);

        git_blob_free(blob);
        git_repository_free(git_repo);

        return content;
    }

    private:
    RulesManager rules_manager;
};


PYBIND11_MODULE(pyrepscan, m) {
    pybind11::class_<RulesManager>(m, "RulesManager")
        .def(
            pybind11::init<>(),
            ""
        )
        .def(
            "add_rule",
            &RulesManager::add_rule,
            "",
            pybind11::arg("name"),
            pybind11::arg("match_pattern"),
            pybind11::arg("match_whitelist_patterns"),
            pybind11::arg("match_blacklist_patterns")
        )
        .def(
            "compile_rules",
            &RulesManager::compile_rules,
            ""
        )
        .def(
            "add_ignored_file_extension",
            &RulesManager::add_ignored_file_extension,
            "",
            pybind11::arg("file_extension")
        )
        .def(
            "add_ignored_file_path",
            &RulesManager::add_ignored_file_path,
            "",
            pybind11::arg("file_path")
        )
        .def(
            "should_scan_file_path",
            &RulesManager::should_scan_file_path,
            "",
            pybind11::arg("file_path")
        )
        .def(
            "scan_content",
            &RulesManager::scan_content,
            "",
            pybind11::arg("content")
        )
        .def(
            "check_pattern",
            &RulesManager::check_pattern,
            "",
            pybind11::arg("content"),
            pybind11::arg("pattern")
        );

    pybind11::class_<GitRepositoryScanner>(m, "GitRepositoryScanner")
        .def(
            pybind11::init<>(),
            ""
        )
        .def(
            "scan",
            &GitRepositoryScanner::scan,
            "",
            pybind11::arg("repository_path"),
            pybind11::arg("branch_glob_pattern")
        )
        .def(
            "compile_rules",
            &GitRepositoryScanner::compile_rules,
            ""
        )
        .def(
            "add_rule",
            &GitRepositoryScanner::add_rule,
            "",
            pybind11::arg("name"),
            pybind11::arg("match_pattern"),
            pybind11::arg("match_whitelist_patterns"),
            pybind11::arg("match_blacklist_patterns")
        )
        .def(
            "add_ignored_file_extension",
            &GitRepositoryScanner::add_ignored_file_extension,
            "",
            pybind11::arg("file_extension")
        )
        .def(
            "add_ignored_file_path",
            &GitRepositoryScanner::add_ignored_file_path,
            "",
            pybind11::arg("file_path")
        )
        .def(
            "get_file_content",
            &GitRepositoryScanner::get_file_content,
            "",
            pybind11::arg("repository_path"),
            pybind11::arg("file_oid")
        );
}

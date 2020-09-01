#include <vector>
#include <map>
#include <unordered_set>
#include <optional>
#include <algorithm>

#include <re2/re2.h>
#include <re2/set.h>


struct ContentRule {
    std::string name;
    std::shared_ptr<re2::RE2> regex;
    std::vector<std::shared_ptr<re2::RE2>> whitelist_regexes;
    std::vector<std::shared_ptr<re2::RE2>> blacklist_regexes;

    ContentRule(
        std::string name,
        std::string regex_pattern,
        std::vector<std::string> whitelist_regex_patterns,
        std::vector<std::string> blacklist_regex_patterns
    ) {
        this->name = name;

        auto regex = std::make_shared<re2::RE2>(regex_pattern, re2::RE2::Quiet);
        if (!regex->ok()) {
            throw std::runtime_error("Invalid regex pattern: " + regex_pattern + "\nError: " + regex->error());
        }
        if (regex->NumberOfCapturingGroups() != 1) {
            throw std::runtime_error("Matching regex pattern must have exactly one capturing group: " + regex_pattern);
        }
        this->regex = regex;

        for (const auto & whitelist_pattern : whitelist_regex_patterns) {
            auto whitelist_regex = std::make_shared<re2::RE2>(whitelist_pattern, re2::RE2::Quiet);
            if (!whitelist_regex->ok()) {
                throw std::runtime_error("Invalid whitelist regex pattern: " + whitelist_pattern + "\nError: " + whitelist_regex->error());
            }
            if (whitelist_regex->NumberOfCapturingGroups() != 0) {
                throw std::runtime_error("Whitelist regex pattern must not have a capturing group: " + whitelist_pattern + "");
            }

            this->whitelist_regexes.push_back(whitelist_regex);
        }

        for (const auto & blacklist_pattern : blacklist_regex_patterns) {
            auto blacklist_regex = std::make_shared<re2::RE2>(blacklist_pattern, re2::RE2::Quiet);
            if (!blacklist_regex->ok()) {
                throw std::runtime_error("Invalid blacklist regex pattern: " + blacklist_pattern + "\nError: " + blacklist_regex->error());
            }
            if (blacklist_regex->NumberOfCapturingGroups() != 0) {
                throw std::runtime_error("Blacklist regex pattern must not have a capturing group: " + blacklist_pattern + "");
            }

            this->blacklist_regexes.push_back(blacklist_regex);
        }
    }
};


struct FileNameRule {
    std::string name;
    std::shared_ptr<re2::RE2> regex;

    FileNameRule(
        std::string name,
        std::string regex_pattern
    ) {
        this->name = name;

        auto regex = std::make_shared<re2::RE2>(regex_pattern, re2::RE2::Quiet);
        if (!regex->ok()) {
            throw std::runtime_error("Invalid regex pattern:\n\t" + regex_pattern + "\nError: " + regex->error());
        }
        this->regex = regex;
    }
};


class RulesManager {
    public:
    RulesManager() {}

    ~RulesManager() {}

    void add_content_rule(
        ContentRule rule
    ) {
        this->content_rules.push_back(rule);
    }

    void add_file_name_rule(
        FileNameRule rule
    ) {
        this->file_name_rules.push_back(rule);
    }

    void add_ignored_file_extension(
        const std::string &file_extension
    ) {
        this->ignored_file_extensions.emplace(file_extension);
    }

    void add_ignored_file_path(
        const std::string &file_path
    ) {
        this->ignored_file_paths.emplace(file_path);
    }

    inline bool should_scan_file_path(
        const std::string &file_path
    ) {
        if(file_path.find_last_of('.') != std::string::npos) {
            std::string file_extension = file_path.substr(file_path.find_last_of('.') + 1);
            if (this->ignored_file_extensions.count(file_extension) > 0) {
                return false;
            }
        }

        for (const auto & ignored_file_path : this->ignored_file_paths) {
            if (file_path.find(ignored_file_path) != std::string::npos) {
                return false;
            }
        }

        return true;
    }

    inline std::optional<std::vector<std::map<std::string, std::string>>> scan_file_name(
        const std::string &file_name
    ) {
        std::vector<std::map<std::string, std::string>> matches;

        for (const auto &file_name_rule: this->file_name_rules) {
            if (re2::RE2::PartialMatch(file_name, *file_name_rule.regex)) {
                matches.push_back(
                    {
                        {"rule_name", file_name_rule.name},
                        {"match", file_name},
                    }
                );
            }
        }

        if (matches.size() == 0) {
            return std::nullopt;
        } else {
            return matches;
        }
    }

    inline std::optional<std::vector<std::map<std::string, std::string>>> scan_content(
        const std::string &content
    ) {
        std::vector<std::map<std::string, std::string>> matches;
        std::string match;

        for (const auto & content_rule : this->content_rules) {
            re2::StringPiece input(content);
            while (re2::RE2::FindAndConsume(&input, *content_rule.regex, &match)) {
                bool blacklist_matched = std::any_of(
                    content_rule.blacklist_regexes.begin(),
                    content_rule.blacklist_regexes.end(),
                    [&match] (std::shared_ptr<re2::RE2> blacklist_regex) {
                        return re2::RE2::PartialMatch(match, *blacklist_regex);
                    }
                );
                if (blacklist_matched) {
                    continue;
                }

                bool whitelist_not_matched = std::none_of(
                    content_rule.whitelist_regexes.begin(),
                    content_rule.whitelist_regexes.end(),
                    [&match] (std::shared_ptr<re2::RE2> whitelist_regex) {
                        return re2::RE2::PartialMatch(match, *whitelist_regex);
                    }
                );
                if (!content_rule.whitelist_regexes.empty() && whitelist_not_matched) {
                    continue;
                }

                matches.push_back(
                    {
                        {"rule_name", content_rule.name},
                        {"match", match},
                    }
                );
            }
        }

        if (matches.size() == 0) {
            return std::nullopt;
        } else {
            return matches;
        }
    }

    inline std::vector<std::string> check_pattern(
        const std::string &content,
        const std::string &pattern
    ) {
        re2::RE2 regex(pattern, re2::RE2::Quiet);
        if (!regex.ok()) {
            throw std::runtime_error("Invalid regex pattern: " + pattern + "\nError: " + regex.error());
        }
        if (regex.NumberOfCapturingGroups() != 1) {
            throw std::runtime_error("Matching regex pattern must have exactly one capturing group: " + pattern);
        }

        std::vector<std::string> matches;
        re2::StringPiece input(content);
        std::string match;
        while (re2::RE2::FindAndConsume(&input, regex, &match)) {
            matches.push_back(match);
        }

        return matches;
    }

    private:
    std::unordered_set<std::string> ignored_file_extensions;
    std::unordered_set<std::string> ignored_file_paths;
    std::vector<ContentRule> content_rules;
    std::vector<FileNameRule> file_name_rules;
};

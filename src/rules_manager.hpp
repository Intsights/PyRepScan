#include <vector>
#include <map>
#include <unordered_set>
#include <optional>

#include <re2/re2.h>
#include <re2/set.h>


class RulesManager {
    public:
    RulesManager() {}

    ~RulesManager() {}

    void add_rule(
        std::string name,
        std::string regex_pattern,
        std::vector<std::string> regex_blacklist_patterns
    ) {
        re2::RE2 matching_regex(regex_pattern, re2::RE2::Quiet);
        if (!matching_regex.ok()) {
            throw std::runtime_error("Invalid matching regex pattern: \"" + regex_pattern + "\"");
        }
        if (matching_regex.NumberOfCapturingGroups() != 1) {
            throw std::runtime_error("Matching regex pattern must have exactly one capturing group: \"" + regex_pattern + "\"");
        }

        for (const auto & blacklist_pattern : regex_blacklist_patterns) {
            re2::RE2 blacklist_regex(blacklist_pattern, re2::RE2::Quiet);
            if (!blacklist_regex.ok()) {
                throw std::runtime_error("Invalid blacklist regex pattern: \"" + blacklist_pattern + "\"");
            }
            if (blacklist_regex.NumberOfCapturingGroups() != 0) {
                throw std::runtime_error("Blacklist regex pattern must not have a capturing group: \"" + blacklist_pattern + "\"");
            }
        }


        std::shared_ptr<re2::RE2::Set> blacklist_pattern_set = std::make_shared<re2::RE2::Set>(
            re2::RE2::Quiet,
            re2::RE2::UNANCHORED
        );
        for (const auto & blacklist_pattern : regex_blacklist_patterns) {
            blacklist_pattern_set->Add(blacklist_pattern, NULL);
        }
        blacklist_pattern_set->Compile();
        this->rules_blacklists.push_back(blacklist_pattern_set);

        this->pattern_set.Add(regex_pattern, NULL);
        this->patterns.push_back(std::make_shared<re2::RE2>(regex_pattern));
        this->rules.push_back(
            {
                {"name", name},
                {"regex_pattern", regex_pattern},
            }
        );
    }

    void compile_rules() {
        this->pattern_set.Compile();
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

    inline std::optional<std::vector<std::map<std::string, std::string>>> scan_content(
        const std::string &content
    ) {
        std::vector<std::int32_t> matched_regexes;

        if (this->pattern_set.Match(content, &matched_regexes)) {
            std::vector<std::map<std::string, std::string>> matches;
            re2::StringPiece input(content);
            std::string match;

            for (const auto & match_index : matched_regexes) {
                while (re2::RE2::FindAndConsume(&input, *this->patterns[match_index], &match)) {
                    if (this->rules_blacklists[match_index]->Match(match, NULL)) {
                        continue;
                    }

                    matches.push_back(
                        {
                            {"rule_name", this->rules[match_index]["name"]},
                            {"match", match},
                        }
                    );
                }
            }

            return matches;
        }

        return std::nullopt;
    }

    private:
    std::unordered_set<std::string> ignored_file_extensions;
    std::unordered_set<std::string> ignored_file_paths;
    std::vector<std::map<std::string, std::string>> rules;
    std::vector<std::shared_ptr<re2::RE2::Set>> rules_blacklists;
    std::vector<std::shared_ptr<re2::RE2>> patterns;
    re2::RE2::Set pattern_set = re2::RE2::Set(
        re2::RE2::Quiet,
        re2::RE2::UNANCHORED
    );
};

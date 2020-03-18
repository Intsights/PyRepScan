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
        std::string match_pattern,
        std::vector<std::string> match_whitelist_patterns,
        std::vector<std::string> match_blacklist_patterns
    ) {
        re2::RE2 matching_regex(match_pattern, re2::RE2::Quiet);
        if (!matching_regex.ok()) {
            throw std::runtime_error("Invalid matching regex pattern: \"" + match_pattern + "\"");
        }
        if (matching_regex.NumberOfCapturingGroups() != 1) {
            throw std::runtime_error("Matching regex pattern must have exactly one capturing group: \"" + match_pattern + "\"");
        }

        for (const auto & match_whitelist_pattern : match_whitelist_patterns) {
            re2::RE2 match_whitelist_regex(match_whitelist_pattern, re2::RE2::Quiet);
            if (!match_whitelist_regex.ok()) {
                throw std::runtime_error("Invalid match validator regex pattern: \"" + match_whitelist_pattern + "\"");
            }
            if (match_whitelist_regex.NumberOfCapturingGroups() != 0) {
                throw std::runtime_error("Match validator regex pattern must not have a capturing group: \"" + match_whitelist_pattern + "\"");
            }
        }

        for (const auto & match_blacklist_pattern : match_blacklist_patterns) {
            re2::RE2 match_blacklist_regex(match_blacklist_pattern, re2::RE2::Quiet);
            if (!match_blacklist_regex.ok()) {
                throw std::runtime_error("Invalid blacklist regex pattern: \"" + match_blacklist_pattern + "\"");
            }
            if (match_blacklist_regex.NumberOfCapturingGroups() != 0) {
                throw std::runtime_error("Blacklist regex pattern must not have a capturing group: \"" + match_blacklist_pattern + "\"");
            }
        }

        std::shared_ptr<re2::RE2::Set> match_blacklist_pattern_set = std::make_shared<re2::RE2::Set>(
            re2::RE2::Quiet,
            re2::RE2::UNANCHORED
        );
        for (const auto & match_blacklist_pattern : match_blacklist_patterns) {
            match_blacklist_pattern_set->Add(match_blacklist_pattern, NULL);
        }
        match_blacklist_pattern_set->Compile();
        this->match_blacklist_pattern_set.push_back(match_blacklist_pattern_set);

        if (match_whitelist_patterns.size() == 0) {
            this->match_whitelist_pattern_set.push_back(nullptr);
        } else {
            std::shared_ptr<re2::RE2::Set> match_whitelists_pattern_set = std::make_shared<re2::RE2::Set>(
                re2::RE2::Quiet,
                re2::RE2::UNANCHORED
            );
            for (const auto & match_whitelist_pattern : match_whitelist_patterns) {
                match_whitelists_pattern_set->Add(match_whitelist_pattern, NULL);
            }
            match_whitelists_pattern_set->Compile();
            this->match_whitelist_pattern_set.push_back(match_whitelists_pattern_set);
        }

        this->match_pattern_set.Add(match_pattern, NULL);
        this->match_patterns.push_back(std::make_shared<re2::RE2>(match_pattern));
        this->rule_names.push_back(name);
    }

    void compile_rules() {
        this->match_pattern_set.Compile();
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

        if (this->match_pattern_set.Match(content, &matched_regexes)) {
            std::vector<std::map<std::string, std::string>> matches;
            re2::StringPiece input(content);
            std::string match;

            for (const auto & match_index : matched_regexes) {
                while (re2::RE2::FindAndConsume(&input, *this->match_patterns[match_index], &match)) {
                    if (this->match_blacklist_pattern_set[match_index]->Match(match, NULL)) {
                        continue;
                    }

                    if (
                        this->match_whitelist_pattern_set[match_index] != nullptr &&
                        !this->match_whitelist_pattern_set[match_index]->Match(match, NULL)
                    ) {
                        continue;
                    }

                    matches.push_back(
                        {
                            {"rule_name", this->rule_names[match_index]},
                            {"match", match},
                        }
                    );
                }
            }

            return matches;
        }

        return std::nullopt;
    }

    inline std::vector<std::string> check_pattern(
        const std::string &content,
        const std::string &pattern
    ) {
        re2::RE2 matching_regex(pattern, re2::RE2::Quiet);
        if (!matching_regex.ok()) {
            throw std::runtime_error("Invalid matching regex pattern: \"" + pattern + "\"");
        }
        if (matching_regex.NumberOfCapturingGroups() != 1) {
            throw std::runtime_error("Matching regex pattern must have exactly one capturing group: \"" + pattern + "\"");
        }

        std::vector<std::string> matches;
        re2::StringPiece input(content);
        std::string match;
        while (re2::RE2::FindAndConsume(&input, matching_regex, &match)) {
            matches.push_back(match);
        }

        return matches;
    }

    private:
    std::unordered_set<std::string> ignored_file_extensions;
    std::unordered_set<std::string> ignored_file_paths;
    std::vector<std::string> rule_names;
    std::vector<std::shared_ptr<re2::RE2::Set>> match_whitelist_pattern_set;
    std::vector<std::shared_ptr<re2::RE2::Set>> match_blacklist_pattern_set;
    std::vector<std::shared_ptr<re2::RE2>> match_patterns;
    re2::RE2::Set match_pattern_set = re2::RE2::Set(
        re2::RE2::Quiet,
        re2::RE2::UNANCHORED
    );
};

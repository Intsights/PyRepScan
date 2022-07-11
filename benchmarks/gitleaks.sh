docker pull zricethezav/gitleaks:latest
docker run -v ${FOLDER_TO_SCAN}:/path -v ${PWD}/benchmarks/gitleaks.toml:/gitleaks.toml zricethezav/gitleaks:latest detect --source="/path" --config=/gitleaks.toml

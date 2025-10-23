#!/bin/bash

# prepare_release.sh - Script to prepare this repository for release

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "Error: Git is not installed. Please install git and try again."
    exit 1
fi

# Check required files exist
required_files=("README.md" "ollama_shim.py" "requirements.txt" "CHANGELOG.md")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "Error: Required file $file is missing."
        exit 1
    fi
done

# Check for uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    echo "Warning: There are uncommitted changes. Staging them now."
    git add .
else
    echo "No uncommitted changes found. Proceeding with release preparation."
fi

# Commit current state if not already committed
if ! git diff-index --quiet HEAD --; then
    commit_message="Prepare for v0.1.0 release"
    git commit -m "$commit_message" || {
        echo "Error: Failed to create commit."
        exit 1
    }
else
    echo "Already at a clean working directory. No new commit created."
fi

# Create the release tag
tag_name="v0.1.0"
git tag $tag_name || {
    echo "Error: Failed to create tag $tag_name"
    exit 1
}
echo "Successfully created tag $tag_name"

# Generate a summary of changes for the release notes
echo -e "\nRelease Notes for $tag_name:"
echo "---------------------------------"
git log --oneline -n 5 $(git rev-list --tags --max-count=1)..HEAD

chmod +x "$0" || {
    echo "Error: Failed to make script executable"
    exit 1
}
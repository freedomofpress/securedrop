# GitHub Helpers

This adds labels to the open PRs based on the location of files changed within the PR.

This will work for admins of SecureDrop that generate a [GitHub token](https://github.com/settings/tokens).

## Setup

### With Docker

    docker build -t github_helpers .

### Without Docker

Download and install `node` and `npm`, then

    npm install
    cp config.json.example config.json

Enter your GitHub token info into `config.json`.

## Running

### With Docker

Run:

    docker run -it -v $(pwd)/state_dir:/opt/state_dir -e GITHUB_TOKEN=$GITHUB_TOKEN github_helpers

replacing `$GITHUB_TOKEN` with your own GitHub token.

### Without Docker

    node index.js

#!/bin/bash

set -e

# If current branch is not master or doesnt start with release...
if [[ "$CIRCLE_BRANCH" != "master"  && "$CIRCLE_BRANCH" != release*  ]]; then
  # Fetch and rebase onto the latest in develop
  git fetch origin develop
  git rebase origin/develop
  # Print out the current head for debugging potential CI issues
  git rev-parse HEAD
fi

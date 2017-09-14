#!/bin/bash

set -e

# If current branch is not master or doesnt start with release...
if [[ "$CIRCLE_BRANCH" != "master"  && "$CIRCLE_BRANCH" != release*  ]]; then

  # Git will yell at you when trying to rebase without author/email configured
  git config --global user.email "ci@freedom.press"
  git config --global user.name "CI User"

  # Fetch and rebase onto the latest in develop
  git fetch origin develop
  git rebase origin/develop

  # Print out the current head for debugging potential CI issues
  git rev-parse HEAD
fi

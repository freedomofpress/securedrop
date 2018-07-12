#!/bin/bash
# shellcheck disable=SC2086
#
# To be utilized in CircleCI
# Determine target branch from PR number and rebase against that

set -e

GITHUB_PR_URL="https://api.github.com/repos/freedomofpress/securedrop/pulls/${CIRCLE_PULL_REQUEST##*/}"

# If current branch is not master or doesnt start with release...
if [[ "$CIRCLE_BRANCH" != "master"  && "$CIRCLE_BRANCH" != release*  ]]; then

  # Git will yell at you when trying to rebase without author/email configured
  git config --global user.email "ci@freedom.press"
  git config --global user.name "CI User"

  # Ensure presensce of upstream remote
  git ls-remote --exit-code --quiet upstream 2>/dev/null || git remote add upstream https://github.com/freedomofpress/securedrop.git

  # Determine target branch via API
  #
  # (We are togglin' between two upstream containers here - the constant is both have python3)
  target_branch="$(curl -s ${GITHUB_PR_URL} | python3 -c 'import sys, json; print(json.load(sys.stdin)["base"]["ref"])')"

  # Fetch and rebase onto the latest in develop
  git fetch upstream "${target_branch}"
  git rebase "upstream/${target_branch}"

  # Print out the current head for debugging potential CI issues
  git rev-parse HEAD
fi

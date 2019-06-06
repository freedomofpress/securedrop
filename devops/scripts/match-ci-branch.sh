#!/bin/bash

#
# Checks the given regular expression against the branch names
# involved in a Circle CI job.
#
# The branch names are collected from the CIRCLE_BRANCH environment
# variable and, for pull requests, from the GitHub API, as CircleCI
# sets CIRCLE_BRANCH to something useless like /pull/123.
#
# Returns:
#   0 unless there's an error
#   1 otherwise
#
# To avoid lots of "set +e; ...; set -e" in the CircleCI commands,
# we'll parse the output instead of looking at the return code.

JQ=$(which jq)
if [ -z "${JQ}" ]
then
    echo "Error: jq must be installed."
    exit 1
fi

BRANCH_RE=$1
if [ -z "${BRANCH_RE}" ]
then
    echo "Error: please specify a regular expression."
    exit 1
fi

CIRCLE_PR_BRANCH=""
if [ -n "${CIRCLE_PR_NUMBER}" ]
then
    GH_PULL_URL="https://api.github.com/repos/${CIRCLE_PROJECT_USERNAME}/${CIRCLE_PROJECT_REPONAME}/pulls/${CIRCLE_PR_NUMBER}"
    CIRCLE_PR_BRANCH=$(curl -s "${GH_PULL_URL}" | jq -r '.head.ref')
fi

if [[ "${CIRCLE_BRANCH}" =~ ${BRANCH_RE} ]]
then
    echo "found \"${BRANCH_RE}\" in CIRCLE_BRANCH \"${CIRCLE_BRANCH}\""
    exit 0
fi

if [[ "${CIRCLE_PR_BRANCH}" =~ ${BRANCH_RE} ]]
then
    echo "found \"${BRANCH_RE}\" in CIRCLE_PR_BRANCH \"${CIRCLE_PR_BRANCH}\""
    exit 0
fi

echo "did not find \"${BRANCH_RE}\" in CIRCLE_BRANCH \"${CIRCLE_BRANCH}\" or CIRCLE_PR_BRANCH \"${CIRCLE_PR_BRANCH}\""
exit 0

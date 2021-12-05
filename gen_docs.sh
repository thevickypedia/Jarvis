#!/usr/bin/env bash
# 'set -e' stops the execution of a script if a command or pipeline has an error.
# This is the opposite of the default shell behaviour, which is to ignore errors in scripts.
set -e

branch="$(git rev-parse --abbrev-ref HEAD)"
checker=$(git diff --name-only `git merge-base $branch HEAD`)
if [[ ! $checker =~ "version.py" ]]; then
  echo -e "\n********************************************************************ERROR********************************************************************"
  echo "Docs generation was ABORTED since module version was not bumped!! Changelog generator requires the commit number and package version in sync."
  echo -e "*********************************************************************************************************************************************\n"
  exit 255
fi

rm -rf docs
mkdir docs
[ ! -d "doc_generator/_static" ] && mkdir doc_generator/_static  # creates a _static folder if unavailable
cp README.md doc_generator && cd doc_generator && make clean html && mv _build/html/* ../docs && rm README.md
touch ../docs/.nojekyll

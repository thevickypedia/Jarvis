#!/usr/bin/env bash
# 'set -e' stops the execution of a script if a command or pipeline has an error.
# This is the opposite of the default shell behaviour, which is to ignore errors in scripts.
set -e

export pre_commit=1;
rm -rf docs  # Remove existing docs directory
mkdir docs  # Create new docs directory
mkdir -p docs_gen/_static  # Create a _static directory if unavailable
cp README.md docs_gen  # Copy readme file to docs_gen
cd docs_gen && make clean html  # cd into doc_gen and create the runbook
mv _build/html/* ../docs && mv README.md ../docs && rm -rf fileio logs  # Move the runbook, readme and cleanup
# The existence of this file tells GitHub Pages not to run the published files through Jekyll.
# This is important since Jekyll will discard any files that begin with _
touch ../docs/.nojekyll
cp static.css ../docs/_static

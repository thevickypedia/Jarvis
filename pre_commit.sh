#!/usr/bin/env bash
# 'set -e' stops the execution of a script if a command or pipeline has an error.
# This is the opposite of the default shell behaviour, which is to ignore errors in scripts.
set -e

export PROCESS_NAME="pre_commit"

clean_docs() {
  # Clean up docs directory keeping the CNAME file if present
  directory="docs"
  file_to_keep="CNAME"
  if [ -e "${directory}/${file_to_keep}" ]; then
    find "${directory}" ! -name "${file_to_keep}" -mindepth 1 -delete
  fi
}

update_release_notes() {
  # Update release notes
  gitverse-release reverse -f release_notes.rst -t 'Release Notes'
}

gen_docs() {
  # Generate sphinx docs
  mkdir -p docs_gen/_static  # Create a _static directory if unavailable
  cp README.md docs_gen  # Copy readme file to docs_gen
  cd docs_gen && make clean html  # cd into doc_gen and create the runbook
  mv _build/html/* ../docs && mv README.md ../docs && rm -rf logs  # Move the runbook, readme and cleanup
  cp static.css ../docs/_static
}

run_pytest() {
  # Run pytest
  python -m pytest
}

gen_docs &
clean_docs &
update_release_notes &
run_pytest &

wait

# The existence of this file tells GitHub Pages not to run the published files through Jekyll.
# This is important since Jekyll will discard any files that begin with _
touch docs/.nojekyll

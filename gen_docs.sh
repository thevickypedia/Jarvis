#!/usr/bin/env bash
# 'set -e' stops the execution of a script if a command or pipeline has an error.
# This is the opposite of the default shell behaviour, which is to ignore errors in scripts.
set -e

# shellcheck disable=SC2207
tuple=($(python -c "from jarvis import version, executors; print(version); print(executors.others.pypi_versions('jarvis-ironman')[-1])"))
#read -r current_pkg_version latest_pypi_version <<< "$tuple";
current_pkg_version="${tuple[0]}"
latest_pypi_version="${tuple[1]}"
bumped=$(python -c "from packaging.version import Version; print(1) if Version('$current_pkg_version') > Version('$latest_pypi_version') else print(0)")
if [[ "$bumped" == 0 ]]; then
  echo -e "\n********************************************************************ERROR********************************************************************"
  echo "Docs generation was ABORTED since module version was not bumped!! Changelog generator requires the commit number and package version in sync."
  echo -e "*********************************************************************************************************************************************\n"
  echo "Current pkg version: $current_pkg_version"
  echo "Latest pypi version: $latest_pypi_version"
  exit 255
fi

branch="$(git rev-parse --abbrev-ref HEAD)"
checker=$(git diff --name-only "$(git merge-base "$branch" HEAD)")
if [[ ! $checker =~ release_notes.rst ]]; then
  echo -e "\n********************************************************************ERROR**********************************************************"
  echo "Docs generation was ABORTED since release notes was not updated!! Changelog generator requires the release notes to be in sync."
  echo -e "***********************************************************************************************************************************\n"
  exit 255
fi

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

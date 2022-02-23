#!/bin/zsh

source $HOME/.zshrc

[[ -z "$PYPI_USER" || -z "$PYPI_TOKEN" ]] && echo "Set PYPI_USER and PYPI_TOKEN in ENV VARS" && exit 1;

python_script="
from version import version_info
print('.'.join(str(c) for c in version_info))
"

read_module_version() {
  local python_file=$1; shift
  local varname
  for varname; do
    IFS= read -r -d '' "${varname#*:}"
  done < <(python -c "$python_script" "$python_file" "${@%%:*}")
}

read_module_version version.py version_info:version  # Reads var $2 from file $1 and assigns it to the var version
statement="RUNNING THIS WILL BUILD v$version OF ${PWD##*/} IN PYPI AND MAY FAIL THE AUTOMATIC BUILD ON GITHUB ACTIONS"
echo -e "\n**********************************************************************************************************"
echo -e $statement
echo -e "**********************************************************************************************************\n"
read -p "Are you sure you want to continue? <Y/N> " prompt
if [[ $prompt =~ [yY](es)* ]]
then
  python -m pip install --upgrade pip
  pip install changelog-generator
  changelog reverse
  pip install setuptools wheel twine
  python setup.py bdist_wheel --universal
  python setup.py sdist
  twine upload -r pypi --repository-url https://upload.pypi.org/legacy/ dist/* -u $PYPI_USER -p $PYPI_TOKEN
  rm -rf build dist *.egg-info
else
    echo -e "\nBUILD PROCESS TERMINATED"
fi

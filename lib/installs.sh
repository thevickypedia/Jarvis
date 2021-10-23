# Looks for brew installation and installs only if brew is not found in /usr/local/bin
brew_check=$(which brew)
brew_condition="/usr/local/bin/brew"
if [[ "$brew_check" != "$brew_condition" ]]; then
  echo "Installing Homebrew"
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"
  else echo "Found Homebrew, skipping installation"
fi

# Looks for git and installs only if git is not found in /usr/bin or /usr/local/bin (if installed using brew)
git_check=$(which git)
git_condition_1="/usr/bin/git"
git_condition_2="/usr/local/bin/git"
if [[ "$git_check" == "$git_condition_1" || "$git_check" == "$git_condition_2" ]]; then
  echo "Found Git CLI, skipping installation"
  else echo "Installing Git CLI"
  brew install git
fi

# Packages installed using homebrew
brew install portaudio coreutils
git clone https://github.com/toy/blueutil.git && cd blueutil && make && make install && cd ../ && rm -rf blueutil

# Upgrades pip module
python3 -m pip install --upgrade pip

# Installs non version specicfic packages using --upgrade and --no-cache flag
python3 -m pip install --upgrade --no-cache gmail-connector changelog-generator sphinx pre-commit recommonmark

# Install pre-commit checker to restrict commit if any step in .pre-commit-config.yaml fails.
pre-commit install

# Get to the current directory and install the module specific packages from requiements.txt
current_dir="$(dirname "$(realpath "$0")")"
python3 -m pip install --no-cache-dir -r $current_dir/requirements.txt

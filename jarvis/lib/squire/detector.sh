# NOTE: `uname -m` is more accurate and universal than `arch`
# See https://en.wikipedia.org/wiki/Uname
unamem="$(uname -m)"
case $unamem in
*aarch64* | arm64)
  architecture="arm64"
  ;;
*64*)
  architecture="amd64"
  ;;
*86*)
  architecture="386"
  ;;
*armv5*)
  architecture="armv5"
  ;;
*armv6*)
  architecture="armv6"
  ;;
*armv7*)
  architecture="armv7"
  ;;
*)
  echo "***************************************************************************************************"
  echo "                                Unknown architecture: $unamem"
  echo "***************************************************************************************************"
  exit 1
  ;;
esac

unameu="$(tr '[:lower:]' '[:upper:]' <<<"$(uname)")"
if [[ $unameu == *DARWIN* ]]; then
  osname="darwin"
elif [[ $unameu == *LINUX* ]]; then
  osname="linux"
elif [[ $unameu == *FREEBSD* ]]; then
  osname="freebsd"
elif [[ $unameu == *NETBSD* ]]; then
  osname="netbsd"
elif [[ $unameu == *OPENBSD* ]]; then
  osname="openbsd"
elif [[ $unameu == *WIN* || $unameu == MSYS* ]]; then
  # Should catch cygwin
  osname="windows"
else
  echo "***************************************************************************************************"
  echo "                                     Unknown OS: $(uname)"
  echo "***************************************************************************************************"
  exit 1
fi

case "$osname" in
darwin | linux | windows)
  export osname=$osname
  ;;
*)
  echo "Unsupported Operating System"
  exit 1
  ;;
esac

if [[ $architecture == "amd64" ]]; then
  export architecture=$architecture
else
  echo "Unsupported architecture"
  exit 1
fi

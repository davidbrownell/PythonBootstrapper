#!/usr/bin/env bash
# ----------------------------------------------------------------------
# |
# |  Bootstrap.sh
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2023-12-13 16:10:48
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2023
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# |
# |  This script downloads and invokes BootstrapImpl.sh from the PythonBootstrapper
# |  repository (https://github.com/davidbrownell/PythonBootstrapper).
# |
# |  Arguments:
# |
# |      --debug                         Display additional debugging information.
# |
# |      --force                         Ensure that a new python environment is installed, even if it already exists.
# |
# |      --python-version <version>      Specify the python version to install; the default python version is installed if not specified.
# |
# ----------------------------------------------------------------------
set +v # Continue on errors

this_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
pushd "${this_dir}" > /dev/null || exit

# ----------------------------------------------------------------------
# |
# |  Download BootstrapImpl.sh
# |
# ----------------------------------------------------------------------
echo "Downloading Bootstrap code..."

temp_script_name=$(mktemp Bootstrap.XXXXXX)

curl --header "Cache-Control: no-cache, no-store" --header "Pragma: no-cache" --location https://raw.githubusercontent.com/davidbrownell/PythonBootstrapper/main/src/BootstrapImpl.sh --output BootstrapImpl.sh --no-progress-meter --fail-with-body > "${temp_script_name}" 2>&1
error=$?

if [[ ${error} != 0 ]]; then
    echo "[1ADownloading Bootstrap code...[31m[1mFAILED[0m."
    echo ""

    cat "${temp_script_name}"
    rm "${temp_script_name}"

    exit ${error}
fi

chmod u+x BootstrapImpl.sh
echo "[1ADownloading Bootstrap code...[32m[1mDONE[0m."

# ----------------------------------------------------------------------
# |
# |  Invoke BootstrapImpl.sh
# |
# ----------------------------------------------------------------------
./BootstrapImpl.sh "$@"
error=$?

# ----------------------------------------------------------------------
# |
# |  Exit
# |
# ----------------------------------------------------------------------
rm "BootstrapImpl.sh"
rm "${temp_script_name}"

exit ${error}

#!/usr/bin/env bash
# ----------------------------------------------------------------------
# |
# |  BootstrapImpl.sh
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2023-12-14 15:22:35
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2023-24
# |  Distributed under the MIT License.
# |
# ----------------------------------------------------------------------
set +e # Continue on errors

echo ""
echo "Script Version 0.12.1"
echo ""

# This script:
#     1) Ensure that PYTHON_VERSION is set
#     2) Ensure that PYTHON_VERSION is valid
#     3) Set global environment variables
#     4) Delete the micromamba environment (if requested)
#     5) Install micromamba (if necessary)
#     6) Initialize a new environment (if necessary)
#        a) Create the micromamba environment
#        b) Intialize the micromamba shell
#        c) Activate the environment
#        d) Install virtualenv
#        e) Deactivate the environment
#     7) Initialize the micromamba shell
#     8) Activate the environment
#     9) Remove the python virtual environment (if necessary)
#     10) Create the python virtual environment
#     11) Invoke custom functionality (if necessary)
#     12) Create Activate.sh and Deactivate.sh

# ----------------------------------------------------------------------
# |
# |  Internal Functions
# |
# ----------------------------------------------------------------------
function _InitializeShell() {
    echo "Initializing the micromamba shell..."

    temp_output_name=$(mktemp BootstrapImpl.XXXXXX)

    eval "$(~/.local/bin/micromamba shell hook --shell bash)" > "${temp_output_name}" 2>&1
    error=$?

    if [[ ${error} != 0 ]]; then
        echo "[1AInitializing the micromamba shell...[31m[1mFAILED[0m."
        echo ""

        cat "${temp_output_name}"
    else
        echo "[1AInitializing the micromamba shell...[32m[1mDONE[0m."
    fi

    rm "${temp_output_name}"
    return ${error}
}


function _ActivateEnvironment() {
    echo "Activating the micromamba environment..."

    temp_output_name=$(mktemp BootstrapImpl.XXXXXX)

    micromamba activate "Python${PYTHON_VERSION}" > "${temp_output_name}" 2>&1
    error=$?

    if [[ ${error} != 0 ]]; then
        echo "[1AActivating the micromamba environment...[31m[1mFAILED[0m."
        echo ""

        cat "${temp_output_name}"
    else
        echo "[1AActivating the micromamba environment...[32m[1mDONE[0m."
    fi

    rm "${temp_output_name}"
    return ${error}
}


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
is_force=0
is_debug=0

# ----------------------------------------------------------------------
# |
# |  Parse and Process is_debug
# |
# ----------------------------------------------------------------------
command_line_args=()

while [[ $# -gt 0 ]]; do
    if [[ "$1" == "--python-version" ]]; then
        PYTHON_VERSION=$2
        shift
    else
        if [[ "$1" == "--debug" ]]; then
            is_debug=1
        elif [[ "$1" == "--force" ]]; then
            is_force=1
        fi

        command_line_args+=("$1")
    fi

    shift
done

# ----------------------------------------------------------------------
if [[ ${is_debug} -eq 1 ]]; then
    set -x
fi

# ----------------------------------------------------------------------
# |
# |  Ensure that PYTHON_VERSION is set
# |
# ----------------------------------------------------------------------
if [[ -z ${PYTHON_VERSION} ]]; then
    echo "Downloading default python version information..."

    temp_output_name=$(mktemp BootstrapImpl.XXXXXX)

    curl --header "Cache-Control: no-cache, no-store" --header "Pragma: no-cache" --location https://raw.githubusercontent.com/davidbrownell/PythonBootstrapper/main/default_version --output default_version --no-progress-meter --fail-with-body > "${temp_output_name}" 2>&1
    error=$?

    if [[ ${error} != 0 ]]; then
        echo "[1ADownloading default python version information...[31m[1mFAILED[0m."
        echo ""

        cat "${temp_output_name}"

        rm default_version
        rm "${temp_output_name}"

        exit ${error}
    fi

    PYTHON_VERSION=$(tr -d "\r\n" < default_version)

    rm default_version
    rm "${temp_output_name}"

    echo "[1ADownloading default python version information...[32m[1mDONE[0m."
fi

# ----------------------------------------------------------------------
# |
# |  Ensure that PYTHON_VERSION is valid
# |
# ----------------------------------------------------------------------
echo "Validating python version..."

# The variable must have major and minor versions that are integers
IFS="." read -r -a python_version_parts <<< "${PYTHON_VERSION}"

# Trim chars from the last parameter
python_version_parts[1]="${python_version_parts[1]//[$'\r\n']}"

if ! {
    [[ ${#python_version_parts[@]} == 2 ]] \
    && [[ ${python_version_parts[0]} =~ ^[0-9]+$ ]] \
    && [[ ${python_version_parts[1]} =~ ^[0-9]+$ ]]
}; then
    echo "[1AValidating python version...[31m[1mFAILED[0m."
    echo ""

    echo "[31m[1mERROR:[0m The PYTHON_VERSION environment variable must be set to a valid python version."
    echo "[31m[1mERROR:[0m"
    echo "[31m[1mERROR:[0m Current Value:"
    echo "[31m[1mERROR:[0m     ${PYTHON_VERSION}"
    echo "[31m[1mERROR:[0m"
    echo "[31m[1mERROR:[0m Example:"
    echo "[31m[1mERROR:[0m     export PYTHON_VERISON=3.12"
    echo ""

    exit 1
fi

echo "[1AValidating python version...[32m[1mDONE[0m."

echo ""
echo "Python Version ${PYTHON_VERSION}"
echo ""

# ----------------------------------------------------------------------
# |
# |  Set global environment variables
# |
# ----------------------------------------------------------------------
# The PLATFORM, ARCH, and validation logic matches the logic found at
# https://raw.githubusercontent.com/mamba-org/micromamba-releases/main/install.sh
case "$(uname)" in
    Linux)
        PLATFORM="linux" ;;
    Darwin)
        PLATFORM="osx" ;;
    *NT*)
        PLATFORM="win" ;;
esac

ARCH="$(uname -m)"
case "$ARCH" in
    aarch64|ppc64le|arm64)
        ;;  # pass
    *)
        ARCH="64" ;;
esac

case "$PLATFORM-$ARCH" in
    linux-aarch64|linux-ppc64le|linux-64|osx-arm64|osx-64|win-64)
        ;;  # pass
    *)
        echo "[1ADownloading micromamba...[31m[1mFAILED[0m (failed to detect your operating system)."
        exit 1
esac

export PYTHON_BOOTSTRAPPER_ACTIVATION_DIR=$(pwd)
export PYTHON_BOOTSTRAPPER_ACTIVATION_VERSION=${PYTHON_VERSION}
export PYTHON_BOOTSTRAPPER_GENERATED_DIR=${PYTHON_BOOTSTRAPPER_ACTIVATION_DIR}/Generated/${PLATFORM}/Python${PYTHON_BOOTSTRAPPER_ACTIVATION_VERSION}

# ----------------------------------------------------------------------
# |
# |  Delete micromamba (if requested)
# |
# ----------------------------------------------------------------------
if [[ ${is_force} -eq 1 ]]; then
    # Remove the environment
    if [[ -d ~/micromamba/envs/Python${PYTHON_BOOTSTRAPPER_ACTIVATION_VERSION} ]]; then
        echo "Removing the Python${PYTHON_BOOTSTRAPPER_ACTIVATION_VERSION} micromamba environment..."

        rm -rf "${HOME}/micromamba/envs/Python${PYTHON_BOOTSTRAPPER_ACTIVATION_VERSION}"
        error=$?

        if [[ ${error} != 0 ]]; then
            echo "[1ARemoving the Python${PYTHON_BOOTSTRAPPER_ACTIVATION_VERSION} micromamba environment...[31m[1mFAILED[0m."
            echo ""

            exit ${error}
        fi

        echo "[1ARemoving the Python${PYTHON_BOOTSTRAPPER_ACTIVATION_VERSION} micromamba environment...[32m[1mDONE[0m."
    fi

    # Remove the binary
    if [[ -f ~/.local/bin/micromamba ]]; then
        echo "Removing the micromamba executable..."

        rm -f ~/.local/bin/micromamba
        error=$?

        if [[ ${error} != 0 ]]; then
            echo "[1ARemoving the micromamba executable...[31m[1mFAILED[0m."
            echo ""

            exit ${error}
        fi

        echo "[1ARemoving the micromamba executable...[32m[1mDONE[0m."
    fi
fi

# ----------------------------------------------------------------------
# |
# |  Download micromamba (if necessary)
# |
# ----------------------------------------------------------------------
echo "Downloading micromamba..."

if [[ -f "${HOME}/.local/bin/micromamba" ]]; then
    echo "[1ADownloading micromamba...[32m[1mDONE[0m (already exists)."
else
    [[ -d ~/.local/bin ]] || mkdir -p ~/.local/bin
    pushd ~/.local/bin > /dev/null || exit $?

    temp_output_name=$(mktemp BootstrapImpl.XXXXXX)

    curl --header "Cache-Control: no-cache, no-store" --header "Pragma: no-cache" --location https://github.com/mamba-org/micromamba-releases/releases/latest/download/micromamba-${PLATFORM}-${ARCH} --output "micromamba" --no-progress-meter --fail-with-body > "${temp_output_name}" 2>&1
    error=$?

    if [[ ${error} != 0 ]]; then
        echo "[1ADownloading micromamba...[31m[1mFAILED[0m."
        echo ""

        cat "${temp_output_name}"

        rm "${temp_output_name}"
        popd > /dev/null || exit $?

        exit ${error}
    fi

    chmod u+x ~/.local/bin/micromamba

    rm "${temp_output_name}"
    popd > /dev/null || exit $?

    echo "[1ADownloading micromamba...[32m[1mDONE[0m."
fi

# ----------------------------------------------------------------------
# |
# |  Initialize a new environment (if necessary)
# |
# ----------------------------------------------------------------------
echo "Initialzing the micromamba environment..."

if [[ -d "${HOME}/micromamba/envs/Python${PYTHON_BOOTSTRAPPER_ACTIVATION_VERSION}" ]]; then
    echo "[1AInitializing the micromamba environment...[32m[1mDONE[0m (already exists)."
else
    echo "[1AInitializing the micromamba environment...[32m[1mDONE[0m (a new environment will be created)."
    echo ""
    echo ""
    echo ""

    # ----------------------------------------------------------------------
    # |  Create the micromamba environment
    ~/.local/bin/micromamba create --channel conda-forge --name "Python${PYTHON_BOOTSTRAPPER_ACTIVATION_VERSION}" --root-prefix "${HOME}/micromamba" --yes "python~=${PYTHON_BOOTSTRAPPER_ACTIVATION_VERSION}.0"
    error=$?

    if [[ ${error} != 0 ]]; then
        exit ${error}
    fi

    echo ""
    echo ""
    echo ""

    # From this point forward, delete the environment if an error occurrs as the environment
    # won't be fully initialized.

    # ----------------------------------------------------------------------
    # |  Initialize the shell
    if [[ ${error} == 0 ]]; then
        _InitializeShell
        error=$?
    fi

    # ----------------------------------------------------------------------
    # |  Activate the environment
    if [[ ${error} == 0 ]]; then
        _ActivateEnvironment
        error=$?
    fi

    # ----------------------------------------------------------------------
    # |  Install virtualenv
    if [[ ${error} == 0 ]]; then
        echo ""
        echo ""
        echo ""

        pip install virtualenv
        error=$?

        echo ""
        echo ""
        echo ""
    fi

    # Deactivte the environment (note that this will always be done, event if the
    # previous commands failed).
    echo "Deactivating the micromamba environment..."

    micromamba deactivate
    error=$?

    if [[ ${error} != 0 ]]; then
        echo "[1ADeactivating the micromamba environment...[31m[1mFAILED[0m."
        echo ""
    else
        echo "[1ADeactivating the micromamba environment...[32m[1mDONE[0m."
    fi

    # Delete the environment if an error occurred
    if [[ ${error} != 0 ]]; then
        echo "Removing the micromamba environment..."

        temp_output_name=$(mktemp BootstrapImpl.XXXXXX)

        rm -rf "${HOME}/micromamba/envs/Python${PYTHON_BOOTSTRAPPER_ACTIVATION_VERSION}" > "${temp_output_name}" 2>&1
        rm_error=$?

        if [[ ${rm_error} != 0 ]]; then
            echo "[1ARemoving the micromamba environment...[31m[1mFAILED[0m."
            echo ""

            cat "${temp_output_name}"
        else
            echo "[1ARemoving the micromamba environment...[32m[1mDONE[0m."
        fi

        rm "${temp_output_name}"
        exit ${error}
    fi
fi

# ----------------------------------------------------------------------
# |
# |  Initialize the micromamba shell
# |
# ----------------------------------------------------------------------
_InitializeShell
error=$?

if [[ ${error} != 0 ]]; then
    exit ${error}
fi

# ----------------------------------------------------------------------
# |
# |  Activate the environment
# |
# ----------------------------------------------------------------------
_ActivateEnvironment
error=$?

if [[ ${error} != 0 ]]; then
    exit ${error}
fi

# ----------------------------------------------------------------------
# |
# |  Remove the python virtual environment (if necessary)
# |
# ----------------------------------------------------------------------
if [[ -d "${PYTHON_BOOTSTRAPPER_GENERATED_DIR}" ]]; then
    echo "Removing the existing python virtual environment..."

    rm -rf "${PYTHON_BOOTSTRAPPER_GENERATED_DIR}"
    error=$?

    if [[ ${error} != 0 ]]; then
        echo "[1ARemoving the existing python virtual environment...[31m[1mFAILED[0m."
        echo ""

        exit ${error}
    fi

    echo "[1ARemoving the existing python virtual environment...[32m[1mDONE[0m."
fi

# ----------------------------------------------------------------------
# |
# |  Create the python virtual environment
# |
# ----------------------------------------------------------------------
echo "Creating the python virtual environment..."

temp_output_name=$(mktemp BootstrapImpl.XXXXXX)

virtualenv --no-periodic-update --no-vcs-ignore --verbose "${PYTHON_BOOTSTRAPPER_GENERATED_DIR}" > "${temp_output_name}" 2>&1
error=$?

if [[ ${error} != 0 ]]; then
    echo "[1ACreating the python virtual environment...[31m[1mFAILED[0m."
    echo ""

    cat "${temp_output_name}"

    rm "${temp_output_name}"
    exit ${error}
fi

rm "${temp_output_name}"
echo "[1ACreating the python virtual environment...[32m[1mDONE[0m."

# ----------------------------------------------------------------------
# |
# |  Invoke custom functionality (if necessary)
# |
# ----------------------------------------------------------------------
if [[ -f "BootstrapEpilog.sh" ]] || [[ -f "BootstrapEpilog.py" ]]; then
    # ----------------------------------------------------------------------
    # |  Activate the python library
    source "${PYTHON_BOOTSTRAPPER_GENERATED_DIR}/bin/activate"
    echo ""

    if [[ -f "BootstrapEpilog.sh" ]]; then
        ./BootstrapEpilog.sh
        error=$?

        if [[ ${error} != 0 ]]; then
            echo "[31m[1mERROR: [0mBootstrapEpilog.sh failed."
            exit ${error}
        fi
    fi

    if [[ -f "BootstrapEpilog.py" ]]; then
        python BootstrapEpilog.py BootstrapEpilog_py.sh "${command_line_args[@]}"
        error=$?

        if [[ ${error} != 0 ]]; then
            echo "[31m[1mERROR: [0mBootstrapEpilog.py failed."
            ! [[ -f "BootstrapEpilog_py.sh" ]] || rm "BootstrapEpilog_py.sh"
            exit ${error}
        fi

        if [[ -f "BootstrapEpilog_py.sh" ]]; then
            chmod u+x "BootstrapEpilog_py.sh"

            ./BootstrapEpilog_py.sh
            error=$?

            rm "BootstrapEpilog_py.sh"

            if [[ ${error} != 0 ]]; then
                echo "[31m[1mERROR: [0mExecuting the BootstrapEpilog.py output failed."
                exit ${error}
            fi
        fi
    fi

    deactivate
fi

echo ""

# ----------------------------------------------------------------------
# |
# |  Create Activate.sh and Deactivate.sh
# |
# ----------------------------------------------------------------------
echo "Creating Activate.sh..."

# ----------------------------------------------------------------------
cat <<END_OF_CONTENT > Activate${PYTHON_BOOTSTRAPPER_ACTIVATION_VERSION}.sh
#!/usr/bin/env bash

# This file is generated during the Bootstrap process and is specific to your environment.
# IT SHOULD NOT be added to your source control system.

# Ensure that the script is being invoked via source (as it modifies the current environment)
script_name=\${ZSH_ARGZERO}
if [[ -z \${script_name} ]]; then
    script_name=\${0##*/}
fi

if [[ \${script_name} == Activate${PYTHON_BOOTSTRAPPER_ACTIVATION_VERSION}.sh ]] || [[ \${script_name} == Activate.sh ]]
then
    echo ""
    echo "[31m[1mERROR:[0m This script activates a terminal for development according to information specific to the repository."
    echo "[31m[1mERROR:[0m"
    echo "[31m[1mERROR:[0m Because this process makes changes to environment variables, it must be run within the current context."
    echo "[31m[1mERROR:[0m To do this, please source (run) the script as follows:"
    echo "[31m[1mERROR:[0m"
    echo "[31m[1mERROR:[0m     source ./\${script_name}"
    echo "[31m[1mERROR:[0m"
    echo "[31m[1mERROR:[0m         - or -"
    echo "[31m[1mERROR:[0m"
    echo "[31m[1mERROR:[0m     . ./\${script_name}"
    echo "[31m[1mERROR:[0m"
    echo ""

    # It's ok to use exit here, as the script wasn't sourced
    exit 1
fi

if [[ ! -z \${PYTHON_BOOTSTRAPPER_ACTIVATION_DIR} ]] && [[ "\${PYTHON_BOOTSTRAPPER_ACTIVATION_DIR}" != "${PYTHON_BOOTSTRAPPER_ACTIVATION_DIR}" ]]; then
    echo ""
    echo "[31m[1mERROR:[0m This environment cannot be activated over \"\${PYTHON_BOOTSTRAPPER_ACTIVATION_DIR}\"."

    return 1
fi

if [[ ! -z \${PYTHON_BOOTSTRAPPER_ACTIVATION_VERSION} ]] && [[ "\${PYTHON_BOOTSTRAPPER_ACTIVATION_VERSION}" != "${PYTHON_BOOTSTRAPPER_ACTIVATION_VERSION}" ]]; then
    echo ""
    echo "[31m[1mERROR:[0m This environment cannot be activated over \"\${PYTHON_BOOTSTRAPPER_ACTIVATION_VERSION}\"."

    return 1
fi

pushd "${PYTHON_BOOTSTRAPPER_ACTIVATION_DIR}" > /dev/null || return \$?

export MAMBA_ROOT_PREFIX=~/micromamba
eval "\$(~/.local/bin/micromamba shell hook --shell bash)" || return \$?

# Get the original prompt before it is decorated
original_prompt=\${PS1}

micromamba activate "Python${PYTHON_BOOTSTRAPPER_ACTIVATION_VERSION}" || return \$?
source "${PYTHON_BOOTSTRAPPER_GENERATED_DIR}/bin/activate" || return \$?

export PYTHON_BOOTSTRAPPER_ACTIVATION_DIR="${PYTHON_BOOTSTRAPPER_ACTIVATION_DIR}"
export PYTHON_BOOTSTRAPPER_ACTIVATION_VERSION="${PYTHON_BOOTSTRAPPER_ACTIVATION_VERSION}"
export PYTHON_BOOTSTRAPPER_GENERATED_DIR="${PYTHON_BOOTSTRAPPER_GENERATED_DIR}"

function Execute() {
    # Set the prompt
    if [[ -z \${_PYTHON_ENVIRONMENT_IS_ACTIVATED} ]]; then
        # If here, the variable is not set
        PS1="(Python${PYTHON_BOOTSTRAPPER_ACTIVATION_VERSION}) \${original_prompt}"
    else
        PS1="\${original_prompt}"
    fi

    if [[ -f "ActivateEpilog.sh" ]]; then
        source ./ActivateEpilog.sh "\$@"
        error=\$?

        if [[ \${error} != 0 ]]; then
            echo "[31m[1mERROR: [0mActivateEpilog.sh failed."
            return \${error}
        fi
    fi

    if [[ -f "ActivateEpilog.py" ]]; then
        # Create the instructions
        python ActivateEpilog.py ActivateEpilog_py.sh "\$@"
        error=\$?

        if [[ \${error} != 0 ]]; then
            echo "[31m[1mERROR: [0mActivateEpilog.py failed."
            ! [[ -f "ActivateEpilog_py.sh" ]] || rm "ActivateEpilog_py.sh"
            return \${error}
        fi

        # Execute the instructions
        if [[ -f "ActivateEpilog_py.sh" ]]; then
            chmod u+x ActivateEpilog_py.sh

            source ./ActivateEpilog_py.sh
            error=\$?

            rm -f ActivateEpilog_py.sh

            if [[ \${error} != 0 ]]; then
                echo "[31m[1mERROR: [0mExecuting the ActivateEpilog.py output failed."
                return \${error}
            fi
        fi
    fi

    return 0
}

Execute "\$@"
error=\$?

if [[ \${error} != 0 ]]; then
    unset PYTHON_BOOTSTRAPPER_GENERATED_DIR
    unset PYTHON_BOOTSTRAPPER_ACTIVATION_VERSION
    unset PYTHON_BOOTSTRAPPER_ACTIVATION_DIR

    deactivate || return \$?
    micromamba deactivate || return \$?

    return \${error}
fi

echo ""
echo "[61m[1m${PYTHON_BOOTSTRAPPER_ACTIVATION_DIR}[0m has been [32m[1mactivated[0m."
echo ""

export _PYTHON_ENVIRONMENT_IS_ACTIVATED=1
return 0
END_OF_CONTENT
# ----------------------------------------------------------------------

chmod u+x Activate${PYTHON_BOOTSTRAPPER_ACTIVATION_VERSION}.sh

! [[ -f "Activate.sh" ]] || rm "Activate.sh"
ln Activate${PYTHON_BOOTSTRAPPER_ACTIVATION_VERSION}.sh Activate.sh

echo "[1ACreating Activate.sh...[32m[1mDONE[0m."

echo "Creating Deactivate.sh..."

# ----------------------------------------------------------------------
cat <<END_OF_CONTENT > Deactivate${PYTHON_BOOTSTRAPPER_ACTIVATION_VERSION}.sh
#!/usr/bin/env bash

# This file is generated during the Bootstrap process and is specific to your environment.
# IT SHOULD NOT be added to your source control system.

# Ensure that the script is being invoked via source (as it modifies the current environment)
script_name=\${ZSH_ARGZERO}
if [[ -z \${script_name} ]]; then
    script_name=\${0##*/}
fi

if [[ \${script_name} == Deactivate${PYTHON_BOOTSTRAPPER_ACTIVATION_VERSION}.sh ]] || [[ \${script_name} == Deactivate.sh ]]
then
    echo ""
    echo "[31m[1mERROR:[0m This script activates a terminal for development according to information specific to the repository."
    echo "[31m[1mERROR:[0m"
    echo "[31m[1mERROR:[0m Because this process makes changes to environment variables, it must be run within the current context."
    echo "[31m[1mERROR:[0m To do this, please source (run) the script as follows:"
    echo "[31m[1mERROR:[0m"
    echo "[31m[1mERROR:[0m     source ./\${script_name}"
    echo "[31m[1mERROR:[0m"
    echo "[31m[1mERROR:[0m         - or -"
    echo "[31m[1mERROR:[0m"
    echo "[31m[1mERROR:[0m     . ./\${script_name}"
    echo "[31m[1mERROR:[0m"
    echo ""

    # It's ok to use exit here, as the script wasn't sourced
    exit 1
fi

if [[ -z \${PYTHON_BOOTSTRAPPER_ACTIVATION_DIR} ]]; then
    echo ""
    echo "[31m[1mERROR:[0m The environment has not been activated."

    return 1
fi

if [[ "\${PYTHON_BOOTSTRAPPER_ACTIVATION_DIR}" != "${PYTHON_BOOTSTRAPPER_ACTIVATION_DIR}" ]]; then
    echo ""
    echo "[31m[1mERROR:[0m This environment was activated by \"\${PYTHON_BOOTSTRAPPER_ACTIVATION_DIR}\"."

    return 1
fi

if [[ "\${PYTHON_BOOTSTRAPPER_ACTIVATION_VERSION}" != "${PYTHON_BOOTSTRAPPER_ACTIVATION_VERSION}" ]]; then
    echo ""
    echo "[31m[1mERROR:[0m This environment was activated with \"\${PYTHON_BOOTSTRAPPER_ACTIVATION_VERSION}\"."

    return 1
fi

if [[ -f "DeactivateEpilog.sh" ]]; then
    source ./DeactivateEpilog.sh
    error=\$?

    if [[ \${error} != 0 ]]; then
        echo "[31m[1mERROR: [0mDeactivateEpilog.sh failed."
        return \${error}
    fi
fi

if [[ -f "DeactivateEpilog.py" ]]; then
    # Create the instructions
    python DeactivateEpilog.py DeactivateEpilog_py.sh "\$@"
    error=\$?

    if [[ \${error} != 0 ]]; then
        echo "[31m[1mERROR: [0mDeactivateEpilog.py failed."
        ! [[ -f "DeactivateEpilog_py.sh" ]] || rm "DeactivateEpilog_py.sh"
        return \${error}
    fi

    # Execute the instructions
    if [[ -f "DeactivateEpilog_py.sh" ]]; then
        chmod u+x DeactivateEpilog_py.sh

        source ./DeactivateEpilog_py.sh
        error=\$?

        rm -f DeactivateEpilog_py.sh

        if [[ \${error} != 0 ]]; then
            echo "[31m[1mERROR: [0mExecuting the DeactivateEpilog.py output failed."
            return \${error}
        fi
    fi
fi

deactivate # Python virtualenv || return \$?
micromamba deactivate || return \$?

popd >> /dev/null || return \$?

unset _PYTHON_ENVIRONMENT_IS_ACTIVATED
unset PYTHON_BOOTSTRAPPER_GENERATED_DIR
unset PYTHON_BOOTSTRAPPER_ACTIVATION_VERSION
unset PYTHON_BOOTSTRAPPER_ACTIVATION_DIR

echo ""
echo "[61m[1m${PYTHON_BOOTSTRAPPER_ACTIVATION_DIR}[0m has been [31m[1mdeactivated[0m."
echo ""
END_OF_CONTENT
# ----------------------------------------------------------------------

chmod u+x Deactivate${PYTHON_BOOTSTRAPPER_ACTIVATION_VERSION}.sh

! [[ -f "Deactivate.sh" ]] || rm "Deactivate.sh"
ln Deactivate${PYTHON_BOOTSTRAPPER_ACTIVATION_VERSION}.sh Deactivate.sh

echo "[1ACreating Deactivate.sh...[32m[1mDONE[0m."

# ----------------------------------------------------------------------
# |
# |  Final Output
# |
# ----------------------------------------------------------------------
echo ""
echo ""
echo ""
echo "[32m[1m-----------------------------------------------------------------------[0m"
echo "[32m[1m-----------------------------------------------------------------------[0m"
echo ""
echo "Your repository has been successfully bootstrapped. Run the following"
echo "commands to activate and deactivate the local development environment:"
echo ""
echo "  [61m[1mActivate.sh[0m:    ${PYTHON_BOOTSTRAPPER_ACTIVATION_DIR}/[61m[1mActivate.sh[0m"
echo "  [61m[1mDeactivate.sh[0m:  ${PYTHON_BOOTSTRAPPER_ACTIVATION_DIR}/[61m[1mDeactivate.sh[0m"
echo ""
echo "[32m[1m-----------------------------------------------------------------------[0m"
echo "[32m[1m-----------------------------------------------------------------------[0m"
echo ""
echo ""
echo ""

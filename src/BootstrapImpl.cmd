@REM ----------------------------------------------------------------------
@REM |
@REM |  BootstrapImpl.cmd
@REM |
@REM |  David Brownell <db@DavidBrownell.com>
@REM |      2023-12-09 17:53:01
@REM |
@REM ----------------------------------------------------------------------
@REM |
@REM |  Copyright David Brownell 2023
@REM |  Distributed under the Boost Software License, Version 1.0. See
@REM |  accompanying file LICENSE_1_0.txt or copy at
@REM |  http://www.boost.org/LICENSE_1_0.txt.
@REM |
@REM ----------------------------------------------------------------------
@setlocal EnableDelayedExpansion

@echo.
@echo Version 0.3.0
@echo.

@REM This script:
@REM     1) Ensure that PYTHON_VERSION is set
@REM     2) Ensure that PYTHON_VERSION is valid
@REM     3) Install micromamba (if necessary)
@REM     4) Initialize a new environment (if necessary)
@REM        a) Create the micromamba environment
@REM        a) Intialize the micromamba shell
@REM        c) Activate the environment
@REM        d) Install virtualenv
@REM        e) Deactivate the environment
@REM     5) Activate the environment
@REM     6) Create a python virtual environment
@REM     7) Invoke custom functionality (if necessary)
@REM     8) Create Activate.cmd and Deactivate.cmd

@set _DELETE_ENVIRONMENT_ON_ERROR=0
@set _IS_FORCE=0
@set _IS_DEBUG=0

@REM ----------------------------------------------------------------------
@REM |
@REM |  Parse and Process Arguments
@REM |
@REM ----------------------------------------------------------------------
:ParseArgs
@if '%1' NEQ '' (
    @set _COMMAND_LINE_ARGS=%_COMMAND_LINE_ARGS% %1

    @if '%1' EQU '--debug' @set _IS_DEBUG=1
    @if '%1' EQU '--force' @set _IS_FORCE=1

    @shift /1
    @goto :ParseArgs
)

@REM ----------------------------------------------------------------------
@if %_IS_DEBUG% NEQ 1 (
    @echo off
)

if %_IS_FORCE% EQU 0 goto :Force_End
if not exist "%USERPROFILE%\micromamba" goto :Force_End

echo Removing micromamba...

rmdir /S /Q "%USERPROFILE%\micromamba"
set _ERRORLEVEL=%ERRORLEVEL%

if %ERRORLEVEL% NEQ 0 (
    echo [1ARemoving micromamba...[31m[1mFAILED[0m.
    echo.

    goto :Exit
)

echo [1ARemoving micromamba...[32m[1mDONE[0m.

:Force_End

@REM ----------------------------------------------------------------------
@REM |
@REM |  Ensure that PYTHON_VERSION is set
@REM |
@REM ----------------------------------------------------------------------
if "%PYTHON_VERSION%" NEQ "" goto :SetPythonVersion_End

@REM Download default_version
echo Downloading default python version information...
call :_CreateTempFileName

curl --header "Cache-Control: no-cache, no-store" --header "Pragma: no-cache" --location https://raw.githubusercontent.com/davidbrownell/PythonBootstrapper/main/default_version --output default_version --no-progress-meter --fail-with-body > "%_BOOTSTRAP_IMPL_TEMP_FILENAME%" 2>&1
set _ERRORLEVEL=%ERRORLEVEL%

if %_ERRORLEVEL% NEQ 0 (
    echo [1ADownloading default python version information...[31m[1mFAILED[0m.
    echo.

    type "%_BOOTSTRAP_IMPL_TEMP_FILENAME%"
    goto :Exit
)

call :_DeleteTempFile
echo [1ADownloading default python version information...[32m[1mDONE[0m.

for /f "delims=" %%i in (default_version) do set PYTHON_VERSION=%%i
:SetPythonVersion_End

@REM ----------------------------------------------------------------------
@REM |
@REM |  Ensure that PYTHON_VERSION is valid
@REM |
@REM ----------------------------------------------------------------------
echo Validating python version...

@REM The variable must have major and minor versions that are integers
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set _PYTHON_VERSION_MAJOR=%%a
    set _PYTHON_VERSION_MINOR=%%b
)

set /A _PYTHON_VERSION_MAJOR_TEST=%_PYTHON_VERSION_MAJOR%
set /A _PYTHON_VERSION_MINOR_TEST=%_PYTHON_VERSION_MINOR%

if "%_PYTHON_VERSION_MAJOR%" EQU "" goto :InvalidVersion
if %_PYTHON_VERSION_MAJOR% NEQ %_PYTHON_VERSION_MAJOR_TEST% goto :InvalidVersion
if "%_PYTHON_VERSION_MINOR%" EQU "" goto :InvalidVersion
if %_PYTHON_VERSION_MINOR% NEQ %_PYTHON_VERSION_MINOR_TEST% goto :InvalidVersion

echo [1AValidating python version...[32m[1mDONE[0m.
goto :EnsureValidVersion_End

:InvalidVersion
echo [1AValidating python version...[31m[1mFAILED[0m.
echo.
echo The PYTHON_VERSION environment variable must be set to a valid python version.
echo.
echo Current Value:
echo     %PYTHON_VERSION%
echo.
echo Example:
echo     set PYTHON_VERISON=3.12
echo.

set _ERRORLEVEL=-1
goto :Exit

:EnsureValidVersion_End

@REM ----------------------------------------------------------------------
@REM |
@REM |  Install micromamba (if necessary)
@REM |
@REM ----------------------------------------------------------------------
echo Downloading micromamba...

if exist "%USERPROFILE%\micromamba\micromamba.exe" (
    echo [1ADownloading micromamba...[32m[1mDONE[0m (already exists^).
    goto :InstallMicromamba_End
)

if not exist "%USERPROFILE%\micromamba" (
    mkdir "%USERPROFILE%\micromamba"
)

call :_CreateTempFileName
curl --header "Cache-Control: no-cache, no-store" --header "Pragma: no-cache" --location https://github.com/mamba-org/micromamba-releases/releases/latest/download/micromamba-win-64 --output "%USERPROFILE%\micromamba\micromamba.exe" --no-progress-meter --fail-with-body > "%_BOOTSTRAP_IMPL_TEMP_FILENAME%" 2>&1
set _ERRORLEVEL=%ERRORLEVEL%

if %_ERRORLEVEL% NEQ 0 (
    echo [1ADownloading micromamba...[31m[1mFAILED[0m.
    echo.

    type "%_BOOTSTRAP_IMPL_TEMP_FILENAME%"
    goto :Exit
)

call :_DeleteTempFile
echo [1ADownloading micromamba...[32m[1mDONE[0m.

:InstallMicromamba_End

@REM ----------------------------------------------------------------------
@REM |  Add micromamba.bat to the path
echo ";%PATH%;" | findstr /C:";%USERPROFILE%\micromamba\condabin;" >NUL
if %ERRORLEVEL% EQU 0 goto :AddMicromambaToPath_End

set PATH=%USERPROFILE%\micromamba\condabin;%PATH%

:AddMicromambaToPath_End

@REM ----------------------------------------------------------------------
@REM |
@REM |  Initialize a new environment (if necessary)
@REM |
@REM ----------------------------------------------------------------------
echo Initializing the micromamba environment...

if exist "%USERPROFILE%\micromamba\envs\Python%PYTHON_VERSION%" (
    echo [1AInitializing the micromamba environment...[32m[1mDONE[0m (already exists^).
    goto :InitializeNewEnvironment_End
)

echo [1AInitializing the micromamba environment...[32m[1mDONE[0m (a new environment will be created^).

echo.
echo.
echo.

@REM ----------------------------------------------------------------------
@REM |  Create the micromamba environment
"%USERPROFILE%\micromamba\micromamba.exe" create --channel conda-forge --name Python%PYTHON_VERSION% --root-prefix "%USERPROFILE%\micromamba" --yes python~=%PYTHON_VERSION%.0
set _ERRORLEVEL=%ERRORLEVEL%

if %_ERRORLEVEL% NEQ 0 goto :Exit

echo.
echo.
echo.

REM From this point forward, delete the environment if an error occurs as the environment
REM won't be fully initialized.
set _DELETE_ENVIRONMENT_ON_ERROR=1

@REM ----------------------------------------------------------------------
@REM -- Initialize the micromamba shell
echo Initializing the micromamba shell...
call :_CreateTempFileName

call micromamba.bat shell init --root-prefix=%USERPROFILE%\micromamba --shell cmd.exe > "%_BOOTSTRAP_IMPL_TEMP_FILENAME%" 2>&1
set _ERRORLEVEL=%ERRORLEVEL%

if %_ERRORLEVEL% NEQ 0 (
    echo [1AInitializing the micromamba shell...[31m[1mFAILED[0m.
    echo.

    type "%_BOOTSTRAP_IMPL_TEMP_FILENAME%"
    goto :Exit
)

echo [1AInitializing the micromamba shell...[32m[1mDONE[0m.
call :_DeleteTempFile

@REM ----------------------------------------------------------------------
@REM |  Activate the environment
echo Activating the micromamba environment...

call micromamba.bat activate Python%PYTHON_VERSION%
set _ERRORLEVEL=%ERRORLEVEL%

if %_ERRORLEVEL% NEQ 0 (
    echo [1AActivating the micromamba environment...[31m[1mFAILED[0m.
    goto :Exit
)

echo [1AActivating the micromamba environment...[32m[1mDONE[0m.

@REM ----------------------------------------------------------------------
@REM |  Install virtual env
echo.
echo.
echo.

pip install virtualenv
set _ERRORLEVEL=%ERRORLEVEL%

echo.
echo.
echo.

@REM Deactivate the environment (note that this will always be done, even if the
@REM previous command failed).
echo Deactivating the micromamba environment...

call micromamba.bat deactivate
if %ERRORLEVEL% NEQ 0 (
    echo [1ADeactivating the micromamba environment...[31m[1mFAILED[0m.
) else (
    echo [1ADeactivating the micromamba environment...[32m[1mDONE[0m.
)

@REM Terminate if the previous command failed
if %_ERRORLEVEL% NEQ 0 goto :Exit

REM If here, the environment has been fully initialized
set _DELETE_ENVIRONMENT_ON_ERROR=0

:InitializeNewEnvironment_End

@REM ----------------------------------------------------------------------
@REM |
@REM |  Activate the environment
@REM |
@REM ----------------------------------------------------------------------
echo Activating the micromamba environment...

call micromamba.bat activate Python%PYTHON_VERSION%
set _ERRORLEVEL=%ERRORLEVEL%

if %_ERRORLEVEL% NEQ 0 (
    echo [1AActivating the micromamba environment...[31m[1mFAILED[0m.
    goto :Exit
)

echo [1AActivating the micromamba environment...[32m[1mDONE[0m.


@REM ----------------------------------------------------------------------
@REM |
@REM |  Create a python virtual environment
@REM |
@REM ----------------------------------------------------------------------
echo Creating a python virtual environment...

call :_CreateTempFileName
virtualenv --clear --no-periodic-update --no-vcs-ignore --verbose .\Generated\Windows\Python%PYTHON_VERSION% > %_BOOTSTRAP_IMPL_TEMP_FILENAME% 2>&1
set _ERRORLEVEL=%ERRORLEVEL%

if %_ERRORLEVEL% NEQ 0 (
    echo [1ACreating a python virtual environment...[31m[1mFAILED[0m.
    echo.

    type "%_BOOTSTRAP_IMPL_TEMP_FILENAME%"
    goto :Exit
)

call :_DeleteTempFile
echo [1ACreating a python virtual environment...[32m[1mDONE[0m.

@REM ----------------------------------------------------------------------
@REM |
@REM |  Invoke custom functionality (if necessary)
@REM |
@REM ----------------------------------------------------------------------
if exist "BootstrapEpilog.cmd" goto :BootstrapEpilog_Execute
if exist "BootstrapEpilog.py" goto :BootstrapEpilog_Execute
goto :BootstrapEpilog_Skip

:BootstrapEpilog_Execute
@REM ----------------------------------------------------------------------
@REM |  Activate the python library
call Generated\Windows\Python%PYTHON_VERSION%\Scripts\activate.bat

echo.

if not exist "BootstrapEpilog.cmd" goto :Epilog_ExecuteCmd_End

call BootstrapEpilog.cmd
set _ERRORLEVEL=%ERRORLEVEL%

if %_ERRORLEVEL% NEQ 0 (
    echo.
    echo [31m[1mERROR: [0mBootstrapEpilog.cmd failed.
    goto :Exit
)

:Epilog_ExecuteCmd_End

if not exist "BootstrapEpilog.py" goto :Epiolg_ExecutePy_End

python BootstrapEpilog.py BootstrapEpilog_py.cmd %_COMMAND_LINE_ARGS%
set _ERRORLEVEL=%ERRORLEVEL%

if %_ERRORLEVEL% NEQ 0 (
    echo [31m[1mERROR: [0mBootstrapEpilog.py failed.
    if exist BootstrapEpilog_py.cmd del BootstrapEpilog_py.cmd
    goto :Exit
)

REM Execute the instructions
if not exist BootstrapEpilog_py.cmd goto :Epilog_ExecutePyCmd_End

call BootstrapEpilog_py.cmd
set _ERRORLEVEL=%ERRORLEVEL%

del BootstrapEpilog_py.cmd

if %_ERRORLEVEL% NEQ 0 (
    echo.
    echo [31m[1mERROR: [0mExecuting the BootstrapEpilog.py output failed.
    goto :Exit
)

:Epilog_ExecutePyCmd_End
:Epiolg_ExecutePy_End
:BootstrapEpilog_Skip

echo.

@REM ----------------------------------------------------------------------
@REM |
@REM |  Create Activate.cmd and Deactivate.cmd
@REM |
@REM ----------------------------------------------------------------------
echo Creating Activate.cmd...

(
    echo @REM This file is generated during the Bootstrap process and is specific to your environment.
    echo @REM IT SHOULD NOT be added to your source control system.
    echo @echo off
    echo.
    echo pushd %cd%
    echo.
    echo call %USERPROFILE%\micromamba\condabin\micromamba.bat activate Python%PYTHON_VERSION%
    echo call .\Generated\Windows\Python%PYTHON_VERSION%\Scripts\activate.bat
    echo.
    echo set PROMPT=(Python%PYTHON_VERSION%^) $P$G
    echo.
    echo set _ERRORLEVEL=0
    echo.
    echo if exist "ActivateEpilog.cmd" goto :ActivateEpilog_Execute
    echo if exist "ActivateEpilog.py" goto :ActivateEpilog_Execute
    echo goto :ActivateEpilog_Skip
    echo.
    echo :ActivateEpilog_Execute
    echo.
    echo if not exist "ActivateEpilog.cmd" goto :ActivateEpilog_ExecuteCmd_End
    echo.
    echo call ActivateEpilog.cmd
    echo set _ERRORLEVEL=%%ERRORLEVEL%%
    echo.
    echo if %%_ERRORLEVEL%% NEQ 0 (
    echo     echo.
    echo     echo [31m[1mERROR: [0mActivateEpilog.cmd failed.
    echo     goto :Exit
    echo ^)
    echo.
    echo :ActivateEpilog_ExecuteCmd_End
    echo.
    echo if not exist "ActivateEpilog.py" goto :ActivateEpilog_ExecutePy_End
    echo.
    echo REM Create the instructions
    echo python ActivateEpilog.py ActivateEpilog_py.cmd %%*
    echo set _ERRORLEVEL=%%ERRORLEVEL%%
    echo.
    echo if %%_ERRORLEVEL%% NEQ 0 (
    echo     echo [31m[1mERROR: [0mActivateEpilog.py failed.
    echo     if exist ActivateEpilog_py.cmd del ActivateEpilog_py.cmd
    echo     goto :Exit
    echo ^)
    echo.
    echo REM Execute the instructions
    echo if not exist ActivateEpilog_py.cmd goto :ActivattEpilog_ExecutePyCmd_End
    echo.
    echo call ActivateEpilog_py.cmd
    echo set _ERRORLEVEL=%%ERRORLEVEL%%
    echo.
    echo del ActivateEpilog_py.cmd
    echo.
    echo if %%_ERRORLEVEL%% NEQ 0 (
    echo     echo.
    echo     echo [31m[1mERROR: [0mExecuting the ActivateEpilog.py output failed.
    echo     goto :Exit
    echo ^)
    echo.
    echo :ActivateEpilog_ExecutePyCmd_End
    echo :ActivateEpilog_ExecutePy_End
    echo :ActivateEpilog_Skip
    echo.
    echo echo.
    echo echo [61m[1m%CD%[0m has been [32m[1mactivated[0m.
    echo echo.
    echo.
    echo :Exit
    echo exit /B %%_ERRORLEVEL%%
) > Activate.cmd

echo [1ACreating Activate.cmd...[32m[1mDONE[0m.

echo Creating Deactivate.cmd...

(
    echo @REM This file is generated during the Bootstrap process and is specific to your environment.
    echo @REM IT SHOULD NOT be added to your source control system.
    echo @echo off
    echo.
    echo set _ERRORLEVEL=0
    echo.
    echo if exist "DeactivateEpilog.cmd" goto :DeactivateEpilog_Execute
    echo if exist "DeactivateEpilog.py" goto :DeactivateEpilog_Execute
    echo goto :DeactivateEpilog_Skip
    echo.
    echo :DeactivateEpilog_Execute
    echo.
    echo if not exist "DeactivateEpilog.cmd" goto :DeactivateEpilog_ExecuteCmd_End
    echo.
    echo call DeactivateEpilog.cmd
    echo set _ERRORLEVEL=%%ERRORLEVEL%%
    echo.
    echo if %%_ERRORLEVEL%% NEQ 0 (
    echo     echo.
    echo     echo [31m[1mERROR: [0mDeactivateEpilog.cmd failed.
    echo     goto :Exit
    echo ^)
    echo.
    echo :DeactivateEpilog_ExecuteCmd_End
    echo.
    echo if not exist "DeactivateEpilog.py" goto :DeactivateEpilog_ExecutePy_End
    echo.
    echo REM Create the instructions
    echo python DeactivateEpilog.py DeactivateEpilog_py.cmd %%*
    echo set _ERRORLEVEL=%%ERRORLEVEL%%
    echo.
    echo if %%_ERRORLEVEL%% NEQ 0 (
    echo     echo [31m[1mERROR: [0mDeactivateEpilog.py failed.
    echo     if exist DeactivateEpilog_py.cmd del DeactivateEpilog_py.cmd
    echo     goto :Exit
    echo ^)
    echo.
    echo REM Execute the instructions
    echo if not exist DeactivateEpilog_py.cmd goto :DeactivateEpilog_ExecutePyCmd_End
    echo.
    echo call DeactivateEpilog_py.cmd
    echo set _ERRORLEVEL=%%ERRORLEVEL%%
    echo.
    echo del DeactivateEpilog_py.cmd
    echo.
    echo if %%_ERRORLEVEL%% NEQ 0 (
    echo     echo.
    echo     echo [31m[1mERROR: [0mExecuting the DeactivateEpilog.py output failed.
    echo     goto :Exit
    echo ^)
    echo.
    echo :DeactivateEpilog_ExecutePyCmd_End
    echo :DeactivateEpilog_ExecutePy_End
    echo :DeactivateEpilog_Skip
    echo.
    echo call .\Generated\Windows\Python%PYTHON_VERSION%\Scripts\deactivate.bat
    echo call %USERPROFILE%\micromamba\condabin\micromamba.bat deactivate
    echo.
    echo popd
    echo.
    echo echo.
    echo echo [61m[1m%CD%[0m has been [31m[1mdeactivated[0m.
    echo echo.
    echo.
    echo :Exit
    echo exit /B %%_ERRORLEVEL%%
) > Deactivate.cmd

echo [1ACreating Deactivate.cmd...[32m[1mDONE[0m.

@REM ----------------------------------------------------------------------
@REM |
@REM |  Final Output
@REM |
@REM ----------------------------------------------------------------------
echo.
echo.
echo.
echo -----------------------------------------------------------------------
echo -----------------------------------------------------------------------
echo.
echo Your repository has been successfully bootstrapped. Run the following
echo commands to activate and deactivate the local development environment:
echo.
echo   [61m[1mActivate.cmd[0m:    %cd%\[61m[1mActivate.cmd[0m
echo   [61m[1mDeactivate.cmd[0m:  %cd%\[61m[1mDeactivate.cmd[0m
echo.
echo -----------------------------------------------------------------------
echo -----------------------------------------------------------------------
echo.
echo.
echo.

@REM ----------------------------------------------------------------------
@REM |
@REM |  Exit
@REM |
@REM ----------------------------------------------------------------------
:Exit
if exist default_version del default_version
call :_DeleteTempFile

if %_DELETE_ENVIRONMENT_ON_ERROR% EQU 1 (
    echo Removing the micromamba environment...

    rmdir /S /Q "%USERPROFILE%\micromamba\envs\Python%PYTHON_VERSION%"

    if %ERRORLEVEL% NEQ 0 (
        echo [1ARemoving the micromamba environment...[31m[1mFAILED[0m.
    ) else (
        echo [1ARemoving the micromamba environment...[32m[1mDONE[0m.
    )
)

endlocal & exit /B %_ERRORLEVEL%

@REM ----------------------------------------------------------------------
@REM ----------------------------------------------------------------------
@REM ----------------------------------------------------------------------
:_CreateTempFileName
set _BOOTSTRAP_IMPL_TEMP_FILENAME=%CD%BootstrapImpl-!RANDOM!-!Time:~6,5!
goto :EOF

@REM ----------------------------------------------------------------------
:_DeleteTempFile
if "%_BOOTSTRAP_IMPL_TEMP_FILENAME%" NEQ "" (
    if exist "%_BOOTSTRAP_IMPL_TEMP_FILENAME%" (
        del "%_BOOTSTRAP_IMPL_TEMP_FILENAME%"
    )
)
goto :EOF

@REM ----------------------------------------------------------------------
@REM |
@REM |  Bootstrap.cmd
@REM |
@REM |  David Brownell <db@DavidBrownell.com>
@REM |      2023-12-11 14:37:24
@REM |
@REM ----------------------------------------------------------------------
@REM |
@REM |  Copyright David Brownell 2023
@REM |  Distributed under the Boost Software License, Version 1.0. See
@REM |  accompanying file LICENSE_1_0.txt or copy at
@REM |  http://www.boost.org/LICENSE_1_0.txt.
@REM |
@REM ----------------------------------------------------------------------
@if "%1" NEQ "--debug" (
    @echo off
)

@REM ----------------------------------------------------------------------
@REM |
@REM |  This script downloads and invokes BoostrapImpl.cmd from the PythonBootstrapper
@REM |  repository.
@REM |
@REM ----------------------------------------------------------------------

setlocal EnableDelayedExpansion

@REM ----------------------------------------------------------------------
pushd %~dp0

@REM ----------------------------------------------------------------------
@REM |
@REM |  Download BootstrapImpl.cmd
@REM |
@REM ----------------------------------------------------------------------
echo Downloading Bootstrap code...

call :_CreateTempFileName

curl --header "Cache-Control: no-cache, no-store" --header "Pragma: no-cache" --location https://raw.githubusercontent.com/davidbrownell/PythonBootstrapper/main/BootstrapImpl.cmd --output BootstrapImpl.cmd --no-progress-meter --fail-with-body > "%_BOOTSTRAP_TEMP_FILENAME%" 2>&1
set _ERRORLEVEL=%ERRORLEVEL%

if %_ERRORLEVEL% NEQ 0 (
    echo [1ADownloading Bootstrap code...[31m[1mFAILED[0m.
    echo.

    type "%_BOOTSTRAP_TEMP_FILENAME%"
    goto :Exit
)

call :_DeleteTempFile
echo [1ADownloading Bootstrap code...[32m[1mDONE[0m.

@REM ----------------------------------------------------------------------
@REM |
@REM |  Invoke BootstrapImpl.cmd
@REM |
@REM ----------------------------------------------------------------------
call BootstrapImpl.cmd
set _ERRORLEVEL=%ERRORLEVEL%

@REM ----------------------------------------------------------------------
@REM |
@REM |  Exit
@REM |
@REM ----------------------------------------------------------------------
:Exit
if exist BootstrapImpl.cmd del BootstrapImpl.cmd
call :_DeleteTempFile

popd

endlocal
exit /B %_ERRORLEVEL%

@REM ----------------------------------------------------------------------
@REM ----------------------------------------------------------------------
@REM ----------------------------------------------------------------------
:_CreateTempFileName
set _BOOTSTRAP_TEMP_FILENAME=%CD%Bootstrap-!RANDOM!-!Time:~6,5!
goto :EOF

@REM ----------------------------------------------------------------------
:_DeleteTempFile
if "%_BOOTSTRAP_TEMP_FILENAME%" NEQ "" (
    if exist "%_BOOTSTRAP_TEMP_FILENAME%" (
        del "%_BOOTSTRAP_TEMP_FILENAME%"
    )
)
goto :EOF

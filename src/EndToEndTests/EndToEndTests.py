# ----------------------------------------------------------------------
# |
# |  EndToEndTests.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2023-12-12 13:26:43
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2023
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Tests for PythonBootstrapper"""

import os
import re
import shutil
import subprocess
import textwrap

from pathlib import Path
from typing import Callable, Optional

import pytest

# ----------------------------------------------------------------------
INVALID_COMMAND                             = "this is an invalid command"
PYTHON_VERSIONS                             = [
    None, # Use default version
    "3.12",
    "3.11",
    "3.10",
    "3.9",
    "3.8",
]

# ----------------------------------------------------------------------
if os.name.lower() == "nt":
    _extension = ".cmd"
    _home_dir = os.environ["USERPROFILE"]
    _execute_prefix = ""
    _script_version = "0.6.0"
    _init_shell_output = ""
    _source = ""
    _subprocess_executable = None

else:
    _extension = ".sh"
    _home_dir = os.environ["HOME"]
    _execute_prefix = "./"
    _script_version = "0.6.0"
    _init_shell_output = "Initializing the micromamba shell...DONE.\n"
    _source = ". "
    _subprocess_executable = "/bin/bash"


assert _home_dir is not None
micromamba_path = Path(_home_dir) / "micromamba"

# Ensure that Bootstrap has been run at least once. This is required because the output produced by
# micromamba during the first run includes file sizes, download times, and hash values. All of these
# values will be different each time the script is run and when different versions are introduced.
assert micromamba_path.is_dir(), textwrap.dedent(
    """\
    These tests must be run AFTER Bootstrap{ext} has been run successfully at least once.

    To do this, navigate to this directory and run the Bootstrap{ext}.
    """,
).format(
    ext=_extension,
)


# ----------------------------------------------------------------------
@pytest.mark.parametrize("python_version", PYTHON_VERSIONS)
class TestBootstrapEpilog(object):
    # ----------------------------------------------------------------------
    @staticmethod
    def Execute(
        files_to_copy: list[tuple[Path, Path]],
        root: Path,
        expected_output: str | Callable[[str], bool],
        expected_result: int=0,
        arguments: Optional[list[str]]=None,
        *,
        python_version: Optional[str]=None,
    ) -> None:
        if arguments is None:
            arguments = []

        if python_version is not None:
            arguments += ["--python-version", python_version]

        result, output = _Execute(
            files_to_copy,
            root,
            "{}Bootstrap{} {}".format(
                _execute_prefix,
                _extension,
                " ".join('"{}"'.format(arg) for arg in (arguments or [])),
            ),
        )

        if python_version is None:
            output = re.sub(r"Python Version \d+\.\d+", "Python Version None", output)

        assert result == expected_result, (result, output)

        if callable(expected_output):
            assert expected_output(output), output
        elif isinstance(expected_output, str):
            assert output == expected_output, output
        else:
            assert False # pragma: no cover

    # ----------------------------------------------------------------------
    def test_Empty(self, tmp_path_factory, templates_path, python_version):
        root = tmp_path_factory.mktemp("root")

        if python_version is None:
            downloading_default_python_version = "Downloading default python version information...DONE.\n"
        else:
            downloading_default_python_version = ""

        self.Execute(
            [
                (templates_path / f"Bootstrap{_extension}", root / f"Bootstrap{_extension}"),
            ],
            root,
            textwrap.dedent(
                """\
                Downloading Bootstrap code...DONE.

                Script Version {script_version}

                {downloading_default_python_version}Validating python version...DONE.

                Python Version {python_version}

                Downloading micromamba...DONE (already exists).
                Initializing the micromamba environment...DONE (already exists).
                {init_shell_output}Activating the micromamba environment...DONE.
                Creating a python virtual environment...DONE.

                Creating Activate{extension}...DONE.
                Creating Deactivate{extension}...DONE.



                -----------------------------------------------------------------------
                -----------------------------------------------------------------------

                Your repository has been successfully bootstrapped. Run the following
                commands to activate and deactivate the local development environment:

                  Activate{extension}:    {activate}
                  Deactivate{extension}:  {deactivate}

                -----------------------------------------------------------------------
                -----------------------------------------------------------------------



                """,
            ).format(
                script_version=_script_version,
                downloading_default_python_version=downloading_default_python_version,
                python_version=python_version,
                init_shell_output=_init_shell_output,
                extension=_extension,
                activate=(root / "Activate{}".format(_extension)).resolve(),
                deactivate=(root / "Deactivate{}".format(_extension)).resolve(),
            ),
            python_version=python_version,
        )

    # ----------------------------------------------------------------------
    def test_ScriptFile(self, tmp_path_factory, templates_path, python_version):
        root = tmp_path_factory.mktemp("root")

        if python_version is None:
            downloading_default_python_version = "Downloading default python version information...DONE.\n"
        else:
            downloading_default_python_version = ""

        self.Execute(
            [
                (templates_path / f"Bootstrap{_extension}", root / f"Bootstrap{_extension}"),
                (templates_path / f"BootstrapEpilog{_extension}", root / f"BootstrapEpilog{_extension}"),
            ],
            root,
            textwrap.dedent(
                """\
                Downloading Bootstrap code...DONE.

                Script Version {script_version}

                {downloading_default_python_version}Validating python version...DONE.

                Python Version {python_version}

                Downloading micromamba...DONE (already exists).
                Initializing the micromamba environment...DONE (already exists).
                {init_shell_output}Activating the micromamba environment...DONE.
                Creating a python virtual environment...DONE.

                Hello from BootstrapEpilog{extension}

                Creating Activate{extension}...DONE.
                Creating Deactivate{extension}...DONE.



                -----------------------------------------------------------------------
                -----------------------------------------------------------------------

                Your repository has been successfully bootstrapped. Run the following
                commands to activate and deactivate the local development environment:

                  Activate{extension}:    {activate}
                  Deactivate{extension}:  {deactivate}

                -----------------------------------------------------------------------
                -----------------------------------------------------------------------



                """,
            ).format(
                script_version=_script_version,
                downloading_default_python_version=downloading_default_python_version,
                python_version=python_version,
                init_shell_output=_init_shell_output,
                extension=_extension,
                activate=(root / "Activate{}".format(_extension)).resolve(),
                deactivate=(root / "Deactivate{}".format(_extension)).resolve(),
            ),
            python_version=python_version,
        )

    # ----------------------------------------------------------------------
    def test_PythonFile(self, tmp_path_factory, templates_path, python_version):
        root = tmp_path_factory.mktemp("root")

        if python_version is None:
            downloading_default_python_version = "Downloading default python version information...DONE.\n"
        else:
            downloading_default_python_version = ""

        self.Execute(
            [
                (templates_path / f"Bootstrap{_extension}", root / f"Bootstrap{_extension}"),
                (templates_path / "BootstrapEpilog.py", root / "BootstrapEpilog.py"),
            ],
            root,
            textwrap.dedent(
                """\
                Downloading Bootstrap code...DONE.

                Script Version {script_version}

                {downloading_default_python_version}Validating python version...DONE.

                Python Version {python_version}

                Downloading micromamba...DONE (already exists).
                Initializing the micromamba environment...DONE (already exists).
                {init_shell_output}Activating the micromamba environment...DONE.
                Creating a python virtual environment...DONE.

                Hello from BootstrapEpilog.py
                Arguments
                  - BootstrapEpilog_py{extension}
                Hello from BootstrapEpilog.py output

                Creating Activate{extension}...DONE.
                Creating Deactivate{extension}...DONE.



                -----------------------------------------------------------------------
                -----------------------------------------------------------------------

                Your repository has been successfully bootstrapped. Run the following
                commands to activate and deactivate the local development environment:

                  Activate{extension}:    {activate}
                  Deactivate{extension}:  {deactivate}

                -----------------------------------------------------------------------
                -----------------------------------------------------------------------



                """,
            ).format(
                script_version=_script_version,
                downloading_default_python_version=downloading_default_python_version,
                python_version=python_version,
                init_shell_output=_init_shell_output,
                extension=_extension,
                activate=(root / "Activate{}".format(_extension)).resolve(),
                deactivate=(root / "Deactivate{}".format(_extension)).resolve(),
            ),
            python_version=python_version,
        )

    # ----------------------------------------------------------------------
    def test_ScriptAndPythonFiles(self, tmp_path_factory, templates_path, python_version):
        root = tmp_path_factory.mktemp("root")

        if python_version is None:
            downloading_default_python_version = "Downloading default python version information...DONE.\n"
        else:
            downloading_default_python_version = ""

        self.Execute(
            [
                (templates_path / f"Bootstrap{_extension}", root / f"Bootstrap{_extension}"),
                (templates_path / f"BootstrapEpilog{_extension}", root / f"BootstrapEpilog{_extension}"),
                (templates_path / "BootstrapEpilog.py", root / "BootstrapEpilog.py"),
            ],
            root,
            textwrap.dedent(
                """\
                Downloading Bootstrap code...DONE.

                Script Version {script_version}

                {downloading_default_python_version}Validating python version...DONE.

                Python Version {python_version}

                Downloading micromamba...DONE (already exists).
                Initializing the micromamba environment...DONE (already exists).
                {init_shell_output}Activating the micromamba environment...DONE.
                Creating a python virtual environment...DONE.

                Hello from BootstrapEpilog{extension}
                Hello from BootstrapEpilog.py
                Arguments
                  - BootstrapEpilog_py{extension}
                Hello from BootstrapEpilog.py output

                Creating Activate{extension}...DONE.
                Creating Deactivate{extension}...DONE.



                -----------------------------------------------------------------------
                -----------------------------------------------------------------------

                Your repository has been successfully bootstrapped. Run the following
                commands to activate and deactivate the local development environment:

                  Activate{extension}:    {activate}
                  Deactivate{extension}:  {deactivate}

                -----------------------------------------------------------------------
                -----------------------------------------------------------------------



                """,
            ).format(
                script_version=_script_version,
                downloading_default_python_version=downloading_default_python_version,
                python_version=python_version,
                init_shell_output=_init_shell_output,
                extension=_extension,
                activate=(root / "Activate{}".format(_extension)).resolve(),
                deactivate=(root / "Deactivate{}".format(_extension)).resolve(),
            ),
            python_version=python_version,
        )

    # ----------------------------------------------------------------------
    def test_ScriptError(self, tmp_path_factory, templates_path, python_version):
        root = tmp_path_factory.mktemp("root")

        script_filename = root / f"BootstrapEpilog{_extension}"
        with script_filename.open("w") as f:
            f.write(INVALID_COMMAND)

        script_filename.chmod(0o755)

        if python_version is None:
            downloading_default_python_version = "Downloading default python version information...DONE.\n"
        else:
            downloading_default_python_version = ""

        # ----------------------------------------------------------------------
        def IsValid(output: str) -> bool:
            return (
                output.startswith(
                    textwrap.dedent(
                        """\
                        Downloading Bootstrap code...DONE.

                        Script Version {script_version}

                        {downloading_default_python_version}Validating python version...DONE.

                        Python Version {python_version}

                        Downloading micromamba...DONE (already exists).
                        Initializing the micromamba environment...DONE (already exists).
                        {init_shell_output}Activating the micromamba environment...DONE.
                        Creating a python virtual environment...DONE.

                        """,
                    ).format(
                        script_version=_script_version,
                        downloading_default_python_version=downloading_default_python_version,
                        python_version=python_version,
                        init_shell_output=_init_shell_output,
                    ),
                )
                and output.endswith(
                    textwrap.dedent(
                        """\
                        ERROR: BootstrapEpilog{extension} failed.
                        """,
                    ).format(
                        extension=_extension,
                    ),
                ),
            )

        # ----------------------------------------------------------------------

        self.Execute(
            [
                (templates_path / f"Bootstrap{_extension}", root / f"Bootstrap{_extension}"),
            ],
            root,
            IsValid,
            expected_result=_error_result,
            python_version=python_version,
        )

    # ----------------------------------------------------------------------
    def test_PythonError(self, tmp_path_factory, templates_path, python_version):
        root = tmp_path_factory.mktemp("root")

        with (root / f"BootstrapEpilog.py").open("w") as f:
            f.write(
                textwrap.dedent(
                    """\
                    import sys
                    sys.exit(2)
                    """,
                ),
            )

        if python_version is None:
            downloading_default_python_version = "Downloading default python version information...DONE.\n"
        else:
            downloading_default_python_version = ""

        self.Execute(
            [
                (templates_path / f"Bootstrap{_extension}", root / f"Bootstrap{_extension}"),
            ],
            root,
            textwrap.dedent(
                """\
                Downloading Bootstrap code...DONE.

                Script Version {script_version}

                {downloading_default_python_version}Validating python version...DONE.

                Python Version {python_version}

                Downloading micromamba...DONE (already exists).
                Initializing the micromamba environment...DONE (already exists).
                {init_shell_output}Activating the micromamba environment...DONE.
                Creating a python virtual environment...DONE.

                ERROR: BootstrapEpilog.py failed.
                """,
            ).format(
                script_version=_script_version,
                downloading_default_python_version=downloading_default_python_version,
                python_version=python_version,
                init_shell_output=_init_shell_output,
            ),
            expected_result=2,
            python_version=python_version,
        )

    # ----------------------------------------------------------------------
    def test_PythonResultError(self, tmp_path_factory, templates_path, python_version):
        root = tmp_path_factory.mktemp("root")

        with (root / f"BootstrapEpilog.py").open("w") as f:
            f.write(
                textwrap.dedent(
                    """\
                    import sys

                    from pathlib import Path

                    with Path(sys.argv[1]).open("w") as f:
                        f.write("{}")
                    """,
                ).format(INVALID_COMMAND.replace("\n", "\\n")),
            )

        if python_version is None:
            downloading_default_python_version = "Downloading default python version information...DONE.\n"
        else:
            downloading_default_python_version = ""

        # ----------------------------------------------------------------------
        def IsValid(output: str) -> bool:
            return (
                output.startswith(
                    textwrap.dedent(
                        """\
                        Downloading Bootstrap code...DONE.

                        Script Version {script_version}

                        {downloading_default_python_version}Validating python version...DONE.

                        Python Version {python_version}

                        Downloading micromamba...DONE (already exists).
                        Initializing the micromamba environment...DONE (already exists).
                        {init_shell_output}Activating the micromamba environment...DONE.
                        Creating a python virtual environment...DONE.

                        """,
                    ).format(
                        script_version=_script_version,
                        downloading_default_python_version=downloading_default_python_version,
                        python_version=python_version,
                        init_shell_output=_init_shell_output,
                    ),
                )
                and output.endswith(
                    textwrap.dedent(
                        """\
                        ERROR: Executing the BootstrapEpilog.py output failed.
                        """,
                    ),
                )
            )

        self.Execute(
            [
                (templates_path / f"Bootstrap{_extension}", root / f"Bootstrap{_extension}"),
            ],
            root,
            IsValid,
            expected_result=_error_result,
            python_version=python_version,
        )

    # ----------------------------------------------------------------------
    def test_Arguments(self, tmp_path_factory, templates_path, python_version):
        root = tmp_path_factory.mktemp("root")

        if python_version is None:
            downloading_default_python_version = "Downloading default python version information...DONE.\n"
        else:
            downloading_default_python_version = ""

        self.Execute(
            [
                (templates_path / f"Bootstrap{_extension}", root / f"Bootstrap{_extension}"),
                (templates_path / "BootstrapEpilog.py", root / "BootstrapEpilog.py"),
            ],
            root,
            textwrap.dedent(
                """\
                Downloading Bootstrap code...DONE.

                Script Version {script_version}

                {downloading_default_python_version}Validating python version...DONE.

                Python Version {python_version}

                Downloading micromamba...DONE (already exists).
                Initializing the micromamba environment...DONE (already exists).
                {init_shell_output}Activating the micromamba environment...DONE.
                Creating a python virtual environment...DONE.

                Hello from BootstrapEpilog.py
                Arguments
                  - BootstrapEpilog_py{extension}
                  - 1
                  - two three
                  - 4
                  - --five
                Hello from BootstrapEpilog.py output

                Creating Activate{extension}...DONE.
                Creating Deactivate{extension}...DONE.



                -----------------------------------------------------------------------
                -----------------------------------------------------------------------

                Your repository has been successfully bootstrapped. Run the following
                commands to activate and deactivate the local development environment:

                  Activate{extension}:    {activate}
                  Deactivate{extension}:  {deactivate}

                -----------------------------------------------------------------------
                -----------------------------------------------------------------------



                """,
            ).format(
                script_version=_script_version,
                downloading_default_python_version=downloading_default_python_version,
                python_version=python_version,
                init_shell_output=_init_shell_output,
                extension=_extension,
                activate=(root / "Activate{}".format(_extension)).resolve(),
                deactivate=(root / "Deactivate{}".format(_extension)).resolve(),
            ),
            arguments=[
                "1",
                "two three",
                "4",
                "--five",
            ],
            python_version=python_version,
        )


# ----------------------------------------------------------------------
@pytest.mark.parametrize("python_version", PYTHON_VERSIONS)
class TestActivateEpilog(object):
    # ----------------------------------------------------------------------
    @staticmethod
    def Execute(
        files_to_copy: list[tuple[Path, Path]],
        root: Path,
        expected_output: str | Callable[[str], bool],
        expected_result: int=0,
        arguments: Optional[list[str]]=None,
        python_version: Optional[str]=None,
    ) -> None:
        if python_version is not None:
            python_version_arg = " --python-version {}".format(python_version)
        else:
            python_version_arg = ""

        result, output = _Execute(
            files_to_copy,
            root,
            "{}Bootstrap{}{}".format(_execute_prefix, _extension, python_version_arg),
        )
        assert result == 0, output

        result, output = _Execute(
            [],
            root,
            "{}{}Activate{} {}".format(
                _source,
                _execute_prefix,
                _extension,
                " ".join('"{}"'.format(arg) for arg in (arguments or [])),
            ),
        )

        assert result == expected_result, (result, output)

        if callable(expected_output):
            assert expected_output(output), output
        elif isinstance(expected_output, str):
            assert output == expected_output, output
        else:
            assert False # pragma: no cover

    # ----------------------------------------------------------------------
    def test_Empty(self, tmp_path_factory, templates_path, python_version):
        root = tmp_path_factory.mktemp("root")

        self.Execute(
            [
                (templates_path / f"Bootstrap{_extension}", root / f"Bootstrap{_extension}"),
            ],
            root,
            textwrap.dedent(
                """\

                {} has been activated.

                """,
            ).format(root),
            python_version=python_version,
        )

    # ----------------------------------------------------------------------
    def test_ScriptFile(self, tmp_path_factory, templates_path, python_version):
        root = tmp_path_factory.mktemp("root")

        self.Execute(
            [
                (templates_path / f"Bootstrap{_extension}", root / f"Bootstrap{_extension}"),
                (templates_path / f"ActivateEpilog{_extension}", root / f"ActivateEpilog{_extension}"),
            ],
            root,
            textwrap.dedent(
                """\
                Hello from ActivateEpilog{extension}

                {root} has been activated.

                """,
            ).format(
                extension=_extension,
                root=root,
            ),
            python_version=python_version,
        )

    # ----------------------------------------------------------------------
    def test_PythonFile(self, tmp_path_factory, templates_path, python_version):
        root = tmp_path_factory.mktemp("root")

        self.Execute(
            [
                (templates_path / f"Bootstrap{_extension}", root / f"Bootstrap{_extension}"),
                (templates_path / "ActivateEpilog.py", root / "ActivateEpilog.py"),
            ],
            root,
            textwrap.dedent(
                """\
                Hello from ActivateEpilog.py
                Arguments
                  - ActivateEpilog_py{extension}
                Hello from ActivateEpilog.py output!

                {root} has been activated.

                """,
            ).format(
                extension=_extension,
                root=root,
            ),
            python_version=python_version,
        )

    # ----------------------------------------------------------------------
    def test_ScriptAndPythonFiles(self, tmp_path_factory, templates_path, python_version):
        root = tmp_path_factory.mktemp("root")

        self.Execute(
            [
                (templates_path / f"Bootstrap{_extension}", root / f"Bootstrap{_extension}"),
                (templates_path / f"ActivateEpilog{_extension}", root / f"ActivateEpilog{_extension}"),
                (templates_path / "ActivateEpilog.py", root / "ActivateEpilog.py"),
            ],
            root,
            textwrap.dedent(
                """\
                Hello from ActivateEpilog{extension}
                Hello from ActivateEpilog.py
                Arguments
                  - ActivateEpilog_py{extension}
                Hello from ActivateEpilog.py output!

                {root} has been activated.

                """,
            ).format(
                extension=_extension,
                root=root,
            ),
            python_version=python_version,
        )

    # ----------------------------------------------------------------------
    def test_ScriptError(self, tmp_path_factory, templates_path, python_version):
        root = tmp_path_factory.mktemp("root")

        script_filename = root / f"ActivateEpilog{_extension}"
        with script_filename.open("w") as f:
            f.write(INVALID_COMMAND)

        script_filename.chmod(0o755)

        # ----------------------------------------------------------------------
        def IsValid(output: str) -> bool:
            return output.endswith(
                textwrap.dedent(
                    """\
                    ERROR: ActivateEpilog{extension} failed.
                    """,
                ).format(
                    extension=_extension,
                ),
            )

        # ----------------------------------------------------------------------

        self.Execute(
            [
                (templates_path / f"Bootstrap{_extension}", root / f"Bootstrap{_extension}"),
            ],
            root,
            IsValid,
            expected_result=_error_result,
            python_version=python_version,
        )

    # ----------------------------------------------------------------------
    def test_PythonError(self, tmp_path_factory, templates_path, python_version):
        root = tmp_path_factory.mktemp("root")

        with (root / f"ActivateEpilog.py").open("w") as f:
            f.write(
                textwrap.dedent(
                    """\
                    import sys
                    sys.exit(2)
                    """,
                ),
            )

        self.Execute(
            [
                (templates_path / f"Bootstrap{_extension}", root / f"Bootstrap{_extension}"),
            ],
            root,
            textwrap.dedent(
                """\
                ERROR: ActivateEpilog.py failed.
                """,
            ),
            expected_result=2,
            python_version=python_version,
        )

    # ----------------------------------------------------------------------
    def test_PythonResultError(self, tmp_path_factory, templates_path, python_version):
        root = tmp_path_factory.mktemp("root")

        with (root / f"ActivateEpilog.py").open("w") as f:
            f.write(
                textwrap.dedent(
                    """\
                    import sys
                    from pathlib import Path

                    with Path(sys.argv[1]).open("w") as f:
                        f.write("{}")
                    """,
                ).format(INVALID_COMMAND.replace("\n", "\\n")),
            )

        # ----------------------------------------------------------------------
        def IsValid(output: str) -> bool:
            return output.endswith(
                textwrap.dedent(
                    """\
                    ERROR: Executing the ActivateEpilog.py output failed.
                    """,
                ),
            )

        # ----------------------------------------------------------------------

        self.Execute(
            [
                (templates_path / f"Bootstrap{_extension}", root / f"Bootstrap{_extension}"),
            ],
            root,
            IsValid,
            expected_result=_error_result,
            python_version=python_version,
        )

    # ----------------------------------------------------------------------
    def test_Arguments(self, tmp_path_factory, templates_path, python_version):
        root = tmp_path_factory.mktemp("root")

        self.Execute(
            [
                (templates_path / f"Bootstrap{_extension}", root / f"Bootstrap{_extension}"),
                (templates_path / "ActivateEpilog.py", root / "ActivateEpilog.py"),
            ],
            root,
            textwrap.dedent(
                """\
                Hello from ActivateEpilog.py
                Arguments
                  - ActivateEpilog_py{extension}
                  - 1
                  - two three
                  - 4
                  - --five
                Hello from ActivateEpilog.py output!

                {root} has been activated.

                """,
            ).format(
                extension=_extension,
                root=root,
            ),
            arguments=[
                "1",
                "two three",
                "4",
                "--five",
            ],
            python_version=python_version,
        )


# ----------------------------------------------------------------------
@pytest.mark.parametrize("python_version", PYTHON_VERSIONS)
class TestDeactivateEpilog(object):
    # ----------------------------------------------------------------------
    @staticmethod
    def Execute(
        files_to_copy: list[tuple[Path, Path]],
        root: Path,
        expected_output: str | Callable[[str], bool],
        expected_result: int=0,
        arguments: Optional[list[str]]=None,
        python_version: Optional[str]=None,
    ) -> None:
        if python_version is not None:
            python_version_arg = " --python-version {}".format(python_version)
        else:
            python_version_arg = ""

        result, output = _Execute(
            files_to_copy,
            root,
            "{}Bootstrap{}{}".format(_execute_prefix, _extension, python_version_arg),
        )
        assert result == 0, output

        result, output = _Execute(
            [],
            root,
            "{source}{execute_prefix}Activate{extension} && {source}{execute_prefix}Deactivate{extension} {args}".format(
                source=_source,
                execute_prefix=_execute_prefix,
                extension=_extension,
                args=" ".join('"{}"'.format(arg) for arg in (arguments or [])),
            ),
        )

        assert result == expected_result, (result, output)

        if callable(expected_output):
            assert expected_output(output), output
        elif isinstance(expected_output, str):
            assert output == expected_output, output
        else:
            assert False # pragma: no cover

    # ----------------------------------------------------------------------
    def test_Empty(self, tmp_path_factory, templates_path, python_version):
        root = tmp_path_factory.mktemp("root")

        self.Execute(
            [
                (templates_path / f"Bootstrap{_extension}", root / f"Bootstrap{_extension}"),
            ],
            root,
            textwrap.dedent(
                """\

                {root} has been activated.


                {root} has been deactivated.

                """,
            ).format(root=root),
            python_version=python_version,
        )

    # ----------------------------------------------------------------------
    def test_ScriptFile(self, tmp_path_factory, templates_path, python_version):
        root = tmp_path_factory.mktemp("root")

        self.Execute(
            [
                (templates_path / f"Bootstrap{_extension}", root / f"Bootstrap{_extension}"),
                (templates_path / f"DeactivateEpilog{_extension}", root / f"DeactivateEpilog{_extension}"),
            ],
            root,
            textwrap.dedent(
                """\

                {root} has been activated.

                Hello from DeactivateEpilog{extension}

                {root} has been deactivated.

                """,
            ).format(
                extension=_extension,
                root=root,
            ),
            python_version=python_version,
        )

    # ----------------------------------------------------------------------
    def test_PythonFile(self, tmp_path_factory, templates_path, python_version):
        root = tmp_path_factory.mktemp("root")

        self.Execute(
            [
                (templates_path / f"Bootstrap{_extension}", root / f"Bootstrap{_extension}"),
                (templates_path / "DeactivateEpilog.py", root / "DeactivateEpilog.py"),
            ],
            root,
            textwrap.dedent(
                """\

                {root} has been activated.

                Hello from DeactivateEpilog.py
                Arguments
                  - DeactivateEpilog_py{extension}
                Hello from DeactivateEpilog.py output!

                {root} has been deactivated.

                """,
            ).format(
                extension=_extension,
                root=root,
            ),
            python_version=python_version,
        )

    # ----------------------------------------------------------------------
    def test_ScriptAndPythonFiles(self, tmp_path_factory, templates_path, python_version):
        root = tmp_path_factory.mktemp("root")

        self.Execute(
            [
                (templates_path / f"Bootstrap{_extension}", root / f"Bootstrap{_extension}"),
                (templates_path / f"DeactivateEpilog{_extension}", root / f"DeactivateEpilog{_extension}"),
                (templates_path / "DeactivateEpilog.py", root / "DeactivateEpilog.py"),
            ],
            root,
            textwrap.dedent(
                """\

                {root} has been activated.

                Hello from DeactivateEpilog{extension}
                Hello from DeactivateEpilog.py
                Arguments
                  - DeactivateEpilog_py{extension}
                Hello from DeactivateEpilog.py output!

                {root} has been deactivated.

                """,
            ).format(
                extension=_extension,
                root=root,
            ),
            python_version=python_version,
        )

    # ----------------------------------------------------------------------
    def test_ScriptError(self, tmp_path_factory, templates_path, python_version):
        root = tmp_path_factory.mktemp("root")

        script_filename = root / f"DeactivateEpilog{_extension}"
        with script_filename.open("w") as f:
            f.write(INVALID_COMMAND)

        script_filename.chmod(0o755)

        # ----------------------------------------------------------------------
        def IsValid(output: str) -> bool:
            return (
                output.startswith(
                    textwrap.dedent(
                        """\

                        {root} has been activated.

                        """,
                    ).format(
                        root=root,
                    ),
                )
                and output.endswith(
                    textwrap.dedent(
                        """\
                        ERROR: DeactivateEpilog{extension} failed.
                        """,
                    ).format(
                        extension=_extension,
                    ),
                )
            )

        # ----------------------------------------------------------------------

        self.Execute(
            [
                (templates_path / f"Bootstrap{_extension}", root / f"Bootstrap{_extension}"),
            ],
            root,
            IsValid,
            expected_result=_error_result,
            python_version=python_version,
        )

    # ----------------------------------------------------------------------
    def test_PythonError(self, tmp_path_factory, templates_path, python_version):
        root = tmp_path_factory.mktemp("root")

        with (root / f"DeactivateEpilog.py").open("w") as f:
            f.write(
                textwrap.dedent(
                    """\
                    import sys
                    sys.exit(2)
                    """,
                ),
            )

        self.Execute(
            [
                (templates_path / f"Bootstrap{_extension}", root / f"Bootstrap{_extension}"),
            ],
            root,
            textwrap.dedent(
                """\

                {root} has been activated.

                ERROR: DeactivateEpilog.py failed.
                """,
            ).format(
                root=root,
            ),
            expected_result=2,
            python_version=python_version,
        )

    # ----------------------------------------------------------------------
    def test_PythonResultError(self, tmp_path_factory, templates_path, python_version):
        root = tmp_path_factory.mktemp("root")

        with (root / f"DeactivateEpilog.py").open("w") as f:
            f.write(
                textwrap.dedent(
                    """\
                    import sys
                    from pathlib import Path

                    with Path(sys.argv[1]).open("w") as f:
                        f.write("{}")
                    """,
                ).format(INVALID_COMMAND.replace("\n", "\\n")),
            )

        # ----------------------------------------------------------------------
        def IsValid(output: str) -> bool:
            return (
                output.startswith(
                    textwrap.dedent(
                        """\

                        {root} has been activated.

                        """,
                    ).format(
                        root=root,
                    ),
                )
                and output.endswith(
                    textwrap.dedent(
                        """\
                        ERROR: Executing the DeactivateEpilog.py output failed.
                        """,
                    ),
                )
            )

        # ----------------------------------------------------------------------

        self.Execute(
            [
                (templates_path / f"Bootstrap{_extension}", root / f"Bootstrap{_extension}"),
            ],
            root,
            IsValid,
            expected_result=_error_result,
            python_version=python_version,
        )

    # ----------------------------------------------------------------------
    def test_Arguments(self, tmp_path_factory, templates_path, python_version):
        root = tmp_path_factory.mktemp("root")

        self.Execute(
            [
                (templates_path / f"Bootstrap{_extension}", root / f"Bootstrap{_extension}"),
                (templates_path / "DeactivateEpilog.py", root / "DeactivateEpilog.py"),
            ],
            root,
            textwrap.dedent(
                """\

                {root} has been activated.

                Hello from DeactivateEpilog.py
                Arguments
                  - DeactivateEpilog_py{extension}
                  - 1
                  - two three
                  - 4
                  - --five
                Hello from DeactivateEpilog.py output!

                {root} has been deactivated.

                """,
            ).format(
                extension=_extension,
                root=root,
            ),
            arguments=[
                "1",
                "two three",
                "4",
                "--five",
            ],
            python_version=python_version,
        )



# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _Execute(
    files_to_copy: list[tuple[Path, Path]],
    root: Path,
    command: str,
) -> tuple[int, str]:
    for source, dest in files_to_copy:
        shutil.copyfile(source, dest)

        if dest.suffix == _extension:
            dest.chmod(0o755)

    result = subprocess.run(
        command,
        check=False,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=root,
        executable=_subprocess_executable,
    )

    content = result.stdout.decode("utf-8")

    # Remove lines eventually replaced by DONE-style messages
    content = re.sub(
        r"^[^\n]+\r?\n\x1b\[1A",
        "",
        content,
        flags=re.MULTILINE,
    )

    # Remove escape sequences
    content = re.sub(r"\x1b\[\d+[Am]", "", content)

    # Remove CRs
    content = content.replace("\r", "")

    return result.returncode, content


# ----------------------------------------------------------------------
@pytest.fixture
def templates_path() -> Path:
    result = Path(__file__).parent.parent.parent / "Templates"

    assert result.is_dir(), result
    return result


# ----------------------------------------------------------------------
_error_result = _Execute([], Path(__file__).parent, INVALID_COMMAND)[0]

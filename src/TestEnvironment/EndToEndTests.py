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

import pytest


# ----------------------------------------------------------------------
if os.name.lower() == "nt":
    _is_windows = True
    _extension = ".cmd"

    user_profile = os.environ["USERPROFILE"]
    assert user_profile is not None

    micromamba_path = Path(user_profile) / "micromamba"

else:
    _is_windows = False
    _extension = ".sh"


# Ensure that Bootstrap has been run at least once. This is required because the output produced by
# micromamba during the first run includes file sizes, download times, and hash values. All of these
# values will be different each time the script is run and when different versions are introduced.
assert micromamba_path.is_dir(), textwrap.dedent(
    """\
    These tests must be run AFTER Bootstrap.cmd has been run successfully at least once.

    To do this, navigate to `../../Templates` and run the Bootstrap script that corresponds to
    your operating system.
    """,
)


# ----------------------------------------------------------------------
class TestBootstrapEpilog(object):
    # ----------------------------------------------------------------------
    def Execute(
        self,
        files_to_copy: list[tuple[Path, Path]],
        root: Path,
        expected_output: str,
        expected_result: int=0,
    ) -> None:
        result, output = _Execute(files_to_copy, root, "Bootstrap{}".format(_extension))

        assert result == expected_result, (result, output)
        assert output == expected_output, output

    # ----------------------------------------------------------------------
    def test_Empty(self, tmp_path_factory, templates_path):
        root = tmp_path_factory.mktemp("root")

        self.Execute(
            [
                (templates_path / f"Bootstrap{_extension}", root / f"Bootstrap{_extension}"),
            ],
            root,
            textwrap.dedent(
                """\
                Downloading Bootstrap code...DONE.

                Version 0.7.1

                Downloading default python version information...DONE.
                Validating python version...DONE.
                Downloading micromamba...DONE (already exists).
                Initializing the micromamba environment...DONE (already exists).
                Activating the micromamba environment...DONE.
                Creating a python virtual environment...DONE.
                Creating Activate.cmd...DONE.
                Creating Deactivate.cmd...DONE.



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
                extension=_extension,
                activate=(root / "Activate{}".format(_extension)).resolve(),
                deactivate=(root / "Deactivate{}".format(_extension)).resolve(),
            ),
        )

    # ----------------------------------------------------------------------
    def test_ScriptFile(self, tmp_path_factory, templates_path):
        root = tmp_path_factory.mktemp("root")

        self.Execute(
            [
                (templates_path / f"Bootstrap{_extension}", root / f"Bootstrap{_extension}"),
                (templates_path / f"BootstrapEpilog{_extension}", root / f"BootstrapEpilog{_extension}"),
            ],
            root,
            textwrap.dedent(
                """\
                Downloading Bootstrap code...DONE.

                Version 0.7.1

                Downloading default python version information...DONE.
                Validating python version...DONE.
                Downloading micromamba...DONE (already exists).
                Initializing the micromamba environment...DONE (already exists).
                Activating the micromamba environment...DONE.
                Creating a python virtual environment...DONE.

                Hello from BootstrapEpilog{extension}

                Creating Activate.cmd...DONE.
                Creating Deactivate.cmd...DONE.



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
                extension=_extension,
                activate=(root / "Activate{}".format(_extension)).resolve(),
                deactivate=(root / "Deactivate{}".format(_extension)).resolve(),
            ),
        )

    # ----------------------------------------------------------------------
    def test_PythonFile(self, tmp_path_factory, templates_path):
        root = tmp_path_factory.mktemp("root")

        self.Execute(
            [
                (templates_path / f"Bootstrap{_extension}", root / f"Bootstrap{_extension}"),
                (templates_path / "BootstrapEpilog.py", root / "BootstrapEpilog.py"),
            ],
            root,
            textwrap.dedent(
                """\
                Downloading Bootstrap code...DONE.

                Version 0.7.1

                Downloading default python version information...DONE.
                Validating python version...DONE.
                Downloading micromamba...DONE (already exists).
                Initializing the micromamba environment...DONE (already exists).
                Activating the micromamba environment...DONE.
                Creating a python virtual environment...DONE.

                Hello from BootstrapEpilog.py

                Creating Activate.cmd...DONE.
                Creating Deactivate.cmd...DONE.



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
                extension=_extension,
                activate=(root / "Activate{}".format(_extension)).resolve(),
                deactivate=(root / "Deactivate{}".format(_extension)).resolve(),
            ),
        )

    # ----------------------------------------------------------------------
    def test_ScriptAndPythonFiles(self, tmp_path_factory, templates_path):
        root = tmp_path_factory.mktemp("root")

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

                Version 0.7.1

                Downloading default python version information...DONE.
                Validating python version...DONE.
                Downloading micromamba...DONE (already exists).
                Initializing the micromamba environment...DONE (already exists).
                Activating the micromamba environment...DONE.
                Creating a python virtual environment...DONE.

                Hello from BootstrapEpilog{extension}
                Hello from BootstrapEpilog.py

                Creating Activate.cmd...DONE.
                Creating Deactivate.cmd...DONE.



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
                extension=_extension,
                activate=(root / "Activate{}".format(_extension)).resolve(),
                deactivate=(root / "Deactivate{}".format(_extension)).resolve(),
            ),
        )

    # ----------------------------------------------------------------------
    def test_ScriptError(self, tmp_path_factory, templates_path):
        root = tmp_path_factory.mktemp("root")

        with (root / f"BootstrapEpilog{_extension}").open("w") as f:
            f.write("this is an invalid command")

        if _is_windows:
            error = textwrap.dedent(
                """\
                'this' is not recognized as an internal or external command,
                operable program or batch file.
                ERROR: BootstrapEpilog.cmd failed.
                """,
            ).rstrip()

            expected_result = 1

        else:
            assert False

        self.Execute(
            [
                (templates_path / f"Bootstrap{_extension}", root / f"Bootstrap{_extension}"),
            ],
            root,
            textwrap.dedent(
                """\
                Downloading Bootstrap code...DONE.

                Version 0.7.1

                Downloading default python version information...DONE.
                Validating python version...DONE.
                Downloading micromamba...DONE (already exists).
                Initializing the micromamba environment...DONE (already exists).
                Activating the micromamba environment...DONE.
                Creating a python virtual environment...DONE.

                {error}
                """,
            ).format(
                error=error,
            ),
            expected_result=expected_result,
        )

    # ----------------------------------------------------------------------
    def test_PythonError(self, tmp_path_factory, templates_path):
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

        self.Execute(
            [
                (templates_path / f"Bootstrap{_extension}", root / f"Bootstrap{_extension}"),
            ],
            root,
            textwrap.dedent(
                """\
                Downloading Bootstrap code...DONE.

                Version 0.7.1

                Downloading default python version information...DONE.
                Validating python version...DONE.
                Downloading micromamba...DONE (already exists).
                Initializing the micromamba environment...DONE (already exists).
                Activating the micromamba environment...DONE.
                Creating a python virtual environment...DONE.

                ERROR: BootstrapEpilog.py failed.
                """,
            ),
            expected_result=2,
        )


# ----------------------------------------------------------------------
class TestActivateEpilog(object):
    # ----------------------------------------------------------------------
    def Execute(
        self,
        files_to_copy: list[tuple[Path, Path]],
        root: Path,
        expected_output: str,
        expected_result: int=0,
    ) -> None:
        result, output = _Execute(files_to_copy, root, "Bootstrap{}".format(_extension))
        assert result == 0, output

        result, output = _Execute([], root, "Activate{}".format(_extension))
        assert result == expected_result, (result, output)
        assert output == expected_output, output

    # ----------------------------------------------------------------------
    def test_Empty(self, tmp_path_factory, templates_path):
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
        )

    # ----------------------------------------------------------------------
    def test_ScriptFile(self, tmp_path_factory, templates_path):
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
        )

    # ----------------------------------------------------------------------
    def test_PythonFile(self, tmp_path_factory, templates_path):
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
                Hello from ActivateEpilog_py{extension}

                {root} has been activated.

                """,
            ).format(
                extension=_extension,
                root=root,
            ),
        )

    # ----------------------------------------------------------------------
    def test_ScriptAndPythonFiles(self, tmp_path_factory, templates_path):
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
                Hello from ActivateEpilog_py{extension}

                {root} has been activated.

                """,
            ).format(
                extension=_extension,
                root=root,
            ),
        )

    # ----------------------------------------------------------------------
    def test_ScriptError(self, tmp_path_factory, templates_path):
        root = tmp_path_factory.mktemp("root")

        with (root / f"ActivateEpilog{_extension}").open("w") as f:
            f.write("this is an invalid command")

        if _is_windows:
            error = textwrap.dedent(
                """\
                'this' is not recognized as an internal or external command,
                operable program or batch file.
                """,
            ).rstrip()

            expected_result = 1

        else:
            assert False

        self.Execute(
            [
                (templates_path / f"Bootstrap{_extension}", root / f"Bootstrap{_extension}"),
            ],
            root,
            textwrap.dedent(
                """\
                {error}
                ERROR: ActivateEpilog{extension} failed.
                """,
            ).format(
                error=error,
                extension=_extension,
            ),
            expected_result=expected_result,
        )

    # ----------------------------------------------------------------------
    def test_PythonError(self, tmp_path_factory, templates_path):
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
        )

    # ----------------------------------------------------------------------
    def test_PythonResultError(self, tmp_path_factory, templates_path):
        root = tmp_path_factory.mktemp("root")

        with (root / f"ActivateEpilog.py").open("w") as f:
            f.write(
                textwrap.dedent(
                    """\
                    import sys
                    from pathlib import Path

                    with Path(sys.argv[1]).open("w") as f:
                        f.write("this is an invalid command")
                    """,
                ),
            )

        if _is_windows:
            error = textwrap.dedent(
                """\
                'this' is not recognized as an internal or external command,
                operable program or batch file.
                """,
            ).rstrip()

            expected_result = 1
        else:
            assert False

        self.Execute(
            [
                (templates_path / f"Bootstrap{_extension}", root / f"Bootstrap{_extension}"),
            ],
            root,
            textwrap.dedent(
                """\
                {}
                ERROR: Executing the ActivateEpilog.py output failed.
                """,
            ).format(error),
            expected_result=expected_result,
        )


# ----------------------------------------------------------------------
class TestDeactivateEpilog(object):
    # ----------------------------------------------------------------------
    def Execute(
        self,
        files_to_copy: list[tuple[Path, Path]],
        root: Path,
        expected_output: str,
        expected_result: int=0,
    ) -> None:
        result, output = _Execute(files_to_copy, root, "Bootstrap{}".format(_extension))
        assert result == 0, output

        result, output = _Execute([], root, "Activate{extension} & Deactivate{extension}".format(extension=_extension))

        assert result == expected_result, (result, output)
        assert output == expected_output, output

    # ----------------------------------------------------------------------
    def test_Empty(self, tmp_path_factory, templates_path):
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
        )

    # ----------------------------------------------------------------------
    def test_ScriptFile(self, tmp_path_factory, templates_path):
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
        )

    # ----------------------------------------------------------------------
    def test_PythonFile(self, tmp_path_factory, templates_path):
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
                Hello from DeactivateEpilog_py{extension}

                {root} has been deactivated.

                """,
            ).format(
                extension=_extension,
                root=root,
            ),
        )

    # ----------------------------------------------------------------------
    def test_ScriptAndPythonFiles(self, tmp_path_factory, templates_path):
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
                Hello from DeactivateEpilog_py{extension}

                {root} has been deactivated.

                """,
            ).format(
                extension=_extension,
                root=root,
            ),
        )

    # ----------------------------------------------------------------------
    def test_ScriptError(self, tmp_path_factory, templates_path):
        root = tmp_path_factory.mktemp("root")

        with (root / f"DeactivateEpilog{_extension}").open("w") as f:
            f.write("this is an invalid command")

        if _is_windows:
            error = textwrap.dedent(
                """\
                'this' is not recognized as an internal or external command,
                operable program or batch file.
                """,
            ).rstrip()

            expected_result = 1

        else:
            assert False

        self.Execute(
            [
                (templates_path / f"Bootstrap{_extension}", root / f"Bootstrap{_extension}"),
            ],
            root,
            textwrap.dedent(
                """\

                {root} has been activated.

                {error}
                ERROR: DeactivateEpilog{extension} failed.
                """,
            ).format(
                root=root,
                error=error,
                extension=_extension,
            ),
            expected_result=expected_result,
        )

    # ----------------------------------------------------------------------
    def test_PythonError(self, tmp_path_factory, templates_path):
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
        )

    # ----------------------------------------------------------------------
    def test_PythonResultError(self, tmp_path_factory, templates_path):
        root = tmp_path_factory.mktemp("root")

        with (root / f"DeactivateEpilog.py").open("w") as f:
            f.write(
                textwrap.dedent(
                    """\
                    import sys
                    from pathlib import Path

                    with Path(sys.argv[1]).open("w") as f:
                        f.write("this is an invalid command")
                    """,
                ),
            )

        if _is_windows:
            error = textwrap.dedent(
                """\
                'this' is not recognized as an internal or external command,
                operable program or batch file.
                """,
            ).rstrip()

            expected_result = 1
        else:
            assert False

        self.Execute(
            [
                (templates_path / f"Bootstrap{_extension}", root / f"Bootstrap{_extension}"),
            ],
            root,
            textwrap.dedent(
                """\

                {root} has been activated.

                {error}
                ERROR: Executing the DeactivateEpilog.py output failed.
                """,
            ).format(
                root=root,
                error=error,
            ),
            expected_result=expected_result,
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

    result = subprocess.run(
        command,
        check=False,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=root,
    )

    content = result.stdout.decode("utf-8")

    # Remove lines eventually replaced by DONE-style messages
    content = re.sub(
        r"^[^\n]+\r\n\x1b\[1A",
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

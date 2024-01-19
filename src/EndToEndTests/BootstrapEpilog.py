# ----------------------------------------------------------------------
# |
# |  BootstrapEpilog.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2023-12-12 13:16:24
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2023
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
import subprocess

from pathlib import Path

result = subprocess.run(
    "pip install -r requirements.txt",
    check=False,
    cwd=Path(__file__).parent,
    shell=True,
    stderr=subprocess.STDOUT,
    stdout=subprocess.PIPE,
)

assert result.returncode == 0, result.stdout.decode("utf-8")

# This file is called during the Bootstrap process.
import sys

from pathlib import Path

print("Hello from BootstrapEpilog.py")
sys.stdout.write("Arguments\n{}\n".format("\n".join("  - {}".format(arg) for arg in sys.argv[1:])))

# The first argument will be a filename that should be used to write os-specific commands. These
# commands (if any) are executed after this script completes. Commands are written to a file
# rather than stdout so that stdout can be used to display status information associated with long-
# running operations.
with Path(sys.argv[1]).open("w") as f:
    f.write("echo Hello from BootstrapEpilog.py output")

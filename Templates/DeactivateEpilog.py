import sys

from pathlib import Path

print("Hello from DeactivateEpilog.py")

with Path(sys.argv[1]).open("w") as f:
    f.write("echo Hello from DeactivateEpilog_py.cmd")

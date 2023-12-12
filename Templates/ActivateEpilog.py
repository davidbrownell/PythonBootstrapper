import sys

from pathlib import Path

print("Hello from ActivateEpilog.py")

with Path(sys.argv[1]).open("w") as f:
    f.write("echo Hello from ActivateEpilog_py.cmd")

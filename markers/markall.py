"""Executes every mark_error_*.py script from current directory."""

import sys
import os
import re

if __name__ == "__main__":
    if len(sys.argv) == 1:
        dir = "."
    else:
        dir = sys.argv[1]
    for filename in os.listdir(dir):
        if re.match(r"^mark_error_\d+\.py", filename):
            print("{}:".format(filename))
            exec(open(os.path.join(dir, filename), encoding="utf-8").read())


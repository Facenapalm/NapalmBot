"""Executes every mark_error_*.py script from current directory."""

import os
import re

if __name__ == "__main__":
    for filename in os.listdir():
        if re.match(r"^mark_error_\d+\.py", filename):
            print("{}:".format(filename))
            exec(open(filename, encoding="utf-8").read())

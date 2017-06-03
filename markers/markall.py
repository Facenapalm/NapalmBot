"""
Executes every mark_error_*.py script from current or given directory.

Usage:
    python markall.py [path-to-markers]
"""

import sys
import os
import re

def main():
    if len(sys.argv) == 1:
        directory = "."
    else:
        directory = sys.argv[1]
        sys.path.append(directory)
    for filename in os.listdir(directory):
        if re.match(r"^mark_error_\d+\.py", filename):
            print("{}:".format(filename))
            __import__(filename[:-3]).main()

if __name__ == "__main__":
	main()

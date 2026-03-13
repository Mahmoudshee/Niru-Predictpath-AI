import sys
from pathlib import Path

def main():
    print(f"ARGV: {sys.argv}")
    if len(sys.argv) > 1:
        path_str = sys.argv[1]
        print(f"PATH STR: {path_str}")
        print(f"RESOLVED: {Path(path_str).resolve()}")

if __name__ == "__main__":
    main()

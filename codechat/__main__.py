
import sys
import os

# Add the parent directory to the Python path so we can import cli
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cli import app

def main():
    app()

if __name__ == "__main__":
    main()
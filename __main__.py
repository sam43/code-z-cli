import sys
from cli import CLI

def main():
    cli = CLI()
    # Pass command line arguments except the script name
    cli.run(sys.argv[1:])

if __name__ == "__main__":
    main()
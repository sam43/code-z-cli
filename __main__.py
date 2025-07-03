import argparse

def main():
    parser = argparse.ArgumentParser(description="CodeZ CLI - AI-powered code assistant")
    parser.add_argument('--with-memory', dest='with_memory', action='store_true', help='Enable contextual replies (session memory)')
    parser.add_argument('--no-memory', dest='with_memory', action='store_false', help='Disable contextual replies (stateless)')
    parser.set_defaults(with_memory=True)  # Default is with memory enabled
    args = parser.parse_args()

    from core import repl
    repl.run(with_memory=args.with_memory)

if __name__ == "__main__":
    main()

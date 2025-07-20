def main():
    """
    Entry point for the script; initializes and runs the command-line interface.
    """
    from cli import CLI
    cli = CLI()
    cli.run()

if __name__ == "__main__":
    main()

import time
import sys

def stream_response(text, console=None, delay=0.01):
    """Stream text to the terminal character by character."""
    for char in text:
        if console:
            console.print(char, end="", soft_wrap=True, highlight=False)
        else:
            print(char, end="", flush=True)
        sys.stdout.flush()
        time.sleep(delay)
    if console:
        console.print("")
    else:
        print("")

def stream_thinking(text, console=None, delay=0.001):
    """Stream text in light gray color for thought process."""
    style = "grey20"  # Rich color for light gray
    for char in text:
        if console:
            console.print(char, end="", style=style, soft_wrap=True, highlight=False)
        else:
            print(char, end="", flush=True)
        sys.stdout.flush()
        time.sleep(delay)
    if console:
        console.print("")
    else:
        print("")

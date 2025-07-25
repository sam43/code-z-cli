#!/usr/bin/env python3
"""
Test script to verify CodeZ CLI installation and entry points work correctly.
"""

import subprocess
import sys
import os

def run_command(cmd):
    """Run a command and return the result."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"

def test_entry_point():
    """Test that the codez command is available and working."""
    print("🧪 Testing CodeZ CLI entry point...")
    
    # Test basic help command
    success, stdout, stderr = run_command("codez --help")
    if not success:
        print(f"❌ Failed to run 'codez --help': {stderr}")
        return False
    
    if "Usage: codez" not in stdout:
        print(f"❌ Unexpected output from 'codez --help': {stdout}")
        return False
    
    print("✅ Basic entry point works!")
    
    
    # Test chat command
    success, stdout, stderr = run_command("codez chat --help")
    if not success:
        print(f"❌ Failed to run 'codez chat --help': {stderr}")
        return False
    
    if "Interactive REPL" not in stdout:
        print(f"❌ Unexpected output from 'codez chat --help': {stdout}")
        return False
    
    print("✅ Chat command works!")
    
    return True

def main():
    """Main test function."""
    print("🚀 Testing CodeZ CLI Installation")
    print("=" * 40)
    
    if test_entry_point():
        print("\n🎉 All tests passed! CodeZ CLI is ready to use!")
        print("\nYou can now run:")
        print("  codez chat          # Start interactive chat")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the installation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
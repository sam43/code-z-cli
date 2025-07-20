#!/usr/bin/env python3
"""
Build script for CodeZ CLI package.
This script helps build and optionally upload the package to PyPI.
"""

import subprocess
import sys
import os
import shutil

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed!")
        print(f"Error: {e.stderr}")
        return False

def clean_build_dirs():
    """Clean up build directories."""
    dirs_to_clean = ['build', 'dist', 'codez_cli.egg-info']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"🧹 Cleaning {dir_name}...")
            shutil.rmtree(dir_name)

def build_package():
    """Build the package."""
    print("🚀 Building CodeZ CLI Package")
    print("=" * 40)
    
    # Clean previous builds
    clean_build_dirs()
    
    # Build the package
    if not run_command("python -m build", "Building package"):
        return False
    
    # Check the built package
    if not run_command("python -m twine check dist/*", "Checking package"):
        print("⚠️  Package check failed, but continuing...")
    
    print("\n🎉 Package built successfully!")
    print("📦 Built files are in the 'dist/' directory")
    
    return True

def test_installation():
    """Test the built package installation."""
    print("\n🧪 Testing package installation...")
    
    # Create a temporary virtual environment for testing
    if not run_command("python -m venv test_env", "Creating test environment"):
        return False
    
    # Activate and install the package
    # Use python -m pip directly from the virtual environment
    venv_python = "test_env/bin/python" if os.name != 'nt' else "test_env\\Scripts\\python"
    
    # Find the wheel file explicitly
    import glob
    wheel_files = glob.glob("dist/*.whl")
    if not wheel_files:
        print("❌ No wheel file found in dist/ directory")
        return False
    if len(wheel_files) > 1:
        print(f"⚠️  Multiple wheel files found, using: {wheel_files[0]}")
    
    install_cmd = f'"{venv_python}" -m pip install "{wheel_files[0]}"'
    if not run_command(install_cmd, "Installing package in test environment"):
        return False
    
    # Test the entry point
    # Test the entry point using virtual environment Python
    test_cmd = f"{venv_python} -m codechat.__main__ --help"
    if not run_command(test_cmd, "Testing entry point"):
        return False
    
    # Clean up test environment
    try:
        shutil.rmtree("test_env")
    except OSError as e:
        print(f"⚠️  Warning: Could not clean up test environment: {e}")
    
    print("✅ Package installation test passed!")
    return True

def main():
    """Main build function."""
    if len(sys.argv) > 1 and sys.argv[1] == "--test-only":
        return 0 if test_installation() else 1
    
    if not build_package():
        return 1
    
    if len(sys.argv) > 1 and sys.argv[1] == "--with-test":
        if not test_installation():
            return 1
    
    print("\n📋 Next steps:")
    print("  • Test locally: pip install dist/*.whl")
    print("  • Upload to PyPI: python -m twine upload dist/*")
    print("  • Upload to Test PyPI: python -m twine upload --repository testpypi dist/*")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
from setuptools import setup, find_packages

setup(
    name="codechat-cli",
    version="1.0.0",
    description="Interactive AI-powered code assistant for your terminal.",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        "rich>=13.0.0",
        "prompt-toolkit>=3.0.0",
        "tree_sitter>=0.20.1",
        "typer>=0.9.0"
    ],
    entry_points={
        "console_scripts": [
            "codechat=codechat.__main__:main"
        ]
    },
    python_requires=">=3.8",
    include_package_data=True,
    zip_safe=False,
)

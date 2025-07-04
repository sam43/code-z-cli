from setuptools import setup, find_packages
from pathlib import Path

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="codechat-cli",
    version="1.0.0",
    description="Interactive AI-powered code assistant for your terminal.",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        'rich',
        'prompt_toolkit',
        'platformdirs',
    ],
    entry_points={
        'console_scripts': [
            'codez = core.repl:run',
        ],
    },
    include_package_data=True,
    python_requires='>=3.8',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'Environment :: Console',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
    ],
)

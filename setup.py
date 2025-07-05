from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='codez-cli',
    version='0.1.0',
    description='CodeZ CLI – Your Offline Code Companion',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Sadat Sayem',
    author_email='scode43@gmail.com',
    url='https://github.com/sam43/code-z-cli',
    license='Apache 2.0',
    packages=find_packages(),
    install_requires=[
        'rich',
        'prompt_toolkit',
        'platformdirs',
        'tree-sitter',  # Added tree-sitter for parsing
    ],
    entry_points={
        'console_scripts': [
            'codez=codechat.__main__:main',
        ],
    },
    include_package_data=True,
    python_requires='>=3.8',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'Environment :: Console',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
    ],
    zip_safe=False,
)

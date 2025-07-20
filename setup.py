from setuptools import setup, find_packages
import tomllib

def get_version():
    with open("pyproject.toml", "rb") as f:
        data = tomllib.load(f)
    return data["project"]["version"]


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='codez-cli',
    version=get_version(),
    description='CodeZ CLI – When AI Takes a Break, We Don’t!',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Sadat Sayem',
    author_email='scode43@gmail.com',
    url='https://github.com/sam43/code-z-cli',
    license='Apache 2.0',
    packages=find_packages(),
    install_requires=[
        'rich>=14.0.0',
        'prompt_toolkit>=3.0.0',
        'platformdirs>=4.2.0',
        'tree-sitter>=0.20.1',
        'typer>=0.16.0',
        'ollama>=0.5.1',
        'pyfiglet>=0.8.post1',
        'httpx>=0.28.1',
        'pydantic>=2.11.7',
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

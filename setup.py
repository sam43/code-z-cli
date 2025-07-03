from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='codez-cli',
    version='0.1.0',
    description='CodeZ CLI – Your Offline Code Companion',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Your Name',
    author_email='your.email@example.com',
    url='https://github.com/yourusername/codez-cli',
    license='MIT',
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

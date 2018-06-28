import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt", "r") as fh:
    requirements = fh.read().split()

with open("VERSION", "r") as fh:
    version = fh.read()

setuptools.setup(
    name='textpipe',
    version=version,
    description="textpipe: clean and extract metadata from text",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/textpipe/textpipe",
    packages=setuptools.find_packages(),
    classifiers=(
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
    license='MIT',
    install_requires=requirements,
)

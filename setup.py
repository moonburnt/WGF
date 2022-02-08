from setuptools import find_packages, setup

with open("README.md") as f:
    long_description = f.read()

setup(
    name="WGF",
    version="0.1.1",
    description="WGF - Whatever Game Framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/moonburnt/WGF",
    author="moonburnt",
    author_email="moonburnt@disroot.org",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Development Status :: 5 - Production/Stable",
    ],
    packages=find_packages(),
    install_requires=[
        "pygame==2.1.2",
    ],
    extras_require={"toml_support": ["toml==0.10.2"]},
)

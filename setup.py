from setuptools import find_namespace_packages, find_packages, setup

setup(
    name="sarathi",
    version="0.0.4b",
    description="A CLI coding assistant",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/abhishek9sharma/sarathi",
    author="Abhishek Sharma",
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
    ],
    keywords="cli coding assistant",
    packages=find_namespace_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.7",
    install_requires=["requests", "astor", "black"],
    extras_require={
        "dev": [
            "twine>=4.0.2",
            "wheel",
        ]
    },
    entry_points={
        "console_scripts": [
            "sarathi=sarathi.cli.cli_handler:main",  #
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/abhishek9sharma/sarathi/issues",
        "Source": "https://github.com/abhishek9sharma/sarathi",
    },
)

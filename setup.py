"""
Setup configuration for Fill Rate Classifier

This file configures the package for installation and distribution.
It defines package metadata, dependencies, and entry points.

Dependencies: README.md, requirements.txt
Used by: pip install, deployment scripts
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="fill-rate-classifier",
    version="0.1.0",
    author="Instawork Engineering",
    author_email="engineering@instawork.com",
    description="A classification suite for analyzing and categorizing fill rate issues",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/instawork/fill-rate-classifier",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "fill-rate-classify=scripts.run_classification:main",
            "fill-rate-report=scripts.generate_report:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.json"],
    },
)
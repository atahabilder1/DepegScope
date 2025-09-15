"""Setup script for DepegScope."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    requirements = [
        line.strip()
        for line in requirements_path.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="depegscope",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Stablecoin Depeg Contagion Analysis Framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/DepegScope",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/DepegScope/issues",
        "Documentation": "https://github.com/yourusername/DepegScope/tree/main/docs",
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Office/Business :: Financial",
    ],
    packages=find_packages(exclude=["tests", "tests.*", "notebooks"]),
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0",
        ],
        "docs": [
            "sphinx>=6.0.0",
            "sphinx-rtd-theme>=1.2.0",
            "myst-parser>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "depegscope-collect=scripts.collect_data:main",
            "depegscope-build=scripts.build_graph:main",
            "depegscope-simulate=scripts.run_simulation:main",
            "depegscope-report=scripts.generate_report:main",
        ],
    },
    include_package_data=True,
    package_data={
        "config": ["*.yaml", "*.yml"],
    },
    zip_safe=False,
)

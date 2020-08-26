from setuptools import setup, find_packages

setup(
    name="gost",
    version="0.0.1",
    url="https://github.com/sixy6e/gost",
    author="Josh Sixsmith",
    description="Structured logging for MPI based Python code",
    keywords=[
        "logging", 
        "structured",
        "structure",
        "log",
        "MPI",
        "mpi4py",
    ],
    packages=find_packages(),
    install_requires=[
        "mpi4py",
        "click",
        "structlog",
        "mpi-structlog",
    ],
    dependency_links=[
        "git+https://github.com/sixy6e/mpi-structlog",
    ],
    license="MIT",
    entry_points="""
        [console_scripts]
        ard-intercomparison=gost.ui.cli:entry_point
    """,
)

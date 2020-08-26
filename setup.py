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
        "datacube",
        "mpi-structlog",
    ],
    dependency_links=[
        "git+https://github.com/sixy6e/mpi-structlog",
    ],
    package_data={
        "gost": ["data/*.zstd"],
    },
    license="MIT",
    zip_safe=False,
    entry_points="""
        [console_scripts]
        ard-intercomparison=gost.ui.cli:entry_point
    """,
)

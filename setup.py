from setuptools import setup, find_packages

setup(
    name="gost",
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    url="https://github.com/sixy6e/gost",
    author="Josh Sixsmith",
    description="Intercomparison workflow for DEA's ARD.",
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
        "git+https://github.com/sixy6e/mpi-structlog@develop#egg=mpi_structlog",
    ],
    package_data={
        "gost": [
            "data/*.zst",
            "latex_templates/figures/*.txt",
            "latex_templates/sections/*.txt",
            "latex_templates/tables/*.txt",
        ],
    },
    license="MIT",
    zip_safe=False,
    entry_points="""
        [console_scripts]
        ard-intercomparison=gost.ui.cli:entry_point
    """,
)

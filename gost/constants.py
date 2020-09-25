"""
Placeholder for filenames. Just makes the whole workflow simpler
rather than asking users to specify input and output filenames, and
ensuring that extensions are used correctly.
There is a multitude of formats available, but for simplicity, which is
one of the goals for this repo, handle the inner workings silently, and
yield the results back to the user in the simplest form.
"""

from enum import Enum
import pkg_resources
import numpy  # type: ignore
import structlog  # type: ignore
from structlog.processors import JSONRenderer  # type: ignore

LOG_PROCESSORS = [
    structlog.stdlib.add_log_level,
    structlog.processors.TimeStamper(fmt="ISO"),
    structlog.processors.StackInfoRenderer(),
    structlog.processors.format_exc_info,
    JSONRenderer(sort_keys=True),
]
SUMMARISE_FUNCS = [numpy.min, numpy.max, numpy.mean]
WRS2_FNAME = pkg_resources.resource_filename(
    "gost", "data/landsat_wrs2_descending.geojsonl.zst"
)
MGRS_FNAME = pkg_resources.resource_filename("gost", "data/sentinel-2-mgrs.geojsonl.zst")
FRAMING = {
    "WRS2": WRS2_FNAME,
    "MGRS": MGRS_FNAME,
}
TM_WORLD_BORDERS_FNAME = pkg_resources.resource_filename(
    "gost", "data/TM_WORLD_BORDERS-0.3.geojsonl.zst"
)
MEASUREMENT_TEMPLATE = pkg_resources.resource_filename(
    "gost", "latex_templates/figures/measurement.txt"
)
MIN_MAX_TABLE_TEMPLATE = pkg_resources.resource_filename(
    "gost", "latex_templates/tables/measurement-min-max-pct.txt"
)
ANCILLARY_TABLE_TEMPLATE = pkg_resources.resource_filename(
    "gost", "latex_templates/tables/ancillary.txt"
)
SOFTWARE_VERSIONS_TABLE_TEMPLATE = pkg_resources.resource_filename(
    "gost", "latex_templates/tables/software-versions.txt"
)
GQA_TABLE_TEMPLATE = pkg_resources.resource_filename(
    "gost", "latex_templates/tables/geometric-quality.txt"
)
NBAR_SECTION_TEMPLATE = pkg_resources.resource_filename(
    "gost", "latex_templates/sections/nbar.txt"
)
NBART_SECTION_TEMPLATE = pkg_resources.resource_filename(
    "gost", "latex_templates/sections/nbart.txt"
)
OA_SECTION_TEMPLATE = pkg_resources.resource_filename(
    "gost", "latex_templates/sections/oa.txt"
)
ANCILLARY_SECTION_TEMPLATE = pkg_resources.resource_filename(
    "gost", "latex_templates/sections/ancillary.txt"
)
GQA_SECTION_TEMPLATE = pkg_resources.resource_filename(
    "gost", "latex_templates/sections/geometric-quality.txt"
)
SOFTWARE_SECTION_TEMPLATE = pkg_resources.resource_filename(
    "gost", "latex_templates/sections/software-versions.txt"
)
MAIN_SECTION_TEMPLATE = pkg_resources.resource_filename(
    "gost", "latex_templates/sections/main.txt"
)


class LogNames(Enum):
    """
    Defines the log filenames used by each part of the workflow.
    """

    QUERY = "ard-intercomparison-query.log.jsonl"
    MEASUREMENT_INTERCOMPARISON = "ard-intercomparison-measurement-comparison.log.jsonl"
    PROC_INFO_INTERCOMPARISON = "ard-intercomparison-proc-info-comparison.log.jsonl"
    COLLATE = "ard-intercomparison-collate.log.jsonl"
    PLOTTING = "ard-intercomparison-plotting.log.jsonl"
    REPORTING = "ard-intercomparison-reporting.log.jsonl"


class DirectoryNames(Enum):
    """
    Defines the sub-directory names used by the workflow.
    """

    LOGS = "logs"
    PBS = "pbs"
    RESULTS = "results"
    PLOTS = "plots"
    REPORT = "report"
    REPORT_FIGURES = "figures"
    REPORT_TABLES = "tables"
    REPORT_SECTIONS = "sections"


class FileNames(Enum):
    """
    Defines the data output filenames from each part of the workflow.
    """

    RESULTS = "intercomparison-results.h5"
    GENERAL_FRAMING = "results-per-framing-geometry-general.geojsonl"
    FMASK_FRAMING = "results-per-framing-geometry-fmask.geojsonl"
    CONTIGUITY_FRAMING = "results-per-framing-geometry-contiguity.geojsonl"
    SHADOW_FRAMING = "results-per-framing-geometry-shadow.geojsonl"
    GQA_FRAMING = "results-per-framing-geometry-gqa.geojsonl"
    ANCILLARY_FRAMING = "results-per-framing-geometry-ancillary.geojsonl"


class LatexSectionFnames(Enum):
    """Filenames specific to LaTeX main and section documents."""

    MAIN = "main.tex"
    ANCILLARY = "ancillary.tex"
    GQA = "geometric-quality.tex"
    SOFTWARE = "software-versions.tex"
    NBAR = "nbar.tex"
    NBART = "nbart.tex"
    OA = "oa.tex"
    PRODUCT_FMT = "{product_name}.tex"


class FigureTemplates(Enum):
    """Figure templates for the report."""

    MEASUREMENT = MEASUREMENT_TEMPLATE


class TableTemplates(Enum):
    """Table templates for the report."""

    MEASUREMENT = MIN_MAX_TABLE_TEMPLATE
    ANCILLARY = ANCILLARY_TABLE_TEMPLATE
    SOFTWARE = SOFTWARE_VERSIONS_TABLE_TEMPLATE
    GQA = GQA_TABLE_TEMPLATE


class SectionTemplates(Enum):
    """Templates for each section of the report."""

    MAIN = MAIN_SECTION_TEMPLATE
    SOFTWARE = SOFTWARE_SECTION_TEMPLATE
    ANCILLARY = ANCILLARY_SECTION_TEMPLATE
    GQA = GQA_SECTION_TEMPLATE
    NBAR = NBAR_SECTION_TEMPLATE
    NBART = NBART_SECTION_TEMPLATE
    OA = OA_SECTION_TEMPLATE


class CsvFileNames(Enum):
    """Filenames specific to CSV's."""

    ANCILLARY = "ancillary-min-max.csv"
    GQA = "gqa-min-max.csv"
    SOFTWARE = "software-versions.csv"


class LatexTableFileNames(Enum):
    """Filenames specific to LaTeX tables."""

    ANCILLARY = "ancillary.tex"
    GQA = "geometric-quality.tex"
    SOFTWARE = "software-versions.tex"
    PRODUCT_FORMAT = "{product_name}.tex"


class DatasetGroups(Enum):
    """
    Defines the different dataset groups.
    """

    INTERCOMPARISON = "INTERCOMPARISON"
    SUMMARY = "SUMMARY"


class DatasetNames(Enum):
    """
    Defines the dataset names.
    """

    QUERY = "QUERY"
    SOFTWARE_VERSIONS = "SOFTWARE-VERSIONS"
    GENERAL_RESULTS = "GENERAL-RESULTS"
    FMASK_RESULTS = "FMASK-RESULTS"
    CONTIGUITY_RESULTS = "CONTIGUITY-RESULTS"
    SHADOW_RESULTS = "SHADOW-RESULTS"
    GQA_RESULTS = "GQA-RESULTS"
    ANCILLARY_RESULTS = "ANCILLARY-RESULTS"
    GENERAL_SUMMARISED = "SUMMARISED-GENERAL"
    FMASK_SUMMARISED = "SUMMARISED-FMASK"
    CONTIGUITY_SUMMARISED = "SUMMARISED-CONTIGUITY"
    SHADOW_SUMMARISED = "SUMMARISED-SHADOW"
    GQA_SUMMARISED = "SUMMARISED-GQA"
    ANCILLARY_SUMMARISED = "SUMMARISED-ANCILLARY"


class MergeLookup(Enum):
    """
    Only used for filename lookup based on the dataset name.
    """

    GENERAL_RESULTS = "GENERAL_FRAMING"
    FMASK_RESULTS = "FMASK_FRAMING"
    CONTIGUITY_RESULTS = "CONTIGUITY_FRAMING"
    SHADOW_RESULTS = "SHADOW_FRAMING"
    GQA_RESULTS = "GQA_FRAMING"
    ANCILLARY_RESULTS = "ANCILLARY_FRAMING"


class SummaryLookup(Enum):
    """
    Only used for filename lookup based on the dataset name.
    """

    GENERAL_RESULTS = "GENERAL_SUMMARISED"
    FMASK_RESULTS = "FMASK_SUMMARISED"
    CONTIGUITY_RESULTS = "CONTIGUITY_SUMMARISED"
    SHADOW_RESULTS = "SHADOW_SUMMARISED"
    GQA_RESULTS = "GQA_SUMMARISED"
    ANCILLARY_RESULTS = "ANCILLARY_SUMMARISED"


class Walltimes(Enum):
    """
    PBS job walltimes for each section of the workflow.
    As it is a chained job, it was easy to set, rather than have users
    think about each component.
    If this gets used for larger workloads than expected, then walltimes
    can be updated.
    """

    QUERY = "00:10:00"
    INTERCOMPARISON = "00:30:00"
    COLLATION = "00:10:00"
    PLOTTING = "00:30:00"

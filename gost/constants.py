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
MGRS_FNAME = pkg_resources.resource_filename(
    "gost", "data/sentinel-2-mgrs.geojsonl.zst"
)
FRAMING = {
    "WRS2": WRS2_FNAME,
    "MGRS": MGRS_FNAME,
}
TM_WORLD_BORDERS_FNAME = pkg_resources.resource_filename(
    "gost", "data/TM_WORLD_BORDERS-0.3.geojsonl.zst"
)
DOCUMENT_TEMPLATE = pkg_resources.resource_filename(
    "gost", "data/doc-template.txt"
)
MEASUREMENT_TEMPLATE = pkg_resources.resource_filename(
    "gost", "data/measurement-template.txt"
)
MIN_MAX_TABLE_TEMPLATE = pkg_resources.resource_filename(
    "gost", "data/min-max-pct-table-template.txt"
)
PROC_INFO_TABLE_TEMPLATE = pkg_resources.resource_filename(
    "gost", "data/proc-info-table-template.txt"
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
    REPORT = "{product_group}-residuals-analysis.tex"


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

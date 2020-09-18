"""
Utils pertaining to the creation of the LaTeX reports.
"""
import io
from pathlib import Path
from typing import Any, Dict, List, Tuple
import pandas
import geopandas  # type: ignore
import structlog  # type: ignore

from gost.collate import reflectance_pass_fail
from gost.constants import (
    DirectoryNames,
    FileNames,
    MEASUREMENT_TEMPLATE,
    DOCUMENT_TEMPLATE,
    TABLE1_TEMPLATE,
)

MIN_MAX_PCT_CAPTION = {
    "nbar": "Difference in Surface Reflectance",
    "nbart": "Difference in Surface reflectance",
    "oa": "Difference",
}

_LOG = structlog.get_logger()


def _write_measurement_docs(
    gdf: geopandas.GeoDataFrame,
    outdir: Path,
    measurement_template: str,
) -> Dict[str, List]:
    """
    Write the measurement sub-documents for each of the product groups.
    """

    # currently the groups are nbar, nbart, oa
    product_groups = set(meas.split("_")[0] for meas in gdf.measurement.unique())
    measurement_doc_fnames: Dict[str, List] = {
        p_group: [] for p_group in product_groups
    }

    for name, grp in gdf.groupby("measurement"):
        product_group = name.split("_")[0]

        # replace items like nbar_blue with NBAR BLUE for figure captions
        figure_caption = name.upper().replace("_", " ")

        out_string = measurement_template.format(
            measurement_name=name,
            product_group=product_group,
            figure_caption=figure_caption,
        )

        # need relative names to insert into the main tex doc of each product
        basename = f"{name}.tex"
        relative_fname = Path(DirectoryNames.MEASUREMENT_DOCS.value, basename)
        measurement_doc_fnames[product_group].append(relative_fname)

        out_fname = outdir.joinpath(relative_fname)
        if not out_fname.parent.exists():
            out_fname.parent.mkdir(parents=True)

        _LOG.info("writing tex document to disk", out_fname=str(out_fname))

        with open(out_fname, "w") as outf:
            outf.write(out_string)

    return measurement_doc_fnames


def _write_product_docs(
    measurement_doc_fnames: Dict[str, List],
    table_fnames: Dict[str, str],
    pass_fail: Dict[str, str],
    outdir: Path,
    document_template: str,
) -> None:
    """Write each of the LaTeX main level product documents."""

    for product_group in measurement_doc_fnames:

        sub_doc_names = measurement_doc_fnames[product_group].copy()

        # only have 1 table doc to insert at this stage
        sub_doc_names.insert(0, table_fnames[product_group])

        doc_sections = "".join([f"  \\subfile{{{s}}}\n" for s in sub_doc_names])

        out_string = document_template.format(
            product_group=product_group,
            product_group2=product_group.upper(),
            sections=doc_sections,
            pass_fail=pass_fail[product_group],
        )

        out_fname = outdir.joinpath(
            FileNames.REPORT.value.format(product_group=product_group)
        )

        _LOG.info("writing tex document to disk", out_fname=str(out_fname))

        with open(out_fname, "w") as outf:
            outf.write(out_string)


def _write_product_tables(outdir: Path, table_template: str) -> Dict[str, str]:
    """Create LaTeX tables from various CSV's."""

    product_groups = ["nbar", "nbart", "oa"]

    table_fnames: Dict[str, str] = dict()

    for product_name in product_groups:

        basename = f"{product_name}_tables.tex"
        relative_fname = Path(DirectoryNames.TABLE_DOCS.value, basename)
        table_fnames[product_name] = str(relative_fname)

        out_fname = outdir.joinpath(relative_fname)
        if not out_fname.parent.exists():
            out_fname.parent.mkdir(parents=True)

        out_string = table_template.format(
            caption=MIN_MAX_PCT_CAPTION[product_name], product_name=product_name
        )

        _LOG.info("writing tex document to disk", out_fname=str(out_fname))

        with open(out_fname, "w") as src:
            src.write(out_string)

    return table_fnames


def latex_documents(
    gdf: geopandas.GeoDataFrame, dataframe: pandas.DataFrame, outdir: Path
) -> None:
    """
    Utility to create the latex document strings.
    Very basic, but is a starting point for auto-generated nice looking
    reports.

    :param gdf:
        A geopandas GeoDataFrame containing the 'general' results.

    :param outdir:
        The base output directory of the entire intercomparison workflow.
    """

    _LOG.info("reading LaTeX main document template")

    with open(DOCUMENT_TEMPLATE, "r") as src:
        doc_template = src.read()

    _LOG.info("reading LaTeX measurement template")

    with open(MEASUREMENT_TEMPLATE, "r") as src:
        measurement_template = src.read()

    _LOG.info("reading LaTeX table template")

    with open(TABLE1_TEMPLATE, "r") as src:
        table_template = src.read()

    measurement_doc_fnames = _write_measurement_docs(gdf, outdir, measurement_template)

    table_fnames = _write_product_tables(outdir, table_template)

    pass_fail_result = reflectance_pass_fail(dataframe)
    nbar_pass_fail = "Pass" if pass_fail_result[0]["test_passed"] else "Fail"
    nbart_pass_fail = "Pass" if pass_fail_result[1]["test_passed"] else "Fail"

    pass_fail = {
        "nbar": f"Result Outcome: {nbar_pass_fail}",
        "nbart": f"Result Outcome: {nbart_pass_fail}",
        "oa": "",
    }

    _write_product_docs(
        measurement_doc_fnames, table_fnames, pass_fail, outdir, doc_template
    )

    _LOG.info("finished writing LaTeX documents")

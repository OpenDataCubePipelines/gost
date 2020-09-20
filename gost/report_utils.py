"""
Utils pertaining to the creation of the LaTeX reports.
"""
from collections import namedtuple
import io
from pathlib import Path
from typing import Any, Dict, List, Tuple
import pandas  # type: ignore
import geopandas  # type: ignore
import structlog  # type: ignore

from gost.collate import reflectance_pass_fail
from gost.constants import (
    CsvFileNames,
    DirectoryNames,
    FileNames,
    LatexTableFileNames,
    MEASUREMENT_TEMPLATE,
    DOCUMENT_TEMPLATE,
    MIN_MAX_TABLE_TEMPLATE,
    METADATA_MIN_MAX_TABLE_TEMPLATE,
    SOFTWARE_VERSIONS_TABLE_TEMPLATE,
)

_LOG = structlog.get_logger()


def write_latex_document(out_string: str, out_fname: Path) -> None:
    """
    Small proxy for writing a LaTeX formatted string as a LaTeX
    document.
    """

    _LOG.info("writing LaTeX document", out_fname=str(out_fname))

    if not out_fname.parent.exists():
        out_fname.parent.mkdir(parents=True)

    with open(out_fname, "w") as src:
        src.write(out_string)


def _write_measurement_figures(
    gdf: geopandas.GeoDataFrame,
    outdir: Path,
    measurement_template: str,
) -> Dict[str, List]:
    """
    Write the measurement sub-documents containing figures for each
    of the product groups.
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
        relative_fname = Path(DirectoryNames.REPORT_FIGURES.value, basename)
        measurement_doc_fnames[product_group].append(relative_fname)

        out_fname = outdir.joinpath(relative_fname)

        write_latex_document(out_string, out_fname)

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

        write_latex_document(out_string, out_fname)


def _write_product_tables(outdir: Path, table_template: str) -> Dict[str, str]:
    """Create LaTeX tables from various CSV's."""

    # product_groups = ["nbar", "nbart", "oa"]
    Table = namedtuple("Table", ["product_name", "caption"])

    tables = [
        Table(product_name="nbar", caption="Difference in Surface Reflectance"),
        Table(product_name="nbar", caption="Difference in Surface Reflectance"),
        Table(product_name="oa", caption="Difference"),
    ]

    table_fnames: Dict[str, str] = dict()

    # for product_name in product_groups:
    for table in tables:

        basename = LatexTableFileNames.PRODUCT_FORMAT.value.format(
            product_name=table.product_name
        )
        relative_fname = Path(DirectoryNames.REPORT_TABLES.value, basename)
        table_fnames[table.product_name] = str(relative_fname)

        out_fname = outdir.joinpath(relative_fname)
        if not out_fname.parent.exists():
            out_fname.parent.mkdir(parents=True)

        out_string = table_template.format(
            caption=table.caption, product_name=table.product_name
        )

        write_latex_document(out_string, out_fname)

    return table_fnames


def _write_ancillary_gqa_tables(outdir: Path, template: str) -> None:
    """Create the ancillary and GQA LaTeX document tables."""

    Table = namedtuple("Table", ["basename", "caption", "basename"])

    tables = [
        Table(
            basename=LatexTableFileNames.ANCILLARY.value,
            caption="Ancillary Minimum and Maximum Residual",
            basename=CsvFileNames.ANCILLARY.value,
        ),
        Table(
            basename=LatexTableFileNames.GQA.value,
            caption="GQA Minimum and Maximum Residual",
            basename=CsvFileNames.GQA.value,
        ),
    ]

    for table in tables:
        out_fname = outdir.joinpath(DirectoryNames.REPORT_TABLES.value, table.basename)

        out_string = template.format(
            caption=table.caption, basename=table.basename
        )

        write_latex_document(out_string, out_fname)


def _write_software_versions_table(outdir: Path, template: str) -> None:
    """Create the software versions LaTeX document table."""

    out_string = template.format(basename=CsvFileNames.SOFTWARE.value)

    out_fname = outdir.joinpath(
        DirectoryNames.REPORT_TABLES.value, LatexTableFileNames.SOFTWARE.value
    )

    write_latex_document(out_string, out_fname)


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

    def _reader(pathname: Path) -> str:
        """Small proxy for reading the plaintext LaTeX templates."""

        _LOG.info("reading LaTeX template", pathname=str(pathname))

        with open(pathname, "r") as src:
            document = src.read()

        return document

    _LOG.info("reading LaTeX document templates")

    doc_template = _reader(Path(DOCUMENT_TEMPLATE))
    measurement_template = _reader(Path(MEASUREMENT_TEMPLATE))
    min_max_table_template = _reader(Path(MIN_MAX_TABLE_TEMPLATE))
    metadata_template = _reader(Path(METADATA_MIN_MAX_TABLE_TEMPLATE))
    software_template = _reader(Path(SOFTWARE_VERSIONS_TABLE_TEMPLATE))

    measurement_doc_fnames = _write_measurement_figures(
        gdf, outdir, measurement_template
    )

    table_fnames = _write_product_tables(outdir, min_max_table_template)

    _write_ancillary_gqa_tables(outdir, metadata_template)
    _write_software_versions_table(outdir, software_template)

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

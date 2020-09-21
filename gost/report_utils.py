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
    LatexSectionFnames,
    SectionTemplates,
    FigureTemplates,
    TableTemplates,
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
    figure_fnames: Dict[str, List] = {p_group: [] for p_group in product_groups}

    for name, grp in gdf.groupby("measurement"):
        product_group = name.split("_")[0]

        # replace items like nbar_blue with NBAR BLUE for figure captions
        figure_caption = name.upper().replace("_", " ")

        out_string = measurement_template.format(
            measurement_name=name,
            figure_caption=figure_caption,
            stem=name,
            main_doc=LatexSectionFnames.MAIN.value,
        )

        # need relative names to insert into the main tex doc of each product
        basename = f"{name}.tex"
        relative_fname = Path(DirectoryNames.REPORT_FIGURES.value, basename)
        figure_fnames[product_group].append(relative_fname)

        out_fname = outdir.joinpath(relative_fname)

        write_latex_document(out_string, out_fname)

    return figure_fnames


def _write_product_sections(
    figure_doc_fnames: Dict[str, List],
    table_fnames: Dict[str, str],
    pass_fail: Dict[str, str],
    outdir: Path,
    product_templates: Dict[str, str],
) -> None:
    """Write each of the LaTeX product section documents."""

    skip_pass_fail_test = ["oa"]

    for product_group in figure_doc_fnames:

        sub_doc_names = figure_doc_fnames[product_group].copy()

        figures = "".join([f"    \\subfile{{\\main/{s}}}\n" for s in sub_doc_names])

        format_kwargs = {
            "main_doc": LatexSectionFnames.MAIN.value,
            "stem": product_group,
            "tables": table_fnames[product_group],
            "figures": figures,
        }
        if product_group not in skip_pass_fail_test:
            format_kwargs["pass_fail"] = pass_fail[product_group]

        out_string = product_templates[product_group].format(**format_kwargs)

        out_fname = outdir.joinpath(
            DirectoryNames.REPORT_SECTIONS.value,
            LatexSectionFnames.PRODUCT_FMT.value.format(product_name=product_group),
        )

        write_latex_document(out_string, out_fname)


def _write_product_tables(outdir: Path, table_template: str) -> Dict[str, str]:
    """Create LaTeX tables from various CSV's."""

    # product_groups = ["nbar", "nbart", "oa"]
    Table = namedtuple("Table", ["product_name", "caption"])

    tables = [
        Table(product_name="nbar", caption="Difference in Surface Reflectance"),
        Table(product_name="nbart", caption="Difference in Surface Reflectance"),
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
            caption=table.caption,
            product_name=table.product_name,
            main_doc=LatexSectionFnames.MAIN.value,
        )

        write_latex_document(out_string, out_fname)

    return table_fnames


def _write_ancillary_gqa_tables(outdir: Path, template: str) -> None:
    """Create the ancillary and GQA LaTeX document tables."""

    Table = namedtuple("Table", ["basename", "caption", "csv_basename"])

    tables = [
        Table(
            basename=LatexTableFileNames.ANCILLARY.value,
            caption="Ancillary Minimum and Maximum Residual",
            csv_basename=CsvFileNames.ANCILLARY.value,
        ),
        Table(
            basename=LatexTableFileNames.GQA.value,
            caption="GQA Minimum and Maximum Residual",
            csv_basename=CsvFileNames.GQA.value,
        ),
    ]

    for table in tables:
        out_fname = outdir.joinpath(DirectoryNames.REPORT_TABLES.value, table.basename)

        out_string = template.format(
            caption=table.caption,
            csv_basename=table.csv_basename,
            main_doc=LatexSectionFnames.MAIN.value,
        )

        write_latex_document(out_string, out_fname)


def _write_software_versions_table(outdir: Path, template: str) -> None:
    """Create the software versions LaTeX document table."""

    out_string = template.format(
        basename=CsvFileNames.SOFTWARE.value, main_doc=LatexSectionFnames.MAIN.value
    )

    out_fname = outdir.joinpath(
        DirectoryNames.REPORT_TABLES.value, LatexTableFileNames.SOFTWARE.value
    )

    write_latex_document(out_string, out_fname)


def _write_metadata_sections(
    outdir: Path, templates: Dict[LatexSectionFnames, str]
) -> None:
    """
    Write the LaTeX document sections for ancillary, gqa and
    software versions.
    """

    for key in templates:
        out_fname = outdir.joinpath(DirectoryNames.REPORT_SECTIONS.value, key.value)

        out_string = templates[key].format(
            main_doc=LatexSectionFnames.MAIN.value, stem=out_fname.stem
        )

        write_latex_document(out_string, out_fname)


def _write_main_section(outdir: Path, template: str) -> None:
    """Write the main level LaTeX document."""

    out_fname = outdir.joinpath(LatexSectionFnames.MAIN.value)

    out_string = template.format(
        stem=out_fname.stem,
        software_section=LatexSectionFnames.SOFTWARE.value,
        ancillary_section=LatexSectionFnames.ANCILLARY.value,
        gqa_section=LatexSectionFnames.GQA.value,
        nbar_section=LatexSectionFnames.NBAR.value,
        nbart_section=LatexSectionFnames.NBART.value,
        oa_section=LatexSectionFnames.OA.value
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

    measurement_template = _reader(Path(FigureTemplates.MEASUREMENT.value))
    min_max_table_template = _reader(Path(TableTemplates.MEASUREMENT.value))
    metadata_template = _reader(Path(TableTemplates.METADATA.value))
    software_template = _reader(Path(TableTemplates.SOFTWARE.value))

    figure_fnames = _write_measurement_figures(gdf, outdir, measurement_template)

    table_fnames = _write_product_tables(outdir, min_max_table_template)

    _write_ancillary_gqa_tables(outdir, metadata_template)
    _write_software_versions_table(outdir, software_template)

    pass_fail_result = reflectance_pass_fail(dataframe)
    nbar_pass_fail = "Pass" if pass_fail_result[0]["test_passed"] else "Fail"
    nbart_pass_fail = "Pass" if pass_fail_result[1]["test_passed"] else "Fail"

    pass_fail = {
        "nbar": nbar_pass_fail,
        "nbart": nbart_pass_fail,
    }

    # measurements per product group
    product_sections = {
        "nbar": _reader(Path(SectionTemplates.NBAR.value)),
        "nbart": _reader(Path(SectionTemplates.NBART.value)),
        "oa": _reader(Path(SectionTemplates.OA.value)),
    }

    _write_product_sections(
        figure_fnames, table_fnames, pass_fail, outdir, product_sections
    )

    # metadata
    metadata_sections = {
        LatexSectionFnames.SOFTWARE: _reader(Path(SectionTemplates.SOFTWARE.value)),
        LatexSectionFnames.ANCILLARY: _reader(Path(SectionTemplates.ANCILLARY.value)),
        LatexSectionFnames.GQA: _reader(Path(SectionTemplates.GQA.value)),
    }

    _write_metadata_sections(outdir, metadata_sections)

    # main document
    main_template = _reader(Path(SectionTemplates.MAIN.value))
    _write_main_section(outdir, main_template)

    _LOG.info("finished writing LaTeX documents")

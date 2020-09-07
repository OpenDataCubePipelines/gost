"""
Utils pertaining to the creation of the LaTeX reports.
"""
import io
from pathlib import Path
from typing import Dict, List
import geopandas  # type: ignore
import structlog  # type: ignore
import zstandard  # type: ignore

from gost.constants import (
    DirectoryNames,
    FileNames,
    MEASUREMENT_TEMPLATE,
    DOCUMENT_TEMPLATE,
)

_LOG = structlog.get_logger()


def _write_measurement_docs(
    gdf: geopandas.GeoDataFrame, outdir: Path, measurement_template: str
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
        basename = "{}.tex".format(name)
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
    measurement_doc_fnames: Dict[str, List], outdir: Path, document_template: str
) -> None:
    """Write each of the LaTeX main level product documents."""

    for product_group in measurement_doc_fnames:

        sub_doc_names = measurement_doc_fnames[product_group]

        section = "  \\subfile{{{s}}}\n"
        doc_sections = "".join([section.format(s=s) for s in sub_doc_names])

        out_string = document_template.format(
            product_group=product_group, sections=doc_sections
        )

        out_fname = outdir.joinpath(FileNames.REPORT.value.format(product_group))

        _LOG.info("writing tex document to disk", out_fname=str(out_fname))

        with open(out_fname, "w") as outf:
            outf.write(out_string)


def latex_documents(gdf: geopandas.GeoDataFrame, outdir: Path) -> None:
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

    with open(DOCUMENT_TEMPLATE, "rb") as src:
        dctx = zstandard.ZstdDecompressor()
        doc_template = io.TextIOWrapper(
            dctx.stream_reader(src), encoding="utf-8"
        ).read()

    _LOG.info("reading LaTeX measurement template")

    with open(MEASUREMENT_TEMPLATE, "rb") as src:
        dctx = zstandard.ZstdDecompressor()
        measurement_template = io.TextIOWrapper(
            dctx.stream_reader(src), encoding="utf-8"
        ).read()

    measurement_doc_fnames = _write_measurement_docs(gdf, outdir, measurement_template)

    _write_product_docs(measurement_doc_fnames, outdir, doc_template)

    _LOG.info("finished writing LaTeX documents")

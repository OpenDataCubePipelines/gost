from pathlib import Path
import numpy
import pandas
import rasterio
import structlog
from scipy import stats
from typing import Any, Dict, List, Tuple

from wagl.scripts.wagl_residuals import distribution

from gost.utils import ContiguityThemes, FmaskThemes
from gost.utils import TerrainShadowThemes, GeneralRecords
from gost.utils import FmaskRecords, TerrainShadowRecords, ContiguityRecords
from gost.utils import evaluate, evaluate_nulls, evaluate_themes
from gost.digest_yaml import Digestyaml


BAND_IDS: List[str] = ["1", "2", "3", "4", "5", "6", "7"]
CONTIGUITY_MEASUREMENT_NAMES: List[str] = [
    "oa_nbar_contiguity",
    "oa_nbart_contiguity",
    "nbar_contiguity",
    "nbart_contiguity",
]
SHADOW_MEASUREMENT_NAMES: List[str] = [
    "oa_combined_terrain_shadow",
    "terrain_shadow",
]
FMASK_MEASUREMENT_NAMES: List[str] = ["oa_fmask", "fmask"]
_LOG = structlog.get_logger()


def process_yamls(dataframe: pandas.DataFrame) -> Tuple[Dict[str, List[Any]], ...]:
    """Process dataframe containing records to process."""

    # initialise placeholders for the results
    general_records = GeneralRecords()
    fmask_records = FmaskRecords()
    contiguity_records = ContiguityRecords()
    shadow_records = TerrainShadowRecords()

    for i, row in dataframe.iterrows():
        _LOG.info(
            "processing document",
            yaml_doc_test=row.yaml_pathname_test,
            yaml_doc_reference=row.yaml_pathname_reference,
        )

        doc_test = Digestyaml(row.yaml_pathname_test)
        doc_reference = Digestyaml(row.yaml_pathname_reference)

        for meas in doc_test.measurements:
            _LOG.info(
                "processing measurement",
                measurement=meas,
            )

            fname_test = Path(row.yaml_pathname_test).parent.joinpath(
                doc_test.measurements[meas]["path"]
            )
            fname_reference = Path(row.yaml_pathname_reference).parent.joinpath(
                doc_reference.measurements[meas]["path"]
            )

            if not fname_reference.exists():
                _LOG.info(
                    "missing reference measurement",
                    measurement_reference=fname_reference,
                    measurement_test=fname_test,
                )
                continue

            if not fname_test.exists():
                _LOG.info(
                    "missing test measurement",
                    measurement_reference=fname_reference,
                    measurement_test=fname_test,
                )
                continue

            ref_ds = rasterio.open(fname_reference)
            test_ds = rasterio.open(fname_test)

            # size of full image in pixels (null and valid)
            size = numpy.prod(ref_ds.shape)

            # compute results
            if meas in FMASK_MEASUREMENT_NAMES:
                # the idea here is to analyse the thematic data differently
                fmask_records.add_base_info(
                    doc_reference, fname_reference, fname_test, size, meas
                )

                # thematic evaluation
                fmask_results = evaluate_themes(ref_ds, test_ds, FmaskThemes)
                for key in fmask_results:
                    value = fmask_results[key]
                    getattr(fmask_records, key).append(value)
            elif meas in CONTIGUITY_MEASUREMENT_NAMES:
                # base records
                contiguity_records.add_base_info(
                    doc_reference, fname_reference, fname_test, size, meas
                )

                # thematic evaluation
                contiguity_results = evaluate_themes(ref_ds, test_ds, ContiguityThemes)
                for key in contiguity_results:
                    value = contiguity_results[key]
                    getattr(contiguity_records, key).append(value)
            elif meas in SHADOW_MEASUREMENT_NAMES:
                # base records
                shadow_records.add_base_info(
                    doc_reference, fname_reference, fname_test, size, meas
                )

                # thematic evaluation
                shadow_results = evaluate_themes(ref_ds, test_ds, TerrainShadowThemes)
                for key in shadow_results:
                    value = shadow_results[key]
                    getattr(shadow_records, key).append(value)
            else:
                # null data evaluation
                null_info = evaluate_nulls(ref_ds, test_ds)
                general_records.percent_data_2_null.append(null_info[0])
                general_records.percent_null_2_data.append(null_info[1])

                diff = evaluate(ref_ds, test_ds)
                h = distribution(diff)

                # store results
                general_records.add_base_info(
                    doc_reference, fname_reference, fname_test, size, meas
                )

                if "nbar" in meas or meas in BAND_IDS:
                    # get difference as a percent reflectance (0->100)
                    general_records.min_residual.append(h["omin"] / 100)
                    general_records.max_residual.append(h["omax"] / 100)
                else:
                    general_records.min_residual.append(h["omin"])
                    general_records.max_residual.append(h["omax"])

                general_records.percent_different.append(
                    (diff != 0).sum() / diff.size * 100
                )

                # percentiles of the cumulative distribution
                h = distribution(numpy.abs(diff))
                hist = h["histogram"]
                cdf = numpy.cumsum(hist / hist.sum())
                p1_idx = numpy.searchsorted(cdf, 0.9)
                p2_idx = numpy.searchsorted(cdf, 0.99)
                pct_90 = h["loc"][p1_idx]
                pct_99 = h["loc"][p2_idx]

                # moments
                mean = numpy.mean(diff)
                stddev = numpy.std(diff, ddof=1)
                skewness = stats.skew(diff)
                kurtosis = stats.kurtosis(diff)

                # percentiles from cumulative distribution
                if "nbar" in meas or meas in BAND_IDS:
                    # get difference as a percent reflectance (0->100)
                    general_records.percentile_90.append(pct_90 / 100)
                    general_records.percentile_99.append(pct_99 / 100)
                    general_records.mean.append(mean / 100)
                    general_records.standard_deviation.append(stddev / 100)
                else:
                    general_records.percentile_90.append(pct_90)
                    general_records.percentile_99.append(pct_99)
                    general_records.mean.append(mean)
                    general_records.standard_deviation.append(stddev)

                general_records.skewness.append(skewness)
                general_records.kurtosis.append(kurtosis)

    results = (
        general_records.records,
        fmask_records.records,
        contiguity_records.records,
        shadow_records.records,
    )
    return results

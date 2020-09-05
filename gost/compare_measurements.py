from pathlib import Path
import numpy  # type: ignore
import pandas  # type: ignore
import structlog  # type: ignore
from scipy import stats  # type: ignore
from typing import Any, Dict, List, Tuple

from wagl.scripts.wagl_residuals import distribution  # type: ignore

from gost.utils import ContiguityThemes, FmaskThemes
from gost.utils import TerrainShadowThemes, GeneralRecords
from gost.utils import FmaskRecords, TerrainShadowRecords, ContiguityRecords
from gost.utils import evaluate, evaluate_nulls, evaluate_themes
from gost.odc_documents import load_odc_metadata


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

        doc_test = load_odc_metadata(Path(row.yaml_pathname_test))
        doc_reference = load_odc_metadata(Path(row.yaml_pathname_test))

        for measurement_name in doc_test.measurements:
            _LOG.info(
                "processing measurement",
                measurement=measurement_name,
            )

            test_measurement = doc_test.measurements[measurement_name]
            reference_measurement = doc_reference.measurements[measurement_name]

            if not reference_measurement.pathname().exists():
                _LOG.info(
                    "missing reference measurement",
                    measurement_reference=str(reference_measurement.pathname()),
                    measurement_test=str(test_measurement.pathname()),
                )
                continue

            if not test_measurement.pathname().exists():
                _LOG.info(
                    "missing test measurement",
                    measurement_reference=str(reference_measurement.pathname()),
                    measurement_test=str(test_measurement.pathname()),
                )
                continue

            # size of full image in pixels (null and valid)
            size = numpy.prod(test_measurement.shape)

            # compute results
            if measurement_name in FMASK_MEASUREMENT_NAMES:
                # the idea here is to analyse the thematic data differently
                fmask_records.add_base_info(
                    doc_reference,
                    reference_measurement.pathname(),
                    test_measurement.pathname(),
                    size,
                    measurement_name,
                )

                # thematic evaluation
                fmask_results = evaluate_themes(
                    reference_measurement, test_measurement, FmaskThemes
                )
                for key in fmask_results:
                    value = fmask_results[key]
                    getattr(fmask_records, key).append(value)
            elif measurement_name in CONTIGUITY_MEASUREMENT_NAMES:
                # base records
                contiguity_records.add_base_info(
                    doc_reference,
                    reference_measurement.pathname(),
                    test_measurement.pathname(),
                    size,
                    measurement_name,
                )

                # thematic evaluation
                contiguity_results = evaluate_themes(
                    reference_measurement, test_measurement, ContiguityThemes
                )
                for key in contiguity_results:
                    value = contiguity_results[key]
                    getattr(contiguity_records, key).append(value)
            elif measurement_name in SHADOW_MEASUREMENT_NAMES:
                # base records
                shadow_records.add_base_info(
                    doc_reference,
                    reference_measurement.pathname(),
                    test_measurement.pathname(),
                    size,
                    measurement_name,
                )

                # thematic evaluation
                shadow_results = evaluate_themes(
                    reference_measurement, test_measurement, TerrainShadowThemes
                )
                for key in shadow_results:
                    value = shadow_results[key]
                    getattr(shadow_records, key).append(value)
            else:
                # null data evaluation
                null_info = evaluate_nulls(reference_measurement, test_measurement)
                general_records.percent_data_2_null.append(null_info[0])
                general_records.percent_null_2_data.append(null_info[1])

                diff = evaluate(reference_measurement, test_measurement)
                h = distribution(diff)

                # store results
                general_records.add_base_info(
                    doc_reference,
                    reference_measurement.pathname(),
                    test_measurement.pathname(),
                    size,
                    measurement_name,
                )

                if "nbar" in measurement_name or measurement_name in BAND_IDS:
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
                if "nbar" in measurement_name or measurement_name in BAND_IDS:
                    # get difference as a percent reflectance (0->100)
                    general_records.percentile_90.append(pct_90 / 100)
                    general_records.percentile_99.append(pct_99 / 100)
                    general_records.mean_residual.append(mean / 100)
                    general_records.standard_deviation.append(stddev / 100)
                else:
                    general_records.percentile_90.append(pct_90)
                    general_records.percentile_99.append(pct_99)
                    general_records.mean_residual.append(mean)
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

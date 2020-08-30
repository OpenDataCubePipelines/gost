#!/usr/bin/env python

from pathlib import Path
import numpy
import rasterio
import structlog

from wagl.scripts.wagl_residuals import distribution

from gost.utils import ContiguityCategories, FmaskCategories
from gost.utils import TerrainShadowCategories, GeneralRecords
from gost.utils import FmaskRecords, TerrainShadowRecords, ContiguityRecords
from gost.utils import evaluate2, evaluate_nulls, evaluate_categories
from gost.digest_yaml import Digestyaml


BAND_IDS = ['1', '2', '3', '4', '5', '6', '7']
CONTIGUITY_MEASUREMENT_NAMES = [
    'oa_nbar_contiguity',
    'oa_nbart_contiguity',
    'nbar_contiguity',
    'nbart_contiguity'
]
SHADOW_MEASUREMENT_NAMES = [
    'oa_combined_terrain_shadow',
    'terrain_shadow'
]
FMASK_MEASUREMENT_NAMES = [
    'oa_fmask',
    'fmask'
]
_LOG = structlog.get_logger()


def process_yamls(dataframe):

    # initialise placeholders for the results
    general_records = GeneralRecords()
    fmask_records = FmaskRecords()
    contiguity_records = ContiguityRecords()
    shadow_records = TerrainShadowRecords()

    for i, row in dataframe.iterrows():
        _LOG.info('processing document', yaml_doc_test=row.yaml_pathname_test, yaml_doc_reference=row.yaml_pathname_reference)

        doc_test = Digestyaml(row.yaml_pathname_test)
        doc_reference = Digestyaml(row.yaml_pathname_reference)

        for meas in doc_test.measurements:
            _LOG.info(
                'processing measurement',
                measurement=meas,
            )

            fname_test = Path(row.yaml_pathname_test).parent.joinpath(doc_test.measurements[meas]['path'])
            fname_reference = Path(row.yaml_pathname_reference).parent.joinpath(doc_reference.measurements[meas]['path'])

            if not fname_reference.exists():
                _LOG.info(
                    'missing reference measurement',
                    measurement_reference=fname_reference,
                    measurement_test=fname_test
                )
                continue

            if not fname_test.exists():
                _LOG.info(
                    'missing test measurement',
                    measurement_reference=fname_reference,
                    measurement_test=fname_test
                )
                continue

            ref_ds = rasterio.open(fname_reference)
            test_ds = rasterio.open(fname_test)

            # compute results
            if meas in FMASK_MEASUREMENT_NAMES:
                # the idea here is to analyse the categorical data differently
                fmask_records.granule.append(doc_reference.granule)
                fmask_records.region_code.append(doc_reference.region_code)
                fmask_records.reference_fname.append(str(fname_reference))
                fmask_records.test_fname.append(str(fname_test))
                fmask_records.size.append(numpy.prod(ref_ds.shape))
                fmask_records.measurement.append(meas)

                # categorical evaluation
                fmask_results = evaluate_categories(
                    ref_ds,
                    test_ds,
                    FmaskCategories
                )
                for key in fmask_results:
                    value = fmask_results[key]
                    getattr(fmask_records, key).append(value)
            elif meas in CONTIGUITY_MEASUREMENT_NAMES:
                # base records
                contiguity_records.granule.append(doc_reference.granule)
                contiguity_records.region_code.append(doc_reference.region_code)
                contiguity_records.reference_fname.append(str(fname_reference))
                contiguity_records.test_fname.append(str(fname_test))
                contiguity_records.size.append(numpy.prod(ref_ds.shape))
                contiguity_records.measurement.append(meas)

                # categorical evaluation
                contiguity_results = evaluate_categories(
                    ref_ds,
                    test_ds,
                    ContiguityCategories
                )
                for key in contiguity_results:
                    value = contiguity_results[key]
                    getattr(contiguity_records, key).append(value)
            elif meas in SHADOW_MEASUREMENT_NAMES:
                # base records
                shadow_records.granule.append(doc_reference.granule)
                shadow_records.region_code.append(doc_reference.region_code)
                shadow_records.reference_fname.append(str(fname_reference))
                shadow_records.test_fname.append(str(fname_test))
                shadow_records.size.append(numpy.prod(ref_ds.shape))
                shadow_records.measurement.append(meas)

                # categorical evaluation
                shadow_results = evaluate_categories(
                    ref_ds,
                    test_ds,
                    TerrainShadowCategories
                )
                for key in shadow_results:
                    value = shadow_results[key]
                    getattr(shadow_records, key).append(value)
            else:
                # null data evaluation
                null_info = evaluate_nulls(ref_ds, test_ds)
                general_records.percent_data_2_null.append(null_info[0])
                general_records.percent_null_2_data.append(null_info[1])

                diff = evaluate2(ref_ds, test_ds)
                h = distribution(diff)

                # store results
                general_records.granule.append(doc_reference.granule)
                general_records.reference_fname.append(str(fname_reference))
                general_records.test_fname.append(str(fname_test))
                general_records.region_code.append(doc_reference.region_code)
                general_records.size.append(diff.size)
                general_records.measurement.append(meas)

                if 'nbar' in meas or meas in BAND_IDS:
                    # get difference as a percent reflectance (0->100)
                    general_records.min_residual.append(h['omin'] / 100)
                    general_records.max_residual.append(h['omax'] / 100)
                else:
                    general_records.min_residual.append(h['omin'])
                    general_records.max_residual.append(h['omax'])

                general_records.percent_different.append(
                    (diff != 0).sum() / diff.size * 100
                )

                # percentiles of the cumulative distribution
                h = distribution(numpy.abs(diff))
                hist = h['histogram']
                cdf = numpy.cumsum(hist / hist.sum())
                p1_idx = numpy.searchsorted(cdf, 0.9)
                p2_idx = numpy.searchsorted(cdf, 0.99)
                pct_90 = h['loc'][p1_idx]
                pct_99 = h['loc'][p2_idx]

                # percentiles from cumulative distribution
                if 'nbar' in meas or meas in BAND_IDS:
                    # get difference as a percent reflectance (0->100)
                    general_records.percentile_90.append(pct_90 / 100)
                    general_records.percentile_99.append(pct_99 / 100)
                else:
                    general_records.percentile_90.append(pct_90)
                    general_records.percentile_99.append(pct_99)

    results = (
        general_records.records,
        fmask_records.records,
        contiguity_records.records,
        shadow_records.records
    )
    return results

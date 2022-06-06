"""
GQA and ancillary comparison evaluation.
"""
from pathlib import Path
from typing import Any, Dict, List, Tuple
import pandas  # type: ignore
import structlog  # type: ignore

from gost.data_model import AncillaryInfo, GeometricQuality
from gost.odc_documents import load_odc_metadata, load_proc_info

_LOG = structlog.get_logger()


def compare_software(dataframe: pandas.DataFrame) -> pandas.DataFrame:
    """
    Retrieve the software versions from the first record.
    No real comparison as such. Merely extract into a table that
    can be presented later for visual comparison and context.
    """

    record = dataframe.iloc[0]

    ref_doc = load_proc_info(Path(record.proc_info_pathname_reference))
    test_doc = load_proc_info(Path(record.proc_info_pathname_test))

    data: Dict[str, List] = {"Name": list(), "Reference": list(), "Test": list()}

    for key, value in ref_doc.software_versions.items():
        data["Name"].append(key)
        data["Reference"].append(value.version)
        data["Test"].append(test_doc.software_versions[key].version)

    result = pandas.DataFrame(data)

    return result


def compare_gqa(
    reference_gqa: GeometricQuality, test_gqa: GeometricQuality
) -> Dict[str, Any]:
    """Compare the GQA fields."""

    result: Dict[str, Any] = dict()


    for field, value in test_gqa.fields.items():
        result[field] = reference_gqa.fields[field] - value

    return result


def compare_ancillary(
    reference_ancillary: AncillaryInfo, test_ancillary: AncillaryInfo
) -> Dict[str, Any]:
    """Compare the ancillary fields."""

    result: Dict[str, Any] = dict()

    ref_data = reference_ancillary.flatten()
    for field, value in test_ancillary.flatten().items():
        if field in ref_data:        
            result[field] = ref_data[field] - value

    return result


def process_yamls(
    dataframe: pandas.DataFrame,
) -> Tuple[Dict[str, List[Any]], Dict[str, List[Any]]]:
    """Compare gqa and ancillary fields."""

    doc = load_proc_info(Path(dataframe.iloc[0].proc_info_pathname_test))

    gqa_results: Dict[str, Any] = {key: [] for key in doc.geometric_quality.fields}
    ancillary_results: Dict[str, Any] = {key: [] for key in doc.ancillary.flatten()}

    gqa_results["reference_pathname"] = []
    gqa_results["test_pathname"] = []
    gqa_results["region_code"] = []
    gqa_results["granule_id"] = []

    ancillary_results["reference_pathname"] = []
    ancillary_results["test_pathname"] = []
    ancillary_results["region_code"] = []
    ancillary_results["granule_id"] = []

    for _, row in dataframe.iterrows():
        _LOG.info(
            "processing document",
            yaml_doc_test=row.proc_info_pathname_test,
            yaml_doc_reference=row.proc_info_pathname_reference,
        )

        doc_reference = load_odc_metadata(Path(row.yaml_pathname_reference))
        proc_info_test = load_proc_info(Path(row.proc_info_pathname_test))
        proc_info_reference = load_proc_info(Path(row.proc_info_pathname_reference))

        gqa_results["region_code"].append(doc_reference.region_code)
        gqa_results["granule_id"].append(doc_reference.granule_id)
        gqa_results["reference_pathname"].append(row.proc_info_pathname_reference)
        gqa_results["test_pathname"].append(row.proc_info_pathname_test)

        ancillary_results["region_code"].append(doc_reference.region_code)
        ancillary_results["granule_id"].append(doc_reference.granule_id)
        ancillary_results["reference_pathname"].append(row.proc_info_pathname_reference)
        ancillary_results["test_pathname"].append(row.proc_info_pathname_test)

        gqa_result = compare_gqa(
            proc_info_reference.geometric_quality, proc_info_test.geometric_quality
        )
        for key in gqa_result:
            gqa_results[key].append(gqa_result[key])

        ancillary_result = compare_ancillary(
            proc_info_reference.ancillary, proc_info_test.ancillary
        )

        for key in ancillary_result:
            ancillary_results[key].append(ancillary_result[key])

    return gqa_results, ancillary_results

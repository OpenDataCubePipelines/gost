"""
GQA comparison evaluation.
"""
from pathlib import Path
import pandas  # type: ignore
import structlog  # type: ignore
from typing import Any, Dict, List

from gost.odc_documents import load_odc_metadata, load_proc_info

_LOG = structlog.get_logger()


def process_yamls(dataframe: pandas.DataFrame) -> Dict[str, List[Any]]:
    """Compare gqa fields."""

    doc = load_proc_info(Path(dataframe.iloc[0].proc_info_pathname_test))

    results: Dict[str, Any] = {key: [] for key in doc.fields}

    results["reference_pathname"] = []
    results["test_pathname"] = []
    results["region_code"] = []
    results["granule_id"] = []

    for _, row in dataframe.iterrows():
        _LOG.info(
            "processing document",
            yaml_doc_test=row.proc_info_pathname_test,
            yaml_doc_reference=row.proc_info_pathname_reference,
        )

        doc_reference = load_odc_metadata(Path(row.yaml_pathname_reference))
        proc_info_test = load_proc_info(Path(row.proc_info_pathname_test))
        proc_info_reference = load_proc_info(Path(row.proc_info_pathname_reference))

        results["region_code"].append(doc_reference.region_code)
        results["granule_id"].append(doc_reference.granule_id)
        results["reference_pathname"].append(row.proc_info_pathname_reference)
        results["test_pathname"].append(row.proc_info_pathname_test)

        for field, value in proc_info_test.fields.items():
            results[field].append(proc_info_reference.fields[field] - value)

    return results

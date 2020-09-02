import pandas
import structlog
from typing import Any, Dict, List

from gost.digest_yaml import DigestProcInfo, Digestyaml

_LOG = structlog.get_logger()


def process_yamls(dataframe: pandas.DataFrame) -> Dict[str, List[Any]]:
    """Compare gqa fields."""

    doc = DigestProcInfo(dataframe.iloc[0].proc_info_pathname_test)
    results = {key: [] for key in doc.fields}
    results["reference_pathname"] = []
    results["test_pathname"] = []
    results["region_code"] = []
    results["granule"] = []

    for i, row in dataframe.iterrows():
        _LOG.info(
            "processing document",
            yaml_doc_test=row.proc_info_pathname_test,
            yaml_doc_reference=row.proc_info_pathname_reference,
        )

        doc_reference = Digestyaml(row.yaml_pathname_reference)
        proc_info_test = DigestProcInfo(row.proc_info_pathname_test)
        proc_info_reference = DigestProcInfo(row.proc_info_pathname_reference)

        results["region_code"].append(doc_reference.region_code)
        results["granule"].append(doc_reference.granule)
        results["reference_pathname"].append(row.proc_info_pathname_reference)
        results["test_pathname"].append(row.proc_info_pathname_test)

        for field in proc_info_test.fields:
            results[field].append(
                proc_info_reference.fields[field] - proc_info_test.fields[field]
            )

    return results

from pathlib import Path
import pytest

from gost.odc_documents import load_odc_metadata, load_proc_info
from . import LS5_ODC_DOC_PATH, LS7_ODC_DOC_PATH, LS8_ODC_DOC_PATH
from . import LS5_ODC_PROC_PATH, LS7_ODC_PROC_PATH, LS8_ODC_PROC_PATH


# Run these tests first
# (note; a bug in pytest is preventing ordering; #55 is supposed to have fixed it)
@pytest.mark.first
@pytest.mark.parametrize(
    "doc_path", [LS5_ODC_DOC_PATH, LS7_ODC_DOC_PATH, LS8_ODC_DOC_PATH]
)
def test_load_odc(doc_path: Path):
    """Check that no exception is raised when loading the yaml document."""
    try:
        load_odc_metadata(doc_path)
    except Exception as exc:
        assert False, f"'load_odc_metadata' raised an exception: {exc}"


@pytest.mark.second
@pytest.mark.parametrize(
    "doc_path", [LS5_ODC_PROC_PATH, LS7_ODC_PROC_PATH, LS8_ODC_PROC_PATH]
)
def test_load_proc(doc_path: Path):
    """Check that no exception is raised when loading the yaml document."""
    try:
        load_proc_info(doc_path)
    except Exception as exc:
        assert False, f"'load_proc_info' raised an exception: {exc}"

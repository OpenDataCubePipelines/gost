import pytest
import numpy

M999 = -999
REF_DATA1 = numpy.array(
    [[0, 1, 2, 3], [1, 2, 3, 4], [2, 3, 4, 5], [0, 5, 4, 3]], dtype="uint8"
)
REF_DATA2 = numpy.array(
    [
        [M999, 1000, 2000, 3000],
        [M999, 2000, 3000, 4000],
        [M999, 3000, 4000, 5000],
        [M999, 5000, 4000, 3000],
    ],
    dtype="int16",
)
REF_DATA3 = numpy.array(
    [
        [0, 0, 0, 0, 0, 0, 0],
        [1, 1, 1, 1, 1, 1, 1],
        [2, 2, 2, 2, 2, 2, 2],
        [3, 3, 3, 3, 3, 3, 3],
        [4, 4, 4, 4, 4, 4, 4],
        [5, 5, 5, 5, 5, 5, 5],
    ],
    dtype="uint8",
)
TEST_DATA1 = numpy.array(
    [[0, 1, 2, 3], [1, 2, 3, 4], [2, 3, 4, 5], [0, 5, 4, 3]], dtype="uint8"
)
TEST_DATA2 = numpy.array(
    [[0, 5, 2, 3], [1, 2, 1, 4], [2, 3, 4, 5], [0, 5, 4, 3]], dtype="uint8"
)
TEST_DATA3 = numpy.array(
    [
        [M999, 1000, 2000, 3000],
        [M999, 2000, 3000, 4000],
        [M999, 3000, 4000, 5000],
        [M999, 5000, 4000, 3000],
    ],
    dtype="int16",
)
TEST_DATA4 = numpy.array(
    [
        [6000, 1000, 2000, M999],
        [7000, 2000, 3000, M999],
        [M999, 3000, 4000, M999],
        [M999, 5000, 4000, M999],
    ],
    dtype="int16",
)
TEST_DATA5 = numpy.array(
    [
        [6000, 100, 200, M999],
        [7000, 200, 300, M999],
        [M999, 300, 400, M999],
        [M999, 500, 400, M999],
    ],
    dtype="int16",
)
TEST_DATA6 = numpy.array(
    [
        [0, 1, 2, 3, 4, 5, 0],
        [1, 2, 3, 4, 5, 0, 1],
        [2, 3, 4, 5, 0, 1, 2],
        [3, 4, 5, 0, 1, 2, 3],
        [4, 5, 0, 1, 2, 3, 4],
        [5, 0, 1, 2, 3, 4, 5],
    ],
    dtype="uint8",
)


class Measurement:
    """Dummy instance of gost.data_model.Measurement"""

    def __init__(self, data, nodata):
        self.data = data
        self.nodata = nodata

    def read(self):
        return self.data


@pytest.fixture
def ref_fmask_measurement1():
    return Measurement(REF_DATA1, 0)


@pytest.fixture
def ref_fmask_measurement2():
    return Measurement(REF_DATA3, 0)


@pytest.fixture
def test_fmask_measurement1():
    return Measurement(TEST_DATA1, 0)


@pytest.fixture
def test_fmask_measurement2():
    return Measurement(TEST_DATA2, 0)


@pytest.fixture
def test_fmask_measurement3():
    return Measurement(TEST_DATA6, 0)


@pytest.fixture
def ref_reflectance_measurement():
    return Measurement(REF_DATA2, M999)


@pytest.fixture
def test_reflectance_measurement1():
    return Measurement(TEST_DATA3, M999)


@pytest.fixture
def test_reflectance_measurement2():
    return Measurement(TEST_DATA4, M999)


@pytest.fixture
def test_reflectance_measurement3():
    return Measurement(TEST_DATA5, M999)

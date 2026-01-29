import os
import tempfile
import numpy as np
import h5py
import pytest
import msagui.parseH5 as parseH5

@pytest.fixture
def temp_h5_file():
    # Create a temporary HDF5 file for testing
    fd, path = tempfile.mkstemp(suffix=".h5")
    os.close(fd)
    try:
        with h5py.File(path, "w") as f:
            f.create_dataset("test_data", data=np.arange(10))
        yield path
    finally:
        if os.path.exists(path):
            os.remove(path)

def test_get_data_single_key(temp_h5_file):
    arr = parseH5.get_data(temp_h5_file, "test_data")
    assert isinstance(arr, list)
    assert np.array_equal(arr[0], np.arange(10))

def test_get_data_multiple_keys(temp_h5_file):
    with h5py.File(temp_h5_file, "a") as f:
        f.create_dataset("other_data", data=np.ones(5))
    arrs = parseH5.get_data(temp_h5_file, ["test_data", "other_data"])
    assert len(arrs) == 2
    assert np.array_equal(arrs[0], np.arange(10))
    assert np.array_equal(arrs[1], np.ones(5))

def test_add_processed_and_delete(temp_h5_file):
    img = np.random.rand(4, 4)
    parseH5.add_processed(temp_h5_file, "processed_img", img)
    with h5py.File(temp_h5_file, "r") as f:
        assert "processed_img" in f
        assert np.allclose(f["processed_img"][:], img)
        assert f["processed_img"].attrs["type"] == "processed"
    parseH5.delete(temp_h5_file, "processed_img")
    with h5py.File(temp_h5_file, "r") as f:
        assert "processed_img" not in f

def test_add_input_and_delete(temp_h5_file):
    fake_path = "/tmp/fake_image.tif"
    parseH5.add_input(temp_h5_file, "input_img", fake_path)
    with h5py.File(temp_h5_file, "r") as f:
        assert "input_img" in f
        assert f["input_img"][()] == fake_path.encode()  # h5py stores strings as bytes
        assert f["input_img"].attrs["type"] == "input"
    parseH5.delete(temp_h5_file, "input_img")
    with h5py.File(temp_h5_file, "r") as f:
        assert "input_img" not in f

def test_overwrite_dataset(temp_h5_file):
    img1 = np.zeros((2, 2))
    img2 = np.ones((2, 2))
    parseH5.add_processed(temp_h5_file, "overwrite_img", img1)
    parseH5.add_processed(temp_h5_file, "overwrite_img", img2)
    with h5py.File(temp_h5_file, "r") as f:
        assert np.allclose(f["overwrite_img"][:], img2)
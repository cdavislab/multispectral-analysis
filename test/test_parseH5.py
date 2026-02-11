import os
import tempfile
import numpy as np
import h5py
import pytest
import msagui.model.parseH5 as parseH5

@pytest.fixture
def temp_h5_file():
    # Create a temporary HDF5 file for testing
    fd, path = tempfile.mkstemp(suffix=".h5")
    os.close(fd)
    try:
        with h5py.File(path, "w") as f:
            f.create_dataset("test_data", data=np.arange(10))
            f["test_data"].attrs["type"] = "array"
        yield path
    finally:
        if os.path.exists(path):
            os.remove(path)

@pytest.fixture
def temp_h5_file_with_str(temp_h5_file):
    with h5py.File(temp_h5_file, "a") as f:
        dset = f.create_dataset("test_str", data="hello world".encode())
        dset.attrs["type"] = "str"
    return temp_h5_file

def test_get_data_single_key(temp_h5_file):
    arr = parseH5.get_data(temp_h5_file, "test_data")
    # Set attribute as 'array' to simulate the expected type

    assert isinstance(arr, list)
    assert np.array_equal(arr[0], np.arange(10))

def test_get_data_multiple_keys(temp_h5_file):
    with h5py.File(temp_h5_file, "a") as f:
        f.create_dataset("other_data", data=np.ones(5))
        f["other_data"].attrs["type"] = "array"
    arrs = parseH5.get_data(temp_h5_file, ["test_data", "other_data"])
    assert len(arrs) == 2
    assert np.array_equal(arrs[0], np.arange(10))
    assert np.array_equal(arrs[1], np.ones(5))

def test_add_processed_and_delete(temp_h5_file):
    img = np.random.rand(4, 4)
    parseH5.add_processed(temp_h5_file, "processed_img", img)
    with h5py.File(temp_h5_file, "r") as f:
        assert "processed_img" in f
        assert np.allclose(f["processed_img"][:], img) # pyright: ignore[reportArgumentType, reportIndexIssue]
        assert f["processed_img"].attrs["type"] == "array"
    parseH5.delete(temp_h5_file, "processed_img")
    with h5py.File(temp_h5_file, "r") as f:
        assert "processed_img" not in f

def test_add_input_and_delete(temp_h5_file):
    fake_path = "/tmp/fake_image.tif"
    parseH5.add_input(temp_h5_file, "input_img", fake_path)
    with h5py.File(temp_h5_file, "r") as f:
        assert "input_img" in f
        assert f["input_img"][()] == fake_path.encode()  # pyright: ignore[reportIndexIssue] # h5py stores strings as bytes 
        assert f["input_img"].attrs["type"] == "str"
    parseH5.delete(temp_h5_file, "input_img")
    with h5py.File(temp_h5_file, "r") as f:
        assert "input_img" not in f

def test_overwrite_dataset(temp_h5_file):
    img1 = np.zeros((2, 2))
    img2 = np.ones((2, 2))
    parseH5.add_processed(temp_h5_file, "overwrite_img", img1)
    parseH5.add_processed(temp_h5_file, "overwrite_img", img2)
    with h5py.File(temp_h5_file, "r") as f:
        assert np.allclose(f["overwrite_img"][:], img2)  # pyright: ignore[reportArgumentType, reportIndexIssue]

def test_decode_dataset_with_bytes(temp_h5_file):
    fake_path = "/tmp/fake_image.csv"
    print(f"Creating fake image file at {fake_path}")
    print(temp_h5_file)
    # Create a dummy file so loader.load can read it
    arr = np.random.rand(4, 4)
    np.savetxt(fake_path, arr, delimiter=",")  # Or use open(fake_path, 'wb').write(...) if loader expects a TIFF

    with h5py.File(temp_h5_file, "a") as f:
        dset = f.create_dataset("bytes_data", data=fake_path.encode())
        dset.attrs["type"] = "str"
    result = parseH5.get_data(temp_h5_file, "bytes_data")
    assert isinstance(result, list)
    assert result[0].shape == (4, 4)

    # Clean up
    os.remove(fake_path)

def test_decode_dataset_with_array(temp_h5_file):
    arr = np.random.rand(3, 3)
    with h5py.File(temp_h5_file, "a") as f:
        dset = f.create_dataset("array_data", data=arr)
        dset.attrs["type"] = "array"
    result = parseH5.get_data(temp_h5_file, "array_data")
    assert isinstance(result, list)
    assert np.allclose(result[0], arr)  # pyright: ignore[reportArgumentType, reportIndexIssue]
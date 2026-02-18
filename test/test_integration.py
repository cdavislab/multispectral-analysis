import pytest
import h5py
import numpy as np
from msagui.model.model import MultiSpectralModel

@pytest.fixture
def temp_hdf5(tmp_path):
    hdf5_path = tmp_path / "test_model.h5"
    # Create img1 and img2 as csv files
    return str(hdf5_path)

@pytest.fixture
def temp_img_paths(tmp_path):
    img1_path = tmp_path / "data_img1.csv"
    img2_path = tmp_path / "data_img2.csv"
    np.savetxt(img1_path, np.ones((5, 5)), delimiter=",")
    np.savetxt(img2_path, np.full((5, 5), 2), delimiter=",")
    return [str(img1_path), str(img2_path)]

def test_single_step(temp_hdf5, temp_img_paths):
    model = MultiSpectralModel()
    model.set_hdf5_path(temp_hdf5)
    model.add(temp_img_paths, lambda: None)
    with h5py.File(temp_hdf5, "r") as f:
        assert "default/1" in f
        assert "default/2" in f
    model.steps.set_steps([{"keyword1": "img1", "operation": "+", "keyword2": "img2", "value": "", "output_key": "result"}])
    model.set_keywords()
    model.set_groups()
    with h5py.File(temp_hdf5, "r") as f:
        assert "1/img1" in f
        assert "1/img2" in f
    model.analyze([0, 1], lambda: None)
    with h5py.File(temp_hdf5, "r") as f:
        assert "1/result" in f
        result_data = f["1/result"][:]
        expected = np.ones((5, 5)) + np.full((5, 5), 2)
        assert np.allclose(result_data, expected)

def test_multistep(temp_hdf5, temp_img_paths):
    model = MultiSpectralModel()
    model.set_hdf5_path(temp_hdf5)
    model.add(temp_img_paths, lambda: None)
    with h5py.File(temp_hdf5, "r") as f:
        assert "default/1" in f
        assert "default/2" in f
    model.steps.set_steps([{"keyword1": "img1", "operation": "+", "keyword2": "img2", "value": "", "output_key": "result"},
                           {"keyword1": "result", "operation": "-", "keyword2": "img2", "value": "", "output_key": "computed_img1"}])
    model.set_keywords()
    model.set_groups()
    with h5py.File(temp_hdf5, "r") as f:
        assert "1/img1" in f
        assert "1/img2" in f
    model.analyze([0, 1], lambda: None)
    with h5py.File(temp_hdf5, "r") as f:
        assert "1/result" in f
        result_data = f["1/result"][:]
        expected = np.ones((5, 5)) + np.full((5, 5), 2)
        assert np.allclose(result_data, expected)
        assert "1/computed_img1" in f
        computed_data = f["1/computed_img1"][:]
        computed_expected = expected - np.full((5, 5), 2)
        assert np.allclose(computed_data, computed_expected)
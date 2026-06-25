import pytest
import h5py
import numpy as np
from pathlib import Path
from msagui.model.model import MultiSpectralModel

@pytest.fixture
def temp_hdf5(tmp_path: Path) -> str:
    hdf5_path = tmp_path / "test_model.h5"
    # Create img1 and img2 as csv files
    return str(hdf5_path)

@pytest.fixture
def temp_img_paths(tmp_path: Path) -> list[str]:
    img1_path = tmp_path / "data_img1.csv"
    img2_path = tmp_path / "data_img2.csv"
    np.savetxt(img1_path, np.ones((5, 5)), delimiter=",")
    np.savetxt(img2_path, np.full((5, 5), 2), delimiter=",")
    return [str(img1_path), str(img2_path)]

def test_single_step(temp_hdf5: str, temp_img_paths: list[str]) -> None:
    """Verify a single add-step produces expected result dataset in grouped output."""
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

def test_multistep(temp_hdf5: str, temp_img_paths: list[str]) -> None:
    """Verify multi-step pipelines persist intermediate and final computed datasets."""
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
        assert f.keys() >= {"1/img1", "1/img2"}  # Check that both img1 and img2 are present in group 1
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

def test_double_analyze(temp_hdf5: str, temp_img_paths: list[str]) -> None:
    """Verify repeated analyze calls keep result datasets consistent."""
    model = MultiSpectralModel()
    model.set_hdf5_path(temp_hdf5)
    model.add(temp_img_paths, lambda: None)
    model.steps.set_steps([{"keyword1": "img1", "operation": "+", "keyword2": "img2", "value": "", "output_key": "result"}])
    model.set_keywords()
    model.set_groups()
    model.analyze([0, 1], lambda: None)
    # Analyze again with the same settings to test caching
    model.analyze([0, 1, 2], lambda: None)
    with h5py.File(temp_hdf5, "r") as f:
        assert "1/result" in f
        result_data = f["1/result"][:]
        expected = np.ones((5, 5)) + np.full((5, 5), 2)
        assert np.allclose(result_data, expected)

def test_double_analyze1(temp_hdf5: str, temp_img_paths: list[str]) -> None:
    """Verify grouping and metadata state after analyze setup for paired inputs."""
    model = MultiSpectralModel()
    model.set_hdf5_path(temp_hdf5)
    model.add(temp_img_paths, lambda: None)
    model.steps.set_steps([{"keyword1": "img1", "operation": "+", "keyword2": "img2", "value": "", "output_key": "result"}])
    model.set_keywords()
    model.set_groups()
    assert model.metadata.keys == ["1", "2"]
    assert model.metadata.groups() == [1]
    assert model.metadata.nicknames() == temp_img_paths

def test_single_keyword_twice(temp_hdf5: str, temp_img_paths: list[str]) -> None:
    """Verify grouping behavior when a step reuses the same keyword twice."""
    model = MultiSpectralModel()
    model.set_hdf5_path(temp_hdf5)
    model.add(temp_img_paths, lambda: None)
    model.steps.set_steps([{"keyword1": "img1", "operation": "+", "keyword2": "img1", "value": "", "output_key": "result"}])
    model.set_keywords()
    model.set_groups()
    assert model.metadata.keys == ["1", "2"]
    assert model.metadata.groups() == [1, "default"]
    assert set(model.metadata.nicknames()) == set(temp_img_paths)

def test_addition(temp_hdf5: str, temp_img_paths: list[str]) -> None:
    """Verify addition operation produces correct numeric output."""
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

def test_subtraction(temp_hdf5: str, temp_img_paths: list[str]) -> None:
    """Verify subtraction operation produces correct numeric output."""
    model = MultiSpectralModel()
    model.set_hdf5_path(temp_hdf5)
    model.add(temp_img_paths, lambda: None)
    with h5py.File(temp_hdf5, "r") as f:
        assert "default/1" in f
        assert "default/2" in f
    model.steps.set_steps([{"keyword1": "img1", "operation": "-", "keyword2": "img2", "value": "", "output_key": "result"}])
    model.set_keywords()
    model.set_groups()
    with h5py.File(temp_hdf5, "r") as f:
        assert "1/img1" in f
        assert "1/img2" in f
    model.analyze([0, 1], lambda: None)
    with h5py.File(temp_hdf5, "r") as f:
        assert "1/result" in f
        result_data = f["1/result"][:]
        expected = np.ones((5, 5)) - np.full((5, 5), 2)
        assert np.allclose(result_data, expected)

def test_division(temp_hdf5: str, temp_img_paths: list[str]) -> None:
    """Verify division operation produces correct numeric output."""
    model = MultiSpectralModel()
    model.set_hdf5_path(temp_hdf5)
    model.add(temp_img_paths, lambda: None)
    with h5py.File(temp_hdf5, "r") as f:
        assert "default/1" in f
        assert "default/2" in f
    model.steps.set_steps([{"keyword1": "img1", "operation": "/", "keyword2": "img2", "value": "", "output_key": "result"}])
    model.set_keywords()
    model.set_groups()
    with h5py.File(temp_hdf5, "r") as f:
        assert "1/img1" in f
        assert "1/img2" in f
    model.analyze([0, 1], lambda: None)
    with h5py.File(temp_hdf5, "r") as f:
        assert "1/result" in f
        result_data = f["1/result"][:]
        expected = np.ones((5, 5)) / np.full((5, 5), 2)
        assert np.allclose(result_data, expected)

def test_multiplication(temp_hdf5: str, temp_img_paths: list[str]) -> None:
    """Verify multiplication operation produces correct numeric output."""
    model = MultiSpectralModel()
    model.set_hdf5_path(temp_hdf5)
    model.add(temp_img_paths, lambda: None)
    with h5py.File(temp_hdf5, "r") as f:
        assert "default/1" in f
        assert "default/2" in f
    model.steps.set_steps([{"keyword1": "img1", "operation": "*", "keyword2": "img2", "value": "", "output_key": "result"}])
    model.set_keywords()
    model.set_groups()
    with h5py.File(temp_hdf5, "r") as f:
        assert "1/img1" in f
        assert "1/img2" in f
    model.analyze([0, 1], lambda: None)
    with h5py.File(temp_hdf5, "r") as f:
        assert "1/result" in f
        result_data = f["1/result"][:]
        expected = np.ones((5, 5)) * np.full((5, 5), 2)
        assert np.allclose(result_data, expected)

def test_multiplication_by_value(temp_hdf5: str, temp_img_paths: list[str]) -> None:
    """Verify scalar multiplication via value field produces expected output."""
    model = MultiSpectralModel()
    model.set_hdf5_path(temp_hdf5)
    model.add(temp_img_paths, lambda: None)
    with h5py.File(temp_hdf5, "r") as f:
        assert "default/1" in f
        assert "default/2" in f
    model.steps.set_steps([{"keyword1": "img1", "operation": "*", "keyword2": "", "value": "3", "output_key": "result"}])
    model.set_keywords()
    model.set_groups()
    with h5py.File(temp_hdf5, "r") as f:
        assert "1/img1" in f
        assert "default/2" in f
    model.analyze([0, 1], lambda: None)
    with h5py.File(temp_hdf5, "r") as f:
        assert "1/result" in f
        result_data = f["1/result"][:]
        expected = np.ones((5, 5)) * 3
        assert np.allclose(result_data, expected)

def test_threshold(temp_hdf5: str, temp_img_paths: list[str]) -> None:
    """Verify proportion-of-max threshold step writes expected output dataset."""
    model = MultiSpectralModel()
    model.set_hdf5_path(temp_hdf5)
    model.add(temp_img_paths, lambda: None)
    with h5py.File(temp_hdf5, "r") as f:
        assert "default/1" in f
        assert "default/2" in f
    model.steps.set_steps([{"keyword1": "img1", "operation": "maxthresh", 'keyword2': "", "value": "0.5", "output_key": "result"}])
    model.set_keywords()
    model.set_groups()
    with h5py.File(temp_hdf5, "r") as f:
        assert "1/img1" in f
        assert "default/2" in f
    model.analyze([0, 1], lambda: None)
    with h5py.File(temp_hdf5, "r") as f:
        assert "1/result" in f
        result_data = f["1/result"][:]
        expected = np.ones((5, 5)) > 0.5
        assert np.allclose(result_data, expected)
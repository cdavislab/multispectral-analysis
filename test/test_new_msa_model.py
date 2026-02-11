import numpy as np
import h5py
import pytest
from msagui.model.model import MultiSpectralModel
from msagui.model.steps import Steps

@pytest.fixture
def temp_hdf5(tmp_path):
	hdf5_path = tmp_path / "test_model.h5"
	with h5py.File(hdf5_path, "w") as f:
		f.create_dataset("img1", data=np.ones((5, 5)))
		f.create_dataset("img2", data=np.full((5, 5), 2))
	return str(hdf5_path)

def test_set_hdf5_path():
	model = MultiSpectralModel()
	model.set_hdf5_path("abc.h5")
	assert model.hdf5_path == "abc.h5"

def test_add_and_delete(monkeypatch, tmp_path):
	model = MultiSpectralModel()
	hdf5_path = tmp_path / "test_add.h5"
	model.set_hdf5_path(str(hdf5_path))
	# Patch parseH5.add_input and parseH5.delete
	monkeypatch.setattr("msagui.model.parseH5.add_input", lambda hdf5, key, path: None)
	monkeypatch.setattr("msagui.model.parseH5.delete", lambda hdf5, key: None)
	# Patch progress_callback to a no-op
	progress_callback = lambda: None
	model.add("file1.tif", progress_callback)
	assert len(model.metadata.items) == 1
	model.delete(0, progress_callback)
	assert len(model.metadata.items) == 0

# def test_set_keywords_and_groups(monkeypatch):
# 	model = MultiSpectralModel()
# 	# Add fake metadata
# 	model.metadata.items = []
# 	model.metadata.keys = ["imgA", "imgB"]
# 	model.metadata.add = lambda meta: model.metadata.items.append(meta)
# 	model.metadata.change_keyword = lambda key, kw: None # type: ignore
# 	model.metadata.delete = lambda key: None
# 	# Patch steps.inputs and match_substr
# 	model.steps.set_steps([{"keyword1": "imgA"}, {"keyword2": "imgB"}])
# 	monkeypatch.setattr("msagui.model.msa_utils.match_substr", lambda keywords, basenames: {"imgA": ["imgA"], "imgB": ["imgB"]})
# 	monkeypatch.setattr("msagui.model.msa_utils.remove_substr", lambda keywords, basename: basename)
# 	monkeypatch.setattr("msagui.model.msa_utils.group_strlist", lambda names: [0, 1])
# 	model.set_keywords()
# 	model.set_groups()

def test_get_images(monkeypatch, temp_hdf5):
	model = MultiSpectralModel()
	model.set_hdf5_path(temp_hdf5)
	# Patch msagui.model.parseH5.get_data
	monkeypatch.setattr("msagui.model.parseH5.get_data", lambda hdf5, keys: [np.ones((5, 5)) for _ in keys])
	arrs = model.get_images(["img1", "img2"])
	assert len(arrs) == 2
	assert np.allclose(arrs[0], np.ones((5, 5)))

def test_process_step(monkeypatch):
	model = MultiSpectralModel()
	# Patch get_images
	model.get_images = lambda keys: [np.ones((2, 2)), np.full((2, 2), 2)]
	group = {"A": "img1", "B": "img2"}
	step = {"keyword1": "A", "keyword2": "B", "operation": "+", "output_key": "C"}
	# Monkeypatch 
	result = model.process_step(group, step)
	assert np.allclose(result, 3)
	# Test threshold
	step = {"keyword1": "A", "keyword2": "", "operation": "threshold", "output_key": "C", "value": 0.5}
	model.get_images = lambda key: np.array([[0.2, 0.6], [0.7, 0.1]]) # type: ignore
	result = model.process_step(group, step)
	assert np.allclose(result, [[0, 0.6], [0.7, 0]])

def test_analyze_group(monkeypatch):
	model = MultiSpectralModel()
	# Patch steps
	steps = [
		{"keyword1": "A", "keyword2": "B", "operation": "+", "output_key": "C"},
		{"keyword1": "C", "keyword2": "", "operation": "threshold", "output_key": "D", "value": 1}
	]
	model.steps.set_steps(steps)
	model.steps.last_used = lambda: {"C": 0, "D": 1}
	model.get_images = lambda keys: [np.ones((2, 2)), np.ones((2, 2))]
	model.process_step = lambda group, step: np.ones((2, 2))
	group = {"A": "img1", "B": "img2", "C": "img3"}
	model._analyze(group, "A",lambda: None)
	assert isinstance(model.group_cache, dict)

def test_steps_inputs_and_last_used():
	steps = Steps()
	steps.set_steps([
		{"input1": "A", "keyword1": "A", "keyword2": "B"},
		{"input2": "B", "keyword1": "B", "keyword2": ""}
	])
	inputs = steps.inputs()
	assert set(inputs) == {"A", "B"}
	last = steps.last_used()
	assert last["A"] == 0
	assert last["B"] == 1

def test_steps_set_and_get():
	steps = Steps()
	s = [{"input1": "A"}]
	steps.set_steps(s)
	assert steps.get_steps() == s
import numpy as np
import h5py
import pytest
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Any, cast
from msagui.model.model import MultiSpectralModel
from msagui.model.steps import Steps

@pytest.fixture
def temp_hdf5(tmp_path: Path) -> str:
	hdf5_path = tmp_path / "test_model.h5"
	with h5py.File(hdf5_path, "w") as f:
		f.create_dataset("img1", data=np.ones((5, 5)))
		f.create_dataset("img2", data=np.full((5, 5), 2))
	return str(hdf5_path)

def test_set_hdf5_path() -> None:
	"""Verify set_hdf5_path updates the model's active HDF5 file path."""
	model = MultiSpectralModel()
	model.set_hdf5_path("abc.h5")
	assert model.hdf5_path == "abc.h5"

def test_add_and_delete(monkeypatch: Any, tmp_path: Path) -> None:
	"""Verify add and delete update metadata count using patched HDF5 operations."""
	model = MultiSpectralModel()
	hdf5_path = tmp_path / "test_add.h5"
	model.set_hdf5_path(str(hdf5_path))
	# Patch parseH5.add_input and parseH5.delete
	monkeypatch.setattr("msagui.model.loader.load", lambda path: np.ones((2, 2)))
	monkeypatch.setattr("msagui.model.parseH5.add_input", lambda hdf5, key, path: None)
	monkeypatch.setattr("msagui.model.parseH5.delete", lambda hdf5, key: None)
	# Patch progress_callback to a no-op
	progress_callback = lambda: None
	model.add("file1.tif", progress_callback)
	assert len(model.metadata.items) == 1
	model.delete(0, progress_callback)
	assert len(model.metadata.items) == 0

def test_add_skips_invalid_files_and_reports_friendly_error(monkeypatch: Any) -> None:
	"""Verify add validates input content and only adds files that can be read."""
	model = MultiSpectralModel()
	monkeypatch.setattr("msagui.model.parseH5.add_input", lambda hdf5, key, path: None)

	def fake_load(path: str) -> Any:
		if "invalid" in path:
			raise ValueError("Could not read '/tmp/invalid.csv': file contains non-numeric text.")
		return np.ones((2, 2))

	monkeypatch.setattr("msagui.model.loader.load", fake_load)

	errors = model.add(["/tmp/valid.csv", "/tmp/invalid.csv"], progress_callback=None)

	assert len(model.metadata.items) == 1
	assert model.metadata.items[0].nickname == "/tmp/valid.csv"
	assert "/tmp/invalid.csv" in errors
	assert "non-numeric text" in str(errors["/tmp/invalid.csv"])

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

def test_get_images(monkeypatch: Any, temp_hdf5: str) -> None:
	"""Verify get_images returns arrays for requested keys in order."""
	model = MultiSpectralModel()
	model.set_hdf5_path(temp_hdf5)
	# Patch msagui.model.parseH5.get_data
	monkeypatch.setattr("msagui.model.parseH5.get_data", lambda hdf5, keys: [np.ones((5, 5)) for _ in keys])
	arrs = model.get_images(["img1", "img2"])
	assert len(arrs) == 2
	assert np.allclose(arrs[0], np.ones((5, 5)))

def test_process_step(monkeypatch: Any) -> None:
	"""Verify process_step handles binary operations and NaN-masking threshold operations."""
	model = MultiSpectralModel()
	# Patch get_images
	model.get_images = lambda keys: [np.ones((2, 2)), np.full((2, 2), 2)]
	group = {"A": "img1", "B": "img2"}
	step = {"keyword1": "A", "keyword2": "B", "operation": "+", "output_key": "C"}
	# Monkeypatch 
	result = model.process_step(group, step)
	assert np.allclose(result, 3)
	# Test proportion-of-max threshold
	step = {"keyword1": "A", "keyword2": "", "operation": "maxthresh", "output_key": "C", "value": 0.5}
	model.get_images = lambda key: np.array([[0.2, 0.6], [0.7, 0.1]]) # type: ignore
	result = model.process_step(group, step)
	assert np.allclose(result, [[np.nan, 0.6], [0.7, np.nan]], equal_nan=True)

	# Test constant threshold
	step = {"keyword1": "A", "keyword2": "", "operation": "threshold", "output_key": "C", "value": 0.5}
	model.get_images = lambda key: np.array([[0.2, 0.6], [0.7, 0.1]]) # type: ignore
	result = model.process_step(group, step)
	assert np.allclose(result, [[np.nan, 0.6], [0.7, np.nan]], equal_nan=True)

	# Test image threshold
	step = {"keyword1": "A", "keyword2": "B", "operation": "threshold", "output_key": "C", "value": ""}
	model.get_images = lambda keys: [ # type: ignore
		np.array([[0.2, 0.6], [0.7, 0.1]]),
		np.array([[0.1, 0.7], [0.6, 0.1]]),
	]
	result = model.process_step(group, step)
	assert np.allclose(result, [[0.2, np.nan], [0.7, 0.1]], equal_nan=True)

def test_analyze_group(monkeypatch: Any) -> None:
	"""Verify _analyze populates group cache and processes configured steps."""
	class DummyMeta:
		def __init__(self, common_name: list[str]) -> None:
			self.common_name = common_name
			
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
	model.metadata.by_group = lambda group_id: [DummyMeta(["test", "processed"])]  # type: ignore
	group = {"A": "img1", "B": "img2", "C": "img3"}
	model._analyze(group, "A",lambda: None)
	assert isinstance(model.group_cache, dict)

def test_steps_inputs_and_last_used() -> None:
	"""Verify Steps.inputs and Steps.last_used compute expected keyword usage."""
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

def test_steps_set_and_get() -> None:
	"""Verify Steps.set_steps persists data retrievable by get_steps."""
	steps = Steps()
	s = [{"input1": "A"}]
	steps.set_steps(s)
	assert steps.get_steps() == s

def test_validate_groups() -> None:
	"""Verify validate_grouping accepts complete groups and rejects incomplete ones."""
	model = MultiSpectralModel()
	# Patch metadata and validate_grouping
	class DummyMeta:
		def __init__(self, keyword: str) -> None:
			self.keyword = keyword
			self.nickname = f"file_{keyword}.tif"
	meta1 = DummyMeta("A")
	meta2 = DummyMeta("B")
	meta3 = DummyMeta("C")

	group_items = [meta1, meta2, meta3]
	keywords = {"A", "B", "C"}
	# Three items for three keywords
	assert model.validate_grouping(cast(Any, group_items), keywords) == True

	# Missing one item from keywords
	group_items = [meta1, meta2]
	keywords = {"A", "B", "D"}
	assert model.validate_grouping(cast(Any, group_items), keywords) == False

	# # Too many items for keywords
	# keywords = {"A", "B"}
	# assert model.validate_grouping(group_items, keywords) == False

def test_save_and_load_session_roundtrip(tmp_path: Path, monkeypatch: Any) -> None:
	"""Verify save_session/load_session preserves settings, steps, metadata, and view state."""
	model = MultiSpectralModel()
	monkeypatch.setattr("msagui.model.loader.load", lambda path: np.ones((2, 2)))

	model.settings.pixel_scale = 2.5
	model.histogram_settings.bins = 99
	model.steps.set_steps([
		{"keyword1": "A", "keyword2": "B", "operation": "+", "output_key": "C"}
	])

	model.add("/tmp/sample_a.csv", progress_callback=None)
	assert len(model.metadata.items) == 1
	model.metadata.items[0].keyword = "A"
	model.metadata.items[0].group = 1

	view_state = {
		"show_groups": True,
		"show_histograms": True,
		"show_inputs": True,
		"show_outputs": False,
		"view_mode": "parent",
		"sort_key": "group",
		"sort_desc": True,
	}

	session_path = tmp_path / "roundtrip_session.h5"
	model.save_session(str(session_path), view_state=view_state)

	new_model = MultiSpectralModel()
	loaded_view_state = new_model.load_session(str(session_path))

	assert new_model.settings.pixel_scale == 2.5
	assert new_model.histogram_settings.bins == 99
	assert new_model.steps.get_steps() == model.steps.get_steps()
	assert len(new_model.metadata.items) == 1
	assert new_model.metadata.items[0].nickname == "/tmp/sample_a.csv"
	assert new_model.metadata.items[0].keyword == "A"
	assert loaded_view_state == view_state

def test_delete_uses_hdf5_path(monkeypatch: Any) -> None:
	"""Verify deleting an item targets its dataset path, not only its metadata key."""
	model = MultiSpectralModel()
	called: dict[str, str] = {}

	def fake_delete(hdf5_path: str, key: str) -> None:
		called["key"] = key

	monkeypatch.setattr("msagui.model.parseH5.delete", fake_delete)
	monkeypatch.setattr("msagui.model.parseH5.add_input", lambda hdf5, key, path: None)
	monkeypatch.setattr("msagui.model.loader.load", lambda path: np.ones((2, 2)))

	model.add("/tmp/groupA_file.csv", progress_callback=None)
	model.metadata.items[0].group = 5
	model.metadata.items[0].keyword = "kw"

	model.delete(0, progress_callback=None)
	assert called["key"] == "/5/kw"

def test_clear_processed_uses_hdf5_path(monkeypatch: Any) -> None:
	"""Verify clear_processed deletes processed datasets using their full HDF5 paths."""
	model = MultiSpectralModel()
	deleted_keys: list[str] = []

	def fake_delete(hdf5_path: str, key: str) -> None:
		deleted_keys.append(key)

	monkeypatch.setattr("msagui.model.parseH5.delete", fake_delete)

	from msagui.model.metadata import ImageMeta
	model.metadata.add(ImageMeta(key="10", nickname="/tmp/out.csv", group=2, keyword="ratio", kind="processed"))

	model.clear_processed()
	assert deleted_keys == ["/2/ratio"]

def test_set_groups_uses_fullpath_signature(monkeypatch: Any) -> None:
	"""Verify grouping distinguishes files that share parent/stem but differ in full path."""
	from msagui.model.metadata import ImageMeta

	model = MultiSpectralModel()
	monkeypatch.setattr("msagui.model.parseH5.move", lambda hdf5_path, old_path, new_path: None)

	# Same immediate parent folder and same stem, but different higher-level paths.
	model.metadata.add(ImageMeta(key="1", nickname="/rootA/condition/sample_img.csv", group="default", kind="input"))
	model.metadata.add(ImageMeta(key="2", nickname="/rootB/condition/sample_img.csv", group="default", kind="input"))

	model.steps.set_steps([
		{"keyword1": "img", "operation": "*", "keyword2": "", "value": "2", "output_key": "out"}
	])

	model.set_keywords()
	model.set_groups()

	groups = [item.group for item in model.metadata.items if item.kind == "input"]
	assert groups[0] != groups[1]

def test_make_figure_helpers_for_svg_export(monkeypatch: Any) -> None:
	"""Verify figure helper methods return matplotlib figures for SVG export."""
	from msagui.model.metadata import ImageMeta

	model = MultiSpectralModel()
	model.metadata.add(ImageMeta(key="1", nickname="/tmp/in.csv", group=1, keyword="img", kind="input"))

	monkeypatch.setattr("msagui.model.parseH5.get_data", lambda hdf5, key: [np.ones((2, 2))])

	fig1 = model.make_image_figure(0)
	assert fig1 is not None
	plt.close(fig1)

	fig2 = model.make_histogram_figure(0)
	assert fig2 is not None
	plt.close(fig2)

	fig3 = model.make_group_image_figure(1)
	assert fig3 is not None
	plt.close(fig3)

	fig4 = model.make_group_histogram_figure(1)
	assert fig4 is not None
	plt.close(fig4)

def test_analyze_surfaces_step_operation_error() -> None:
	"""Verify _analyze raises contextual RuntimeError when a step operation fails."""
	class DummyMeta:
		def __init__(self) -> None:
			self.common_name = ["prefix_", "_suffix"]

	model = MultiSpectralModel()
	model.steps.set_steps([
		{"keyword1": "A", "keyword2": "B", "operation": "+", "output_key": "C", "value": ""}
	])
	model.steps.last_used = lambda: {"C": 0}
	model.metadata.by_group = lambda group_id: [DummyMeta()]  # type: ignore

	def _raise(_group: Any, _step: Any) -> Any:
		raise ValueError("operands could not be broadcast")

	model.process_step = _raise  # type: ignore

	with pytest.raises(RuntimeError, match="Failed processing step 1"):
		model._analyze({"A": "img1", "B": "img2"}, "G1", lambda: None)

def test_analyze_returns_error_for_group_shape_mismatch(monkeypatch: Any) -> None:
	"""Verify analyze reports shape mismatch details before processing steps."""
	from msagui.model.metadata import ImageMeta

	model = MultiSpectralModel()
	monkeypatch.setattr("msagui.model.loader.load", lambda path: np.ones((2, 2)))
	monkeypatch.setattr("msagui.model.parseH5.add_input", lambda hdf5, key, path: None)
	monkeypatch.setattr("msagui.model.parseH5.move", lambda hdf5, old, new: None)

	model.add([
		"/tmp/cell1_OPTIR_1655.csv",
		"/tmp/cell1_OPTIR_1703.csv",
	], progress_callback=None)
	model.metadata.items[0].common_name = ["cell1_OPTIR_", ""]
	model.metadata.items[1].common_name = ["cell1_OPTIR_", ""]

	model.steps.set_steps([
		{"keyword1": "1655", "operation": "+", "keyword2": "1703", "value": "", "output_key": "out"}
	])

	def _fake_get_images(key: Any) -> Any:
		if "1655" in str(key):
			return np.zeros((212, 221))
		return np.zeros((197, 212))

	model.get_images = _fake_get_images  # type: ignore

	error = model.analyze([0, 1], lambda: None)
	assert isinstance(error, ValueError)
	assert "Input image sizes do not match" in str(error)
	assert "1655" in str(error)
	assert "1703" in str(error)
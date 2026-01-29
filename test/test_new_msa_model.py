import numpy as np
import h5py
import pytest
from msagui.model import MultiSpectralModel, Steps

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
	monkeypatch.setattr("msagui.parseH5.add_input", lambda hdf5, key, path: None)
	monkeypatch.setattr("msagui.parseH5.delete", lambda hdf5, key: None)
	model.add("file1.tif")
	assert len(model.metadata.items) == 1
	key = model.metadata.items[0].key
	model.delete(key)
	assert len(model.metadata.items) == 0

def test_set_keywords_and_groups(monkeypatch):
	model = MultiSpectralModel()
	# Add fake metadata
	model.metadata.items = []
	model.metadata.basenames = ["imgA", "imgB"]
	model.metadata.add = lambda meta: model.metadata.items.append(meta)
	model.metadata.change_keyword = lambda key, kw: None
	model.metadata.delete = lambda key: None
	# Patch steps.inputs and match_substr
	model.steps.set_steps([{"input1": "imgA"}, {"input2": "imgB"}])
	monkeypatch.setattr("msagui.msa_utils.match_substr", lambda keywords, basenames: {"imgA": ["imgA"], "imgB": ["imgB"]})
	monkeypatch.setattr("msagui.msa_utils.remove_substr", lambda keywords, basename: basename)
	monkeypatch.setattr("msagui.msa_utils.group_strlist", lambda names: [0, 1])
	model.set_keywords()
	model.set_groups()

def test_get_images(monkeypatch, temp_hdf5):
	model = MultiSpectralModel()
	model.set_hdf5_path(temp_hdf5)
	# Patch msagui.parseH5.get_data
	monkeypatch.setattr("msagui.parseH5.get_data", lambda hdf5, keys: [np.ones((5, 5)) for _ in keys])
	arrs = model.get_images(["img1", "img2"])
	assert len(arrs) == 2
	assert np.allclose(arrs[0], np.ones((5, 5)))

def test_process_step(monkeypatch):
	model = MultiSpectralModel()
	# Patch get_images
	model.get_images = lambda keys: [np.ones((2, 2)), np.full((2, 2), 2)]
	group = {"A": "img1", "B": "img2"}
	step = {"keyword_1": "A", "keyword_2": "B", "operation": "+", "output": "C"}
	result = model.process_step(group, step)
	assert np.allclose(result, 3)
	# Test threshold
	step = {"keyword_1": "A", "keyword_2": "", "operation": "threshold", "output": "C", "value": 0.5}
	model.get_images = lambda key: np.array([[0.2, 0.6], [0.7, 0.1]])
	result = model.process_step(group, step)
	assert np.allclose(result, [[0, 0.6], [0.7, 0]])

def test_analyze_group(monkeypatch):
	model = MultiSpectralModel()
	# Patch steps
	steps = [
		{"keyword_1": "A", "keyword_2": "B", "operation": "+", "output": "C"},
		{"keyword_1": "C", "keyword_2": "", "operation": "threshold", "output": "D", "value": 1}
	]
	model.steps.set_steps(steps)
	model.steps.last_used = lambda: {"C": 0, "D": 1}
	model.get_images = lambda keys: [np.ones((2, 2)), np.ones((2, 2))]
	model.process_step = lambda group, step: np.ones((2, 2))
	group = {"A": "img1", "B": "img2", "C": "img3"}
	model.analyze_group(group)
	assert isinstance(model.group_cache, dict)

def test_steps_inputs_and_last_used():
	steps = Steps()
	steps.set_steps([
		{"input1": "A", "keyword_1": "A", "keyword_2": "B"},
		{"input2": "B", "keyword_1": "B", "keyword_2": ""}
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

# def test_set_and_get_steps():
#     model = MultiSpectralModel()
#     steps = ["normalize", "filter"]
#     model.set_steps(steps)
#     assert model.get_steps() == steps

# def test_save_and_decorate_image(tmp_path):
#     model = MultiSpectralModel()
#     image = np.random.rand(10, 10)
#     filename = tmp_path / "img.png"
#     model.save_image(str(filename), image)
#     assert os.path.exists(filename)

# def test_construct_image(monkeypatch):
#     model = MultiSpectralModel()
#     images = [np.random.rand(5, 5) for _ in range(4)]
#     # Patch plt.show to avoid displaying
#     monkeypatch.setattr("matplotlib.pyplot.show", lambda: None)
#     model.construct_image(images)

# def test_load_and_get_image(temp_hdf5):
#     model = MultiSpectralModel()
#     model.hdf5_path = temp_hdf5
#     arr = model.get_image("img1")[0]
#     assert np.allclose(arr, np.ones((5, 5)))

# def test_batch_get_image(temp_hdf5):
#     model = MultiSpectralModel()
#     model.hdf5_path = temp_hdf5
#     with h5py.File(temp_hdf5, "a") as f:
#         f.create_dataset("img2", data=np.zeros((5, 5)))
#     arrs = model.get_image(["img1", "img2"])
#     assert np.allclose(arrs[0], np.ones((5, 5)))
#     assert np.allclose(arrs[1], np.zeros((5, 5)))

# def test_set_processed_image(temp_hdf5):
#     model = MultiSpectralModel()
#     model.hdf5_path = temp_hdf5
#     arr = np.full((3, 3), 7)
#     model.set_processed_image("proc1", arr)
#     with h5py.File(temp_hdf5, "r") as f:
#         assert np.allclose(f["proc1"][:], arr)
#         assert f["proc1"].attrs["type"] == "processed"

# def test_set_input_image(temp_hdf5):
#     model = MultiSpectralModel()
#     model.hdf5_path = temp_hdf5
#     model.set_input_image("input1", "some_path.tif")
#     with h5py.File(temp_hdf5, "r") as f:
#         assert f["input1"][()] == b"some_path.tif"
#         assert f["input1"].attrs["type"] == "input"

# def test_set_hdf5_path():
#     model = MultiSpectralModel()
#     model.set_hdf5_path("abc.h5")
#     assert model.hdf5_path == "abc.h5"

# def test_add_file(tmp_path):
#     model = MultiSpectralModel()
#     model.hdf5_path = str(tmp_path / "file.h5")
#     model.add_file("img_path.tif")
#     assert model.metadata.items[0].key == "1"
#     with h5py.File(model.hdf5_path, "r") as f:
#         assert f["1"][()] == b"img_path.tif"

# def test_imaging_settings_kwargs():
#     settings = ImagingSettings(vmin=0, vmax=1)
#     imshow_kwargs = settings.imshow_kwargs()
#     assert "cmap" in imshow_kwargs
#     imsave_kwargs = settings.imsave_kwargs()
#     assert "dpi" in imsave_kwargs

# def test_metadata_store():
#     store = MetadataStore()
#     meta1 = ImageMeta(key="a", group="g1", kind="input")
#     meta2 = ImageMeta(key="b", group="g2", kind="processed")
#     store.add(meta1)
#     store.add(meta2)
#     assert store.by_group("g1") == [meta1]
#     assert set(store.keys()) == {"a", "b"}
#     assert store.new_key() == "1"  # since "a" and "b" are not "1"
#     store.add(ImageMeta(key="1", group="g3", kind="input"))
#     assert store.new_key() == "2"


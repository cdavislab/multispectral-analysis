import pytest
import numpy as np
import msagui.model.msa_utils as msa_utils

class DummySettings:
    show_colorbar = False
    cunits = ""
    font = "DejaVu Sans"
    font_size = 10
    font_weight = "normal"
    num_ticks = 0
    scale_bar_fixed_value = 0
    pixel_scale = 0
    scale_bar_units = ""
    scale_bar_location = "lower right"
    scale_bar_color = "white"

    def imsave_kwargs(self):
        return {"cmap": "gray"}
    def imshow_kwargs(self):
        return {"cmap": "gray"}

def test_shape_to_square_perfect_square():
    rows, cols, rem = msa_utils.shape_to_square(9)
    assert rows == 3
    assert cols == 3
    assert rem == 0

def test_shape_to_square_non_perfect_square():
    rows, cols, rem = msa_utils.shape_to_square(10)
    assert rows == 3
    assert cols == 4
    assert rem == 2

def test_save_image(monkeypatch):
    called = {}
    def fake_imsave(filename, image, **kwargs):
        called['filename'] = filename
        called['image'] = image
        called['kwargs'] = kwargs
    monkeypatch.setattr(msa_utils, "imsave", fake_imsave)
    arr = np.zeros((2,2))
    msa_utils.save_image("test.png", arr, DummySettings()) # type: ignore
    assert called['filename'] == "test.png"
    assert np.allclose(called['image'], arr)
    assert called['kwargs'] == {"cmap": "gray"}

def test_decorate_image(monkeypatch):
    called = {}
    class DummyAx:
        def imshow(self, image, **kwargs):
            called['image'] = image
            called['kwargs'] = kwargs
        def get_xticklabels(self):
            return []
        def get_yticklabels(self):
            return []
        def set_xticks(self, ticks):
            pass
        def set_yticks(self, ticks):
            pass
    arr = np.ones((2,2))
    msa_utils.decorate_image(arr, DummyAx(), DummySettings()) # type: ignore
    assert np.allclose(called['image'], arr)
    assert called['kwargs'] == {"cmap": "gray"}

def test_find_substring():
    l = ["apple", "banana", "grape", "pineapple"]
    idxs = msa_utils.find_substring(None, l, "apple")
    assert idxs == [0, 3]

def test_group_strlist():
    strlist = ["a", "b", "a", "c", "b"]
    result = msa_utils.group_strlist(strlist)
    # Should assign same group index to same string
    assert result[0] == result[2]
    assert result[1] == result[4]
    assert len(set(result)) == 3

def test_remove_substr_single():
    s = "hello world"
    out = msa_utils.remove_substr("world", s)
    assert out == "hello "

def test_remove_substr_list():
    s = "hello world"
    out = msa_utils.remove_substr(["hello", "world"], s)
    assert out == " "

def test_match_substr():
    substr = ["cat", "dog"]
    strings = ["cat1", "dog2", "catdog", "bird"]
    result = msa_utils.match_substr(substr, strings)
    # match_substr assigns each string to the first (longest-priority) match,
    # so "catdog" is captured by "cat" and not duplicated under "dog".
    assert "cat" in result
    assert "dog" in result
    assert set(result["cat"]) == {"cat1", "catdog"}
    assert set(result["dog"]) == {"dog2"}

def test_construct_image(monkeypatch):
    # Patch subplots and tight_layout to avoid GUI
    called = {}
    def fake_subplots(rows, cols, figsize=None):
        class DummyAx:
            def imshow(self, image, **kwargs): pass
            def axis(self, arg): called.setdefault('off', []).append(arg)
            def get_xticklabels(self): return []
            def get_yticklabels(self): return []
            def set_xticks(self, ticks): pass
            def set_yticks(self, ticks): pass
            def set_box_aspect(self, aspect): pass
        axs = np.array([[DummyAx() for _ in range(cols)] for _ in range(rows)])
        return None, axs
    monkeypatch.setattr(msa_utils, "subplots", fake_subplots)
    monkeypatch.setattr(msa_utils, "tight_layout", lambda: None)
    images = [np.zeros((2,2)) for _ in range(5)]
    msa_utils.construct_image(images, DummySettings()) # type: ignore
    # Should call axis('off') for empty slots
    assert 'off' in called
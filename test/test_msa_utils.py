import pytest
import numpy as np
from typing import Any
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

    def imsave_kwargs(self) -> dict[str, str]:
        return {"cmap": "gray"}
    def imshow_kwargs(self) -> dict[str, str]:
        return {"cmap": "gray"}

def test_shape_to_square_perfect_square() -> None:
    """Verify square input size maps to equal rows and columns with no remainder."""
    rows, cols, rem = msa_utils.shape_to_square(9)
    assert rows == 3
    assert cols == 3
    assert rem == 0

def test_shape_to_square_non_perfect_square() -> None:
    """Verify non-square input size maps to near-square layout with remainder."""
    rows, cols, rem = msa_utils.shape_to_square(10)
    assert rows == 3
    assert cols == 4
    assert rem == 2

def test_save_image(monkeypatch: Any) -> None:
    """Verify save_image forwards image and settings kwargs to imsave."""
    called = {}
    def fake_imsave(filename: str, image: Any, **kwargs: Any) -> None:
        called['filename'] = filename
        called['image'] = image
        called['kwargs'] = kwargs
    monkeypatch.setattr(msa_utils, "imsave", fake_imsave)
    arr = np.zeros((2,2))
    msa_utils.save_image("test.png", arr, DummySettings()) # type: ignore
    assert called['filename'] == "test.png"
    assert np.allclose(called['image'], arr)
    assert called['kwargs'] == {"cmap": "gray"}

def test_decorate_image(monkeypatch: Any) -> None:
    """Verify decorate_image delegates rendering with imshow kwargs."""
    called = {}
    class DummyAx:
        def imshow(self, image: Any, **kwargs: Any) -> None:
            called['image'] = image
            called['kwargs'] = kwargs
        def get_xticklabels(self) -> list[Any]:
            return []
        def get_yticklabels(self) -> list[Any]:
            return []
        def set_xticks(self, ticks: Any) -> None:
            pass
        def set_yticks(self, ticks: Any) -> None:
            pass
    arr = np.ones((2,2))
    msa_utils.decorate_image(arr, DummyAx(), DummySettings()) # type: ignore
    assert np.allclose(called['image'], arr)
    assert called['kwargs'] == {"cmap": "gray"}

def test_find_substring() -> None:
    """Verify find_substring returns all indices containing the target token."""
    l = ["apple", "banana", "grape", "pineapple"]
    idxs = msa_utils.find_substring(None, l, "apple")
    assert idxs == [0, 3]

def test_group_strlist() -> None:
    """Verify group_strlist assigns stable shared ids for identical strings."""
    strlist = ["a", "b", "a", "c", "b"]
    result = msa_utils.group_strlist(strlist)
    # Should assign same group index to same string
    assert result[0] == result[2]
    assert result[1] == result[4]
    assert len(set(result)) == 3

def test_remove_substr_single() -> None:
    """Verify remove_substr removes a single substring occurrence pattern."""
    s = "hello world"
    out = msa_utils.remove_substr("world", s)
    assert out == "hello "

def test_remove_substr_list() -> None:
    """Verify remove_substr removes all substrings in a provided list."""
    s = "hello world"
    out = msa_utils.remove_substr(["hello", "world"], s)
    assert out == " "

def test_match_substr() -> None:
    """Verify match_substr groups strings by matching keyword precedence."""
    substr = ["cat", "dog"]
    strings = ["cat1", "dog2", "catdog", "bird"]
    result = msa_utils.match_substr(substr, strings)
    # match_substr assigns each string to the first (longest-priority) match,
    # so "catdog" is captured by "cat" and not duplicated under "dog".
    assert "cat" in result
    assert "dog" in result
    assert set(result["cat"]) == {"cat1", "catdog"}
    assert set(result["dog"]) == {"dog2"}

def test_construct_image(monkeypatch: Any) -> None:
    """Verify construct_image hides unused subplot slots in non-square grids."""
    # Patch subplots and tight_layout to avoid GUI
    called = {}
    def fake_subplots(rows: int, cols: int, figsize: Any = None) -> tuple[None, np.ndarray[Any, Any]]:
        class DummyAx:
            def imshow(self, image: Any, **kwargs: Any) -> None: pass
            def axis(self, arg: Any) -> None: called.setdefault('off', []).append(arg)
            def get_xticklabels(self) -> list[Any]: return []
            def get_yticklabels(self) -> list[Any]: return []
            def set_xticks(self, ticks: Any) -> None: pass
            def set_yticks(self, ticks: Any) -> None: pass
            def set_box_aspect(self, aspect: Any) -> None: pass
        axs = np.array([[DummyAx() for _ in range(cols)] for _ in range(rows)])
        return None, axs
    monkeypatch.setattr(msa_utils, "subplots", fake_subplots)
    monkeypatch.setattr(msa_utils, "tight_layout", lambda: None)
    images = [np.zeros((2,2)) for _ in range(5)]
    msa_utils.construct_image(images, DummySettings()) # type: ignore
    # Should call axis('off') for empty slots
    assert 'off' in called
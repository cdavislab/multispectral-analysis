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

def test_decorate_image_applies_bad_color_for_nan() -> None:
    """Verify decorate_image applies configured bad color to the colormap."""
    import matplotlib.colors as mcolors

    class DummySettingsWithBad(DummySettings):
        bad = "magenta"

    called: dict[str, Any] = {}

    class DummyAx:
        def imshow(self, image: Any, **kwargs: Any) -> str:
            called["image"] = image
            called["kwargs"] = kwargs
            return "image_obj"
        def get_xticklabels(self) -> list[Any]:
            return []
        def get_yticklabels(self) -> list[Any]:
            return []
        def set_xticks(self, ticks: Any) -> None:
            pass
        def set_yticks(self, ticks: Any) -> None:
            pass
        def add_artist(self, _artist: Any) -> None:
            pass

    arr = np.array([[1.0, np.nan], [2.0, 3.0]])
    result = msa_utils.decorate_image(arr, DummyAx(), DummySettingsWithBad())  # type: ignore

    assert result == "image_obj"
    assert np.allclose(called["image"], arr, equal_nan=True)
    assert "cmap" in called["kwargs"]
    cmap = called["kwargs"]["cmap"]
    assert np.allclose(cmap.get_bad(), mcolors.to_rgba("magenta"))

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

def test_operate_threshold_with_scalar_and_image() -> None:
    """Verify threshold keeps values above scalar/array threshold and masks others with NaN."""
    image = np.array([[0.2, 0.6], [0.7, 0.1]])

    scalar_result = msa_utils.operate(image, 0.5, "threshold")
    assert np.allclose(scalar_result, [[np.nan, 0.6], [0.7, np.nan]], equal_nan=True)

    threshold_image = np.array([[0.1, 0.7], [0.6, 0.1]])
    image_result = msa_utils.operate(image, threshold_image, "threshold")
    assert np.allclose(image_result, [[0.2, np.nan], [0.7, 0.1]], equal_nan=True)

def test_operate_maxthresh_uses_proportion_of_max() -> None:
    """Verify maxthresh interprets operand as proportion of max(image) and masks others with NaN."""
    image = np.array([[0.2, 0.6], [0.7, 0.1]])
    result = msa_utils.operate(image, 0.5, "maxthresh")
    assert np.allclose(result, [[np.nan, 0.6], [0.7, np.nan]], equal_nan=True)

def test_otsu_threshold_returns_value_in_data_range() -> None:
    """Verify Otsu threshold is finite and bounded by the finite data range."""
    image = np.array(
        [[0.0, 0.1, 0.2], [0.15, 0.2, 0.1], [0.8, 0.85, 0.9], [0.95, 1.0, np.nan]]
    )
    threshold = msa_utils.otsu_threshold(image)

    finite = image[np.isfinite(image)]
    assert np.isfinite(threshold)
    assert float(np.min(finite)) <= threshold <= float(np.max(finite))

def test_operate_division_by_zero_returns_nan() -> None:
    """Verify division writes NaN when denominator is zero."""
    numerator = np.array([[2, 4], [6, 8]])
    denominator = np.array([[1, 0], [3, 0]])

    result = msa_utils.operate(numerator, denominator, "/")
    assert np.allclose(result, [[2.0, np.nan], [2.0, np.nan]], equal_nan=True)

def test_compute_statistics_ignores_nan_and_counts_valid_pixels() -> None:
    """Verify statistics use NaN-safe reducers and count only valid values."""
    image = np.array([[1.0, np.nan], [3.0, 5.0]])

    stats = msa_utils.compute_statistics(image)
    assert stats["count"] == 3
    assert stats["mean"] == pytest.approx(3.0)
    assert stats["median"] == pytest.approx(3.0)
    assert stats["max_signal"] == pytest.approx(5.0)

def test_compute_statistics_all_nan_returns_nan_fields_and_zero_count() -> None:
    """Verify fully masked arrays produce stable NaN stats and count zero."""
    image = np.array([[np.nan, np.nan], [np.nan, np.nan]])

    stats = msa_utils.compute_statistics(image)
    assert stats["count"] == 0
    assert np.isnan(stats["mean"])
    assert np.isnan(stats["median"])
    assert np.isnan(stats["max_signal"])
    assert np.isnan(stats["standard_deviation"])
    assert np.isnan(stats["standard_error"])

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

def test_construct_histogram_ignores_nan_values() -> None:
    """Verify histogram creation succeeds when image contains NaN values."""
    from msagui.model.histogram_settings import HistogramSettings

    settings = HistogramSettings()
    image = np.array([[1.0, np.nan], [2.0, 0.0]])

    fig = msa_utils.construct_histogram([image], settings)
    assert fig is not None
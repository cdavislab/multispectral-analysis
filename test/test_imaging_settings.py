import pytest
from msagui.imaging_settings import ImagingSettings

def test_default_imshow_kwargs():
    settings = ImagingSettings()
    kwargs = settings.imshow_kwargs()
    assert kwargs == {
        "cmap": "viridis",
        "interpolation": "nearest",
        "origin": "lower",
        "aspect": "auto"
    }

def test_default_imsave_kwargs():
    settings = ImagingSettings()
    kwargs = settings.imsave_kwargs()
    assert kwargs == {
        "dpi": 300,
        "cmap": "viridis",
        "vmin": None,
        "vmax": None,
        "format": None,
        "origin": "lower",
        "metadata": None
    }

def test_custom_imshow_kwargs():
    settings = ImagingSettings(cmap="gray", interpolation="bilinear", vmin=0.0, vmax=1.0, aspect="equal")
    kwargs = settings.imshow_kwargs()
    assert kwargs == {
        "cmap": "gray",
        "interpolation": "bilinear",
        "vmin": 0.0,
        "vmax": 1.0,
        "origin": "lower",
        "aspect": "equal"
    }

def test_custom_imsave_kwargs():
    settings = ImagingSettings(dpi=150, cmap="plasma", vmin=0.1, vmax=0.9, format="png", metadata={"author": "test"})
    kwargs = settings.imsave_kwargs()
    assert kwargs == {
        "dpi": 150,
        "cmap": "plasma",
        "vmin": 0.1,
        "vmax": 0.9,
        "format": "png",
        "origin": "lower",
        "metadata": {"author": "test"}
    }

def test_none_values_not_in_imshow_kwargs():
    settings = ImagingSettings(vmin=None, vmax=None)
    kwargs = settings.imshow_kwargs()
    assert "vmin" not in kwargs
    assert "vmax" not in kwargs

def test_asdict_consistency():
    settings = ImagingSettings()
    d = settings.__dict__
    asd = settings.imshow_kwargs()
    for k in asd:
        assert k in d

def test_edge_cases():
    settings = ImagingSettings(cmap=None, interpolation=None)
    kwargs = settings.imshow_kwargs()
    assert "cmap" not in kwargs
    assert "interpolation" not in kwargs
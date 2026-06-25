import pytest
from msagui.model.imaging_settings import ImagingSettings

def test_default_imshow_kwargs() -> None:
    """Verify default imaging settings produce expected imshow kwargs."""
    settings = ImagingSettings()
    kwargs = settings.imshow_kwargs()
    assert kwargs == {
        "cmap": "CMRmap",
        "interpolation": "nearest",
        "origin": "lower"
    }

def test_default_imsave_kwargs() -> None:
    """Verify default imaging settings produce expected imsave kwargs."""
    settings = ImagingSettings()
    kwargs = settings.imsave_kwargs()
    assert kwargs == {
        "transparent": False,
        "dpi": 300,
        "bbox_inches": "tight",
        "pad_inches": 0.1,
        "facecolor": 'auto',
        "edgecolor": 'auto',
    }


def test_custom_imshow_kwargs() -> None:
    """Verify custom color and range values are propagated to imshow kwargs."""
    settings = ImagingSettings(cmap="gray", interpolation="bilinear", vmin=0.0, vmax=1.0)
    kwargs = settings.imshow_kwargs()
    assert kwargs == {
        "cmap": "gray",
        "interpolation": "bilinear",
        "vmin": 0.0,
        "vmax": 1.0,
        "origin": "lower"
    }

def test_custom_imsave_kwargs() -> None:
    """Verify custom export settings are propagated to imsave kwargs."""
    settings = ImagingSettings(dpi=150, cmap="plasma", vmin=0.1, vmax=0.9, metadata={"author": "test"})
    kwargs = settings.imsave_kwargs()
    assert kwargs == {
        "transparent": False,
        "dpi": 150,
        'metadata': {"author": "test"},
        "bbox_inches": "tight",
        "pad_inches": 0.1,
        "facecolor": 'auto',
        "edgecolor": 'auto',
    }

def test_none_values_not_in_imshow_kwargs() -> None:
    """Verify None-valued range settings are omitted from imshow kwargs."""
    settings = ImagingSettings(vmin=None, vmax=None)
    kwargs = settings.imshow_kwargs()
    assert "vmin" not in kwargs
    assert "vmax" not in kwargs

def test_asdict_consistency() -> None:
    """Verify keys emitted by imshow kwargs exist in the dataclass fields."""
    settings = ImagingSettings()
    d = settings.__dict__
    asd = settings.imshow_kwargs()
    for k in asd:
        assert k in d

def test_edge_cases() -> None:
    """Verify optional string fields are excluded when explicitly set to None."""
    settings = ImagingSettings(cmap=None, interpolation=None)
    kwargs = settings.imshow_kwargs()
    assert "cmap" not in kwargs
    assert "interpolation" not in kwargs

def test_bad_color_setting_stored_but_not_direct_imshow_kwarg() -> None:
    """Verify bad color preference is stored on settings and applied downstream by renderer."""
    settings = ImagingSettings(cmap="gray", bad="#000000")
    kwargs = settings.imshow_kwargs()
    assert settings.bad == "#000000"
    assert kwargs["cmap"] == "gray"
    assert "bad" not in kwargs
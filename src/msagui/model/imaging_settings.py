
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class ImagingSettings:
    dpi: int = 300
    cmap: str | None = "CMRmap"
    interpolation: str | None= "nearest"
    vmin: Optional[float] = None
    vmax: Optional[float] = None
    origin: str = "lower"
    aspect: str = "auto"
    bbox_inches: str = "tight"
    transparent: bool = False
    pad_inches: float = 0.1
    format: Optional[str] = None
    metadata: Optional[dict] = None
    facecolor: Optional[str] = 'auto'
    edgecolor: Optional[str] = 'auto'
    backend: Optional[str] = None
    export_directory: Optional[str] = 'folder'
    export_format: str = "png"

    cunits: str = "Intensity"
    font: str = "DejaVu Sans"
    font_size: float = 12.0
    font_weight: str = "normal"
    pixel_scale: float = 1.0
    scale_bar_units: str = "μm"
    scale_bar_location: str = "lower right"
    scale_bar_fixed_value: Optional[float] = 0
    num_ticks: int = 0
    show_colorbar: bool = False

    def update_from_dict(self, settings_dict: dict):
        for key, value in settings_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def to_dict(self) -> dict:
        return asdict(self)

    def imshow_kwargs(self) -> dict:
        return {
            k: v for k, v in asdict(self).items()
            if k in {"cmap", "interpolation", "vmin", "vmax", "origin", "aspect"}
            and v is not None
        }

    def imsave_kwargs(self) -> dict:
        kwargs = {
            k: v for k, v in asdict(self).items()
            if k in {"transparent", "dpi", "format", "metadata", "bbox_inches", "pad_inches", "facecolor", "edgecolor", "backend"}
            and v is not None
        }
        # matplotlib expects format without a leading dot (e.g. "png", not ".png")
        if "format" in kwargs and kwargs["format"].startswith("."):
            kwargs["format"] = kwargs["format"].lstrip(".")
        return kwargs
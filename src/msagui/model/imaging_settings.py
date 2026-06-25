
from dataclasses import dataclass, asdict
from typing import Any

@dataclass
class ImagingSettings:
    dpi: int = 300
    cmap: str | None = "CMRmap"
    bad: str | None = None
    interpolation: str | None= "nearest"
    vmin: float | None = None
    vmax: float | None = None
    origin: str = "lower"
    transparent: bool = False
    pad_inches: float = 0.1
    metadata: dict[str, Any] | None = None
    facecolor: str | None = 'auto'
    edgecolor: str | None = 'auto'

    export_format: str = "png"

    cunits: str = "Intensity"
    font: str = "DejaVu Sans"
    font_size: float = 12.0
    font_weight: str = "normal"
    pixel_scale: float = 1.0
    scale_bar_units: str = "μm"
    scale_bar_color: str = "white"
    scale_bar_location: str = "lower right"
    scale_bar_fixed_value: float | None = 0
    num_ticks: int = 0
    show_colorbar: bool = False

    def update_from_dict(self, settings_dict: dict[str, Any]) -> None:
        for key, value in settings_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def to_dict(self) -> dict:
        return asdict(self)

    def imshow_kwargs(self) -> dict:
        return {
            k: v for k, v in asdict(self).items()
            if k in {"cmap", "interpolation", "vmin", "vmax", "origin"}
            and v is not None
        }

    def imsave_kwargs(self) -> dict:
        kwargs = {
            k: v for k, v in asdict(self).items()
            if k in {"transparent", "dpi", "metadata", "pad_inches", "facecolor", "edgecolor"}
            and v is not None
        }
        kwargs["bbox_inches"] = "tight"
        return kwargs

from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class ImagingSettings:
    dpi: int = 300
    cmap: str | None = "viridis"
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
    export_directory: Optional[str] = 'msa_analysis'

    def imshow_kwargs(self) -> dict:
        return {
            k: v for k, v in asdict(self).items()
            if k in {"cmap", "interpolation", "vmin", "vmax", "origin", "aspect"}
            and v is not None
        }

    def imsave_kwargs(self) -> dict:
        return {
            k: v for k, v in asdict(self).items()
            if k in {"transparent", "dpi", "format", "metadata", "bbox_inches", "pad_inches", "facecolor", "edgecolor", "backend"}
            and v is not None
        }
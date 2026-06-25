from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class HistogramSettings:
    """Settings controlling how per-image histograms are drawn."""

    # --- Data ---
    bins: int = 50
    exclude_zeros: bool = True

    # --- Appearance ---
    color: str = "steelblue"
    kde: bool = True
    kde_color: str = "navy"
    log_scale: bool = False
    grid: bool = True

    # --- Axis ---
    xlabel: str = ""
    ylabel: str = "Count"
    vmin: Optional[float] = None
    vmax: Optional[float] = None

    # --- Figure size ---
    figsize_w: float = 4.0
    figsize_h: float = 3.0

    # --- Font ---
    font: str = "DejaVu Sans"
    font_size: float = 11.0
    font_weight: str = "normal"

    # ------------------------------------------------------------------ #
    def update_from_dict(self, d: dict) -> None:
        for key, value in d.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def to_dict(self) -> dict:
        return asdict(self)

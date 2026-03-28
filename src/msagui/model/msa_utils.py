import io
import logging
from math import ceil, sqrt
from PIL import Image
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from msagui.model.imaging_settings import ImagingSettings
from msagui.model.histogram_settings import HistogramSettings
from typing import Any
import numpy.typing as npt
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.pyplot import imsave, subplots, tight_layout
from matplotlib.ticker import MaxNLocator
from matplotlib.font_manager import FontProperties
from scipy.stats import gaussian_kde
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar
from mpl_toolkits.axes_grid1 import make_axes_locatable

logger = logging.getLogger(__name__)

def shape_to_square(size: int) -> tuple[int, int, int]:
    """
    Outputs the number of rows, columns, and remainder
    needed to shape a given number into a nearly square format.
    """
    rows = int(sqrt(size))
    cols = int(ceil(size / rows))
    remainder = rows * cols - size
    return rows, cols, remainder

def save_image(filename: str, image: npt.NDArray[Any], settings: ImagingSettings) -> None:
    """
    Save image with optional imshow kwargs.
    """
    imsave(filename, image, **settings.imsave_kwargs())

def _apply_font_and_ticks(ax: Axes, settings: ImagingSettings) -> dict[str, str | int]:
    """Apply font and tick settings from ImagingSettings to an axis."""
    font_props = {"fontfamily": settings.font,
                  "fontsize":   settings.font_size,
                  "fontweight": settings.font_weight}
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontfamily(settings.font)
        label.set_fontsize(settings.font_size)
        label.set_fontweight(settings.font_weight)
    if settings.num_ticks == 0:
        ax.set_xticks([])
        ax.set_yticks([])
    else:
        ax.xaxis.set_major_locator(MaxNLocator(settings.num_ticks))
        ax.yaxis.set_major_locator(MaxNLocator(settings.num_ticks))
    return font_props


def _add_scale_bar(image: npt.NDArray[Any], ax: Axes, settings: ImagingSettings) -> None:
    """Overlay a scale bar on *ax* using pixel_scale / scale_bar_* settings.

    The scale bar is suppressed when ``scale_bar_fixed_value == 0`` or
    ``pixel_scale == 0``.
    """
    if settings.scale_bar_fixed_value == 0 or settings.pixel_scale == 0:
        return
    if settings.scale_bar_fixed_value is not None:
        bar_pixels = settings.scale_bar_fixed_value / settings.pixel_scale
        label = f"{settings.scale_bar_fixed_value} {settings.scale_bar_units}"
    else:
        # Auto: ~20 % of image width, rounded to a sensible value
        bar_pixels = image.shape[1] * 0.2
        bar_value = round(bar_pixels * settings.pixel_scale, 2)
        label = f"{bar_value} {settings.scale_bar_units}"
        bar_pixels = bar_value / settings.pixel_scale

    fp = FontProperties(family=settings.font, size=settings.font_size,
                        weight=settings.font_weight)
    scalebar = AnchoredSizeBar(
        ax.transData,
        bar_pixels,
        label,
        settings.scale_bar_location,
        pad=0.5,
        color=settings.scale_bar_color or "white",
        frameon=False,
        size_vertical=max(1, image.shape[0] // 40),
        fontproperties=fp,
    )
    ax.add_artist(scalebar)


def decorate_image(image: npt.NDArray[Any], ax: Axes, settings: ImagingSettings) -> Any:
    """
    Add an image to the provided axis and apply all ImagingSettings display
    options: colormap/scale, font, tick count, and scale bar.

    Returns the AxesImage so the caller can attach a colorbar.
    """
    imshow_options = settings.imshow_kwargs()
    bad_color = getattr(settings, "bad", None)
    if bad_color:
        cmap_option = imshow_options.get("cmap", plt.get_cmap())
        cmap = plt.get_cmap(cmap_option).copy() if isinstance(cmap_option, str) else cmap_option.copy()
        cmap.set_bad(color=bad_color)
        imshow_options["cmap"] = cmap

    im = ax.imshow(image, **imshow_options)
    _apply_font_and_ticks(ax, settings)
    _add_scale_bar(image, ax, settings)
    return im


def construct_image(images: list[npt.NDArray[Any]], settings: ImagingSettings) -> tuple[Figure, Any]:
    """
    Constructs a grid of images with optional colorbars labelled by ``cunits``.

    Colorbars are attached via ``make_axes_locatable`` so the image axes keep
    their natural aspect ratio regardless of colorbar presence.
    """
    rows, cols, _ = shape_to_square(len(images))
    fig, axs = subplots(rows, cols, figsize=(cols * 3, rows * 3))
    axs_flat = np.atleast_1d(axs).flatten()  # type: ignore
    for i, image in enumerate(images):
        im = decorate_image(image, axs_flat[i], settings)
        # Lock the axis box to the image's native row/column ratio so
        # the displayed image is not distorted
        if image.ndim >= 2 and image.shape[1] != 0:
            axs_flat[i].set_box_aspect(image.shape[0] / image.shape[1])
        if settings.show_colorbar:
            fp = FontProperties(family=settings.font, size=settings.font_size,
                                weight=settings.font_weight)
            divider = make_axes_locatable(axs_flat[i])
            cax = divider.append_axes("right", size="5%", pad=0.05)
            cbar = fig.colorbar(im, cax=cax)
            if settings.cunits:
                cbar.set_label(settings.cunits, fontproperties=fp)
            for tick_label in cbar.ax.get_yticklabels():
                tick_label.set_fontfamily(settings.font)
                tick_label.set_fontsize(settings.font_size)
    for j in range(i + 1, len(axs_flat)):
        axs_flat[j].axis('off')
    tight_layout()
    return fig, axs

def construct_histogram(images: list[npt.NDArray[Any]], settings: HistogramSettings) -> Figure:
    """Build a matplotlib Figure containing one histogram per image in *images*.

    Parameters
    ----------
    images:
        List of 2-D (or N-D) numpy arrays.  All non-zero pixels are used when
        ``settings.exclude_zeros`` is True.
    settings:
        A :class:`HistogramSettings` instance controlling appearance.

    Returns
    -------
    matplotlib.figure.Figure
    """
    n = len(images)
    rows, cols, _ = shape_to_square(n)
    fig, axs = plt.subplots(
        rows, cols,
        figsize=(settings.figsize_w * cols, settings.figsize_h * rows),
    )
    axs_flat = np.atleast_1d(axs).flatten()  # type: ignore

    font_kw = {
        "fontfamily": settings.font,
        "fontsize":   settings.font_size,
        "fontweight": settings.font_weight,
    }

    for i, image in enumerate(images):
        ax = axs_flat[i]
        flat = image.flatten().astype(float)
        flat = flat[np.isfinite(flat)]
        if settings.exclude_zeros:
            flat = flat[flat != 0]

        if flat.size == 0:
            ax.text(0.5, 0.5, "No data", ha="center", va="center",
                    transform=ax.transAxes)
            continue

        ax.hist(
            flat,
            bins=settings.bins,
            color=settings.color,
            alpha=0.75,
            range=(
                settings.vmin if settings.vmin is not None else float(flat.min()),
                settings.vmax if settings.vmax is not None else float(flat.max()),
            ),
        )

        if settings.kde and flat.size > 1:
            try:
                kde_fn = gaussian_kde(flat)
                x_range = np.linspace(
                    settings.vmin if settings.vmin is not None else flat.min(),
                    settings.vmax if settings.vmax is not None else flat.max(),
                    300,
                )
                kde_vals = kde_fn(x_range)
                # Scale KDE to match histogram counts
                bin_width = (x_range[-1] - x_range[0]) / settings.bins
                kde_scaled = kde_vals * flat.size * bin_width
                ax.plot(x_range, kde_scaled,
                        color=settings.kde_color, linewidth=1.5)
            except Exception:
                logger.debug("Skipping KDE due to failure", exc_info=True)

        if settings.log_scale:
            ax.set_yscale("log")
        if settings.grid:
            ax.grid(True, alpha=0.3)
        if settings.xlabel:
            ax.set_xlabel(settings.xlabel, **font_kw)
        if settings.ylabel:
            ax.set_ylabel(settings.ylabel, **font_kw)
        if settings.vmin is not None or settings.vmax is not None:
            ax.set_xlim(
                left  = settings.vmin if settings.vmin is not None else None,
                right = settings.vmax if settings.vmax is not None else None,
            )

        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontfamily(settings.font)
            label.set_fontsize(settings.font_size)
            label.set_fontweight(settings.font_weight)

    # Hide any unused axes
    for j in range(i + 1, len(axs_flat)):
        axs_flat[j].set_visible(False)

    tight_layout()
    return fig


def find_substring(self: Any, l: list[str], substr: str) -> list[int]:
    """
    Returns a list of idx from `l` that contain `substr`.
    """
    return [i for i, s in enumerate(l) if substr in s]

def replace_item(arr: npt.NDArray[Any], old_value: Any, new_value: Any) -> npt.NDArray[Any]:
    """
    Replaces all occurrences of old_value with new_value in arr.
    Adds a temporary marker to avoid conflict when new value already in old value
    """
    arr = np.where(arr == new_value, -1, arr)
    arr = np.where(arr == old_value, new_value, arr)
    arr = np.where(arr == -1, old_value, arr)
    return arr

def find_unique(arr: npt.NDArray[Any]) -> npt.NDArray[Any]:
    """
    Returns values that appear only once
    """
    values, counts = np.unique(arr, return_counts=True)
    return values[np.where(counts == 1)]

def _construct_group_dict(strlist: list[str], pregroup: list[int | str]) -> dict[str, int]:
    group_dict = dict()
    for s, group in zip(strlist, pregroup):
        if group == -1:
            continue
        group_dict[s] = group
    return group_dict

def group_strlist(strlist: list[str], pregroup: list[int | str] | None = None) -> npt.NDArray[np.integer[Any]]:
    """
    Groups strings in list by matching strings.
    Returns a list of group indices for each string in strlist.
    """
    if pregroup:
        groups = _construct_group_dict(strlist, pregroup)
    else:
        groups = dict()

    groups_idx = []
    count = 1
    for s in strlist:
        # Find a group index for s that is not already assigned to another string.
        while count in groups.values():
            count += 1
        if s not in groups.keys():
            groups[s] = count
        groups_idx.append(groups[s])
    return np.array(groups_idx)

def split_substr(substrings: list[str] | str, string: str) -> list[str]:
    """Split *string* on the first matching substring.

    Substrings are tried longest-first so that '1655_corr' takes priority over
    the shorter prefix '1655'.
    """
    if isinstance(substrings, str):
        substrings = [substrings]
    for substring in sorted(substrings, key=len, reverse=True):
        if substring in string:
            return string.split(substring)
    return [string]

def remove_substr(substrings: list[str] | str, string: str) -> str:
    """Remove occurrences of each substring from string.

    Substrings are sorted longest-first so that more specific strings (e.g.
    '1655_corr') are removed before shorter prefixes ('1655'), preventing
    partial matches from corrupting the remainder.
    """
    if isinstance(substrings, str):
        substrings = [substrings]
    for substring in sorted(substrings, key=len, reverse=True):
        string = string.replace(substring, "")
    return string

def match_substr(substr: list[str], strings: list[str]) -> dict[str, list[str]]:
    """
    Sort strings into dictionary by matching keywords found as substring.

    Each string is matched to the *longest* keyword that it contains, so that
    '1655_corr' takes priority over the shorter prefix '1655'.

    :param substr:   List of substrings (keywords) to match against strings
    :param strings:  List of strings to be matched
    """
    # Longest-first so more specific keywords win over shorter prefix keywords.
    ordered_substr = sorted(substr, key=len, reverse=True)
    substr_match: dict[str, list[str]] = {}
    for string in strings:
        for keyword in ordered_substr:
            if keyword in string:
                substr_match.setdefault(keyword, []).append(string)
                break  # stop at first (longest) match
    return substr_match

def otsu_threshold(image: npt.NDArray[Any], bins: int = 256) -> float:
    """Compute Otsu threshold from finite image values."""
    values = np.asarray(image, dtype=float)
    values = values[np.isfinite(values)]

    if values.size == 0:
        raise ValueError("Cannot compute auto threshold from empty/non-finite image.")

    data_min = float(np.min(values))
    data_max = float(np.max(values))
    if data_min == data_max:
        return data_min

    hist, edges = np.histogram(values, bins=bins, range=(data_min, data_max))
    centers = (edges[:-1] + edges[1:]) / 2.0
    hist = hist.astype(float)

    weight1 = np.cumsum(hist)
    weight2 = np.cumsum(hist[::-1])[::-1]
    mean1 = np.cumsum(hist * centers) / np.maximum(weight1, 1e-12)
    mean2 = (
        np.cumsum((hist * centers)[::-1]) / np.maximum(weight2[::-1], 1e-12)
    )[::-1]

    between = weight1[:-1] * weight2[1:] * (mean1[:-1] - mean2[1:]) ** 2
    best_idx = int(np.argmax(between))
    return float(centers[best_idx])

def operate(a: npt.NDArray[Any], b: npt.NDArray[Any] | float, operation: str) -> npt.NDArray[Any]:
    """Apply an element-wise operation between arrays or array and scalar.

    Args:
        a: Left-hand array operand.
        b: Right-hand operand (array or scalar for unary-threshold mode).
        operation: One of ``+``, ``-``, ``*``, ``/``, ``threshold``, or ``maxthresh``.

    Returns:
        Result array for the requested operation.

    Raises:
        ValueError: If ``operation`` is unsupported.
    """
    if operation == '+':
        return a + b
    elif operation == '-':
        return a - b
    elif operation == '*':
        return a * b
    elif operation == '/':
        a_float = np.asarray(a, dtype=float)
        b_arr = np.asarray(b)
        result = np.full(a_float.shape, np.nan, dtype=float)
        np.divide(a_float, b_arr, out=result, where=b_arr != 0)
        return result
    elif operation == 'threshold':
        a_float = np.asarray(a, dtype=float)
        return np.where(a_float >= b, a_float, np.nan)
    elif operation == 'maxthresh':
        a_float = np.asarray(a, dtype=float)
        return np.where(a_float >= b * np.max(a_float), a_float, np.nan)
    else:
        raise ValueError(f"Unsupported operation: {operation}")

def is_number(s: Any) -> bool:
    """Return True when input can be parsed as a float."""
    try:
        float(s)
        return True
    except ValueError:
        return False
    
def compute_statistics(image: npt.NDArray[Any]) -> dict[str, float | int]:
    """
    Computes basic statistics for a given image array.
    """
    valid_pixels = np.asarray(image, dtype=float)
    valid_pixels = valid_pixels[~np.isnan(valid_pixels)]
    count = int(valid_pixels.size)

    if count == 0:
        return {
            'mean': float(np.nan),
            'median': float(np.nan),
            'max_signal': float(np.nan),
            'standard_deviation': float(np.nan),
            'standard_error': float(np.nan),
            'count': 0
        }

    std_deviation = np.nanstd(valid_pixels)
    stats = {
        'mean': float(np.nanmean(valid_pixels)),
        'median': float(np.nanmedian(valid_pixels)),
        'max_signal': float(np.nanmax(valid_pixels)),
        'standard_deviation': float(std_deviation),
        'standard_error': float(std_deviation / np.sqrt(count)),
        'count': count
    }
    return stats

def fig_to_img(fig: Figure, **kwargs: Any) -> Image.Image:
    """Convert a Matplotlib figure to a PIL Image."""
    buf = io.BytesIO()
    fig.savefig(buf, **kwargs)  # Save the figure in the buffer
    buf.seek(0)
    img = Image.open(buf)
    return img
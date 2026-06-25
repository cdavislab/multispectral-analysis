"""Core multispectral analysis helpers."""

import numpy as np
import numpy.typing as npt
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib_scalebar.scalebar import ScaleBar
from typing import Any

def bin_image(image_data: npt.NDArray[Any], image_name: str = "") -> tuple[npt.NDArray[np.float64], str]:
    """Bin an image into 2×2 blocks using mean intensity.

    Args:
        image_data: Input 2-D image array.
        image_name: Name prefix used to generate output image name.

    Returns:
        Tuple of binned image array and generated binned image name.
    """
    height, width = image_data.shape
    binned_height = height // 2
    binned_width = width // 2

    binned_image = np.zeros((binned_height, binned_width), dtype=np.float64)

    for i in range(0, height - 1, 2):
        for j in range(0, width - 1, 2):
            block = image_data[i:i+2, j:j+2]
            binned_image[i//2, j//2] = np.mean(block)

    binned_image_name = f"{image_name}_binned"

    return binned_image, binned_image_name 

def correct_spectra(
    data: npt.NDArray[Any],
    reference: npt.NDArray[Any],
    correction_factor: float,
) -> npt.NDArray[Any]:
    """Subtract scaled reference spectra and clip negative values to zero.

    Args:
        data: Input data spectrum or image array.
        reference: Reference array to be scaled and subtracted.
        correction_factor: Multiplicative factor applied to the reference.

    Returns:
        Corrected array with non-negative values.
    """
    corrected = data - correction_factor * reference
    corrected[corrected < 0] = 0
    return corrected

def threshold(data: npt.NDArray[Any], threshpercent: float = 0.05) -> tuple[npt.NDArray[Any], np.generic]:
    """Zero values below a percentage of the maximum signal.

    Args:
        data: Input array to threshold. This array is modified in place.
        threshpercent: Fraction of maximum intensity used as threshold.

    Returns:
        Tuple of thresholded array and original maximum signal.
    """
    maxsignal = np.max(data)
    threshval = maxsignal * threshpercent
    data[data<threshval] = 0
    return data, maxsignal
    
def compute_ratio(top: npt.NDArray[Any], bottom: npt.NDArray[Any]) -> npt.NDArray[Any]:
    """Compute element-wise ratio between two arrays with zero-division protection.

    Args:
        top: Numerator array.
        bottom: Denominator array.

    Returns:
        Ratio array with zeros where denominator is zero.
    """
    return np.divide(top, bottom, out = np.zeros_like(top), where = bottom != 0)

def summarize(data: npt.NDArray[Any], header_name: str = "") -> npt.NDArray[Any]:
    """Summarize non-zero pixels with basic descriptive statistics.

    Args:
        data: Input data array.
        header_name: Reserved parameter for compatibility.

    Returns:
        Two-row array containing statistics and header labels.
    """
    _ = header_name
    data_foravg = data[data != 0]
    mean_value = np.mean(data_foravg)
    median_value = np.median(data_foravg)
    max_signal = np.max(data_foravg)
    std_deviation = np.std(data_foravg)
    standard_error = std_deviation / np.sqrt(np.size(data_foravg))
    size = np.size(data_foravg)
    
    return np.array([[mean_value, median_value, max_signal, std_deviation, standard_error, size],\
        ['Average','Median','Max', 'Std','Se','n']])

def histogram(
    data: npt.NDArray[Any],
    fname: str | None = None,
    ax: Axes | None = None,
    lower_bound: float | None = None,
    upper_bound: float | None = None,
) -> tuple[npt.NDArray[Any], Figure]:
    """Create a histogram plot from non-zero values.

    Args:
        data: Input data array.
        fname: Reserved parameter for compatibility.
        ax: Optional axis to render into.
        lower_bound: Optional lower x-axis limit.
        upper_bound: Optional upper x-axis limit.

    Returns:
        Flattened non-zero values and the generated figure.
    """
    _ = fname
    data = data[data != 0]
    flat = data.flatten()
    sns.set_style('darkgrid')
    if ax == None:
        fig, ax = plt.subplots()
    g = sns.histplot(data = flat, ax=ax)
    if lower_bound != None or upper_bound != None:
        ax.set_xlim([lower_bound,upper_bound])
    fig = g.get_figure()
    return flat, fig

def ratio_image(
    data: npt.NDArray[Any],
    lower_bound: float | None = None,
    upper_bound: float | None = None,
    scalebar_size: float = 0,
    ax: Axes | None = None,
) -> Axes:
    """Render a ratio image with optional limits and scale bar.

    Args:
        data: Input ratio image array.
        lower_bound: Optional lower color limit.
        upper_bound: Optional upper color limit.
        scalebar_size: Pixel size in microns for scale bar rendering.
        ax: Optional axis to render into.

    Returns:
        Axis containing the rendered image.
    """
    ax = ax or plt.gca()
    if lower_bound != None or upper_bound != None:
        im_obj = plt.imshow(data, cmap='CMRmap', vmin=lower_bound, vmax=upper_bound)
        plt.clim([lower_bound, upper_bound],ax=ax)
    else:
        im_obj = plt.imshow(data, cmap='CMRmap')
    plt.colorbar(im_obj, cmap='CMRmap',ax=ax)
    ax.axis('off')
    if scalebar_size > 0:
        scalebar = ScaleBar(scalebar_size, "um", label="10 μm", width_fraction=0.015, location=3, frameon=None, color="white", fixed_value=10, box_alpha=0, scale_loc="none")
        ax.add_artist(scalebar)
    return ax
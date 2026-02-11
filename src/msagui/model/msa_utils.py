import io
from math import ceil, sqrt
from PIL import Image
from msagui.model.imaging_settings import ImagingSettings
from typing import Any
import numpy.typing as npt
import numpy as np
from matplotlib.pyplot import imsave, subplots, tight_layout

def shape_to_square(size) -> tuple:
    """
    Outputs the number of rows, columns, and remainder
    needed to shape a given number into a nearly square format.
    """
    rows = int(sqrt(size))
    cols = int(ceil(size / rows))
    remainder = rows * cols - size
    return rows, cols, remainder

def save_image(filename: str, image: npt.NDArray, settings: ImagingSettings):
    """
    Save image with optional imshow kwargs.
    """
    imsave(filename, image, **settings.imsave_kwargs())

def decorate_image(image: npt.NDArray, ax, settings: ImagingSettings):
    """
    Add an image to the provided axis with optional imshow kwargs.
    """
    ax.imshow(image, **settings.imshow_kwargs())
    
def construct_image(images: list, settings: ImagingSettings):
    """
    Constructs a grid of images
    """
    rows, cols, _ = shape_to_square(len(images))
    fig, axs = subplots(rows, cols, figsize=(cols * 3, rows * 3))
    axs_flat = np.atleast_1d(axs).flatten() # type: ignore
    for i, image in enumerate(images):
        decorate_image(image, axs_flat[i], settings)
    for j in range(i + 1, len(axs_flat)):
        axs_flat[j].axis('off')
    tight_layout()
    return fig, axs


def find_substring(self, l: list, substr: str) -> list:
    """
    Returns a list of idx from `l` that contain `substr`.
    """
    return [i for i, s in enumerate(l) if substr in s]

def group_strlist(strlist: list[str]) -> npt.NDArray[np.integer[Any]]:
    """
    Groups strings in strlist by common substrings
    Returns a list of group indices for each string in strlist.
    """
    groups = dict()
    groups_idx = []
    count = 0
    for s in strlist:
        if s not in groups.keys():
            count += 1
            groups[s] = count
        groups_idx.append(groups[s])
    return np.array(groups_idx)

def remove_substr(substr: list[str] | str, string: str) -> str:
    if isinstance(substr, str):
        substr = [substr]
    for substring in substr:
        string = string.replace(substring, "")
    return string

def match_substr(substr: list[str], strings: list[str]) -> dict[str, list[str]]:
    """
    Sort strings into dictionary by matching keywords found as substring.
    
    :param self: Class instance
    :param substr: List of substrings to match against strings
    :param strings: List of strings to be matched against substrings
    """
    substr_match = dict()
    for string in strings:
        for keyword in substr:
            if keyword in string:
                if keyword not in substr_match:
                    substr_match[keyword] = []
                substr_match[keyword].append(string)
    return substr_match

def operate(a, b, operation: str) -> npt.NDArray:
    if operation == '+':
        return a + b
    elif operation == '-':
        return a - b
    elif operation == '*':
        return a * b
    elif operation == '/':
        return np.divide(a, b, out=np.zeros(a.shape), where=b!=0)
    elif operation == 'threshold':
        return np.where(a >= b, a, 0)
    else:
        raise ValueError(f"Unsupported operation: {operation}")

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
    
def compute_statistics(image: npt.NDArray) -> dict:
    """
    Computes basic statistics for a given image array.
    """
    stats = {
        'mean': float(np.mean(image)),
        'median': float(np.median(image)),
        'max_signal': float(np.max(image)),
        'standard_deviation': float(np.std(image)),
        'standard_error': float(np.std(image) / np.sqrt(image.size)),
        'count': int(image.size)
    }
    return stats

def fig_to_img(fig, **kwargs):
    """Convert a Matplotlib figure to a PIL Image."""
    buf = io.BytesIO()
    fig.savefig(buf, **kwargs)  # Save the figure in the buffer
    buf.seek(0)
    img = Image.open(buf)
    return img
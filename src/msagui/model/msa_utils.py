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

def replace_item(arr: npt.NDArray, old_value, new_value) -> npt.NDArray:
    """
    Replaces all occurrences of old_value with new_value in arr.
    Adds a temporary marker to avoid conflict when new value already in old value
    """
    arr = np.where(arr == new_value, -1, arr)
    arr = np.where(arr == old_value, new_value, arr)
    arr = np.where(arr == -1, old_value, arr)
    return arr

def find_unique(arr: npt.NDArray) -> npt.NDArray:
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
    if isinstance(substrings, str):
        substrings = [substrings]

    for substring in substrings:
        if substring in string:
            return string.split(substring)
        
    return [string]

def remove_substr(substrings: list[str] | str, string: str) -> str:
    """ Removes occurrences of substr from string. substr can be a single string or a list of strings."""
    if isinstance(substrings, str):
        substrings = [substrings]
    for substring in substrings:
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
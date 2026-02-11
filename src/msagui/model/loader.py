from PIL import Image
import numpy as np
import numpy.typing as npt

def load_tiff(path: str) -> npt.NDArray:
    """
    Loads a TIFF image using PIL and returns it as a numpy array.
    """

    img = Image.open(path, formats=["TIFF"])
    return np.array(img)

def load(path: str) -> npt.NDArray:
    """
    Loads from csv, tsv, tiff, or other common formats using numpy.
    """
    loader = {'csv': lambda p: np.loadtxt(p, delimiter=','),
            'tsv': lambda p: np.loadtxt(p, delimiter='\t'),
                'tiff': load_tiff,
                'tif': load_tiff
            }

    ext = path.split('.')[-1].lower()
    if ext in loader:
        data = loader[ext](path)
    else:
        raise ValueError(f"Unsupported file extension: {ext}")
    return data
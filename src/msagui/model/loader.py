from PIL import Image
import logging
import numpy as np
import numpy.typing as npt

logger = logging.getLogger(__name__)

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
        try:
            data = loader[ext](path)
            logger.debug("Loaded %s file: %s", ext, path)
        except Exception:
            logger.exception("Failed to load %s file: %s", ext, path)
            raise
    else:
        logger.error("Unsupported file extension '%s' for path: %s", ext, path)
        raise ValueError(f"Unsupported file extension: {ext}")
    return data
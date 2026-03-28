from PIL import Image
import logging
import numpy as np
import numpy.typing as npt

logger = logging.getLogger(__name__)


def _validate_numeric_array(data: npt.NDArray, path: str) -> npt.NDArray:
    """Validate loaded input data is a non-empty numeric numpy array."""
    if not isinstance(data, np.ndarray):
        raise ValueError(f"Could not read '{path}': file did not produce array data.")
    if data.size == 0:
        raise ValueError(f"Could not read '{path}': file contains no data.")
    if not np.issubdtype(data.dtype, np.number):
        raise ValueError(f"Could not read '{path}': file contains non-numeric values.")
    return data

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
    if ext not in loader:
        logger.error("Unsupported file extension '%s' for path: %s", ext, path)
        raise ValueError(
            f"Could not read '{path}': unsupported file type '.{ext}'. "
            "Please use CSV, TSV, TIFF, or TIF files."
        )

    try:
        data = loader[ext](path)
        data = _validate_numeric_array(data, path)
        logger.debug("Loaded %s file: %s", ext, path)
        return data
    except ValueError as exc:
        logger.exception("Failed to load %s file: %s", ext, path)
        msg = str(exc)
        if ext in {"csv", "tsv"} and ("could not convert string" in msg.lower() or "invalid" in msg.lower()):
            raise ValueError(
                f"Could not read '{path}': file contains non-numeric text. "
                "Please remove text values and keep numeric data only."
            ) from exc
        if msg.startswith("Could not read"):
            raise
        raise ValueError(f"Could not read '{path}': {msg}") from exc
    except Exception as exc:
        logger.exception("Failed to load %s file: %s", ext, path)
        if ext in {"tif", "tiff"}:
            raise ValueError(
                f"Could not read '{path}': image file is unreadable or corrupted."
            ) from exc
        raise ValueError(f"Could not read '{path}': file could not be parsed.") from exc
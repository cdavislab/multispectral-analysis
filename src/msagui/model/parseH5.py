
from functools import lru_cache
import logging
import h5py
import numpy.typing as npt
import msagui.model.loader as loader

logger = logging.getLogger(__name__)

def _decode_dataset(data_obj) -> npt.NDArray:
    assert isinstance(data_obj, h5py.Dataset), f"Expected h5py.Dataset, got {type(data_obj)}"
    data = data_obj[()]
    if data_obj.attrs.get('type') == 'str':
        # Byte string directly stored in the HDF5 file, decode it directly
        fpath = data_obj[()].decode()
        logger.debug("Decoding string dataset %s from path %s", data_obj.name, fpath)
        return loader.load(fpath)
    elif data_obj.attrs.get('type') == 'array':
        # Already a numpy array stored in the HDF5 file
        return data_obj[()]
    else:
        raise ValueError(f"Unknown dataset type {data_obj.attrs.get('type')} "
                         f"for key: {data_obj.name}")

@lru_cache(maxsize=8)
def _load(hdf5_path: str, key: str, f: h5py.File | None = None) -> npt.NDArray:
    """
    Loads a dataset from an HDF5 file. Optimized with LRU caching.
    """
    try:
        if f is not None:
            data_obj = f[key]
            return _decode_dataset(data_obj)
        else:
            with h5py.File(hdf5_path, "r") as f:
                data_obj = f[key]
                return _decode_dataset(data_obj)
    except Exception:
        logger.exception("Failed loading dataset '%s' from HDF5 file %s", key, hdf5_path)
        raise

def get_data(hdf5_path: str, keys: str | list[str]) -> list[npt.NDArray]:
    """
    keys: str or iterable[str]
    """
    if isinstance(keys, str):
        logger.debug("Loading single dataset '%s' from %s", keys, hdf5_path)
        return [_load(hdf5_path, keys, f=None)]

    # batch load
    with h5py.File(hdf5_path, "r") as f:
        data = []
        for key in keys:
            data.append(_load(hdf5_path, key, f=f))  # preload into cache
        return data

def move(hdf5_path: str, old_path: str, new_path: str):
    """
    Moves a dataset to a new group in the HDF5 file.
    """
    try:
        with h5py.File(hdf5_path, "a") as f:
            assert old_path in f, f"Old path {old_path} not found in HDF5 file"
            if new_path in f:
                del f[new_path]
            f.move(old_path, new_path)
        logger.debug("Moved dataset in %s: %s -> %s", hdf5_path, old_path, new_path)
    except Exception:
        logger.exception("Failed moving dataset in %s: %s -> %s", hdf5_path, old_path, new_path)
        raise
        

def add_processed(hdf5_path: str, key: str, image: npt.NDArray):
    """
    Sets a processed image in the HDF5 file.
    """
    try:
        with h5py.File(hdf5_path, "a") as f:
            if key in f:
                del f[key]
            dset = f.create_dataset(key, data=image)
            dset.attrs['type'] = 'array'
        logger.debug("Added processed dataset '%s' to %s", key, hdf5_path)
    except Exception:
        logger.exception("Failed adding processed dataset '%s' to %s", key, hdf5_path)
        raise

def add_input(hdf5_path: str, key: str, file_path: str):    
    """
    Sets an input image in the HDF5 file.
    """
    try:
        with h5py.File(hdf5_path, "a") as f:
            if key in f:
                del f[key]
            dset = f.create_dataset(key, data=file_path)
            dset.attrs['type'] = 'str'
        logger.debug("Added input dataset '%s' to %s", key, hdf5_path)
    except Exception:
        logger.exception("Failed adding input dataset '%s' to %s", key, hdf5_path)
        raise

def delete(hdf5_path: str, key: str):
    """
    Deletes a dataset from the HDF5 file.
    """
    try:
        with h5py.File(hdf5_path, "a") as f:
            if key in f:
                del f[key]
        logger.debug("Deleted dataset '%s' from %s", key, hdf5_path)
    except Exception:
        logger.exception("Failed deleting dataset '%s' from %s", key, hdf5_path)
        raise
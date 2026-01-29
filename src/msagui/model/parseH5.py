
from functools import lru_cache
import h5py
import numpy.typing as npt
import numpy as np
@lru_cache(maxsize=8)
def _load(hdf5_path: str, key: str, f: h5py.File | None = None) -> npt.NDArray:
    """
    Loads a dataset from an HDF5 file. Optimized with LRU caching.
    """

    if f is not None:
        data_obj = f[key]
    
    with h5py.File(hdf5_path, "r") as f:
        data_obj = f[key]
    # if data_obj.dtype == 'O':
        # stored as object, likely a file path
        data = np.loadtxt(data_obj[()].decode(), delimiter=',')
    # else:
    #     data = data_obj[()]
    return data

def get_data(hdf5_path: str, keys: str | list[str]) -> list[npt.NDArray]:
    """
    keys: str or iterable[str]
    """
    if isinstance(keys, str):
        return [_load(hdf5_path, keys, f=None)]

    # batch load
    with h5py.File(hdf5_path, "r") as f:
        data = []
        for key in keys:
            data.append(_load(hdf5_path, key, f=f))  # preload into cache
        return data
    
def add_processed(hdf5_path: str, key: str, image: npt.NDArray):
    """
    Sets a processed image in the HDF5 file.
    """
    with h5py.File(hdf5_path, "a") as f:
        if key in f:
            del f[key]
        dset = f.create_dataset(key, data=image)
        dset.attrs['type'] = 'processed'

def add_input(hdf5_path: str, key: str, file_path: str):    
    """
    Sets an input image in the HDF5 file.
    """
    with h5py.File(hdf5_path, "a") as f:
        if key in f:
            del f[key]
        dset = f.create_dataset(key, data=file_path)
        dset.attrs['type'] = 'input'

def delete(hdf5_path: str, key: str):
    """
    Deletes a dataset from the HDF5 file.
    """
    with h5py.File(hdf5_path, "a") as f:
        if key in f:
            del f[key]
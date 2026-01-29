from tkinter import Image
import matplotlib.pyplot as plt
import numpy as np
from dataclasses import dataclass, asdict
from typing import Callable, Optional
import numpy.typing as npt
import matplotlib.typing as mpt
import h5py
from pyparsing import Dict, lru_cache
import os
from msagui.model import msa_utils
from msagui.model.msa_utils import *
import msagui.model.parseH5 as parseH5
from msagui.model.metadata import ImageMeta, MetadataStore
from msagui.model.imaging_settings import ImagingSettings
import io
from PIL import Image
from matplotlib.figure import Figure
class MultiSpectralModel:
    def __init__(self):
        self.metadata = MetadataStore()
        self.settings = ImagingSettings()
        self.steps = Steps()
        self.hdf5_path: str = "hdf5_data.h5"
        self.group_cache = dict()

    def process(self, items: str | list[str], func: Callable[[str], None], progress_callback: Callable) -> dict[str, Exception]:
        if isinstance(items, str):
            items = [items]

        failed = {}
        for item in items:
            if progress_callback:
                progress_callback()
            try:
                func(item)
            except Exception as e:
                failed[item] = e

        return failed

    def add(self, file_path: str | list[str], progress_callback: Callable) -> dict[str, Exception]:
        def add_single(fpath: str):
            new_key = self.metadata.new_key()
            self.metadata.add(ImageMeta(key=new_key, nickname=fpath, group="default", kind="input"))
            parseH5.add_input(self.hdf5_path, new_key, fpath)
        
        return self.process(file_path, func=add_single, progress_callback=progress_callback)

    def delete(self, key: str | list[str], progress_callback: Callable) -> dict[str, Exception]:
        def delete_single(key: str):
            parseH5.delete(self.hdf5_path, key)
            self.metadata.delete(key)
        
        return self.process(key, func=delete_single, progress_callback=progress_callback)

    def set_keywords(self):
        """
        Sets keywords for images based on filename matching.
        """
        keywords = self.steps.inputs()
        keyword_matches = match_substr(keywords, self.metadata.basenames)
        for keyword, keys in keyword_matches.items():
            for key in keys:
                self.metadata.change_keyword(key, keyword)

    def set_groups(self):
        """
        Updates image groups based on name matching after removing keywords.
        """
        keywords = self.steps.inputs()
        basenames_trimmed = [remove_substr(keywords, basename) for basename in self.metadata.basenames]
        groups_idx = group_strlist(basenames_trimmed)

        for meta, group_idx in zip(self.metadata.items, groups_idx):
            meta.group = group_idx

    def set_hdf5_path(self, hdf5_path: str):
        """
        Sets the HDF5 file path for loading images.
        """
        self.hdf5_path = hdf5_path

    def get_images(self, keys: str | list[str]) -> npt.NDArray | list[npt.NDArray]:
        """
        Retrieves image data from HDF5 file for given keys.
        """
        if isinstance(keys, str):
            keys = [keys]

        keys_to_fetch = [key for key in keys if key not in self.group_cache]
        data = parseH5.get_data(self.hdf5_path, keys_to_fetch)

        images = []
        for key in keys:
            if key in self.group_cache:
                images.append(self.group_cache[key])
            else:
                images.append(data.pop(0))

        return images if len(images) > 1 else images[0]

    def process_step(self, group: dict, step: dict) -> npt.NDArray:
        """
        Processes a single step for a given group of images. Decides operation based on step dictionary.
        Determines whether to use one or two input images based on presence of value or keyword_2.
        """
        path_1 = group[step['keyword_1']]
        path_2 = group.get(step['keyword_2'])
        value = step.get('value')

        if path_2 is None:
            data1 = self.get_images(path_1)
            return operate(data1, value, step['operation'])
        
        data1, data2 = self.get_images([path_1, path_2])
        return operate(data1, data2, step['operation'])
        
    def analyze(self, group: dict):
        self.group_cache.clear()
        last_used = self.steps.last_used()

        for i, step in enumerate(self.steps.get_steps()):
            output_keyword = step['output']
            result = self.process_step(group, step)
            if i < last_used[output_keyword]:
                self.group_cache[output_keyword] = result


    def get_groups_from_idx(self, idx: int | list[int]) -> set[int]:
        if isinstance(idx, int):
            idx = [idx]

        groups = set()
        for i in idx:
            groups.add(self.metadata.items[i].group)

        return groups
    
    def analyze_groups(self, idx: int | list[int]):
        groups = self.get_groups_from_idx(idx)
        for group in groups:
            items = self.metadata.by_group(group)
            group_dict = {item.keyword: item.key for item in items}
            self.analyze(group_dict)

    def fig_to_img(self, fig):
        """Convert a Matplotlib figure to a PIL Image."""
        buf = io.BytesIO()
        fig.savefig(buf, format='png')  # Save the figure in the buffer
        buf.seek(0)
        img = Image.open(buf)
        return img
    
    @staticmethod
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

    def make_image(self, idx: int) -> npt.NDArray:
        """
        Makes processed image for given dataframe index.
        """
        print(type(idx))
        print(type)
        item = self.metadata.items[idx]
        key = item.key
        data = parseH5.get_data(self.hdf5_path, key)  # Ensure image is loaded
        fig, axs = construct_image(data, self.settings)
        if item.statistics is None:
            stats = self.compute_statistics(data[0]) #HACK
            item.statistics = stats
        return self.fig_to_img(fig), item.statistics

@dataclass
class Steps:
    def __init__(self):
        self.steps = []
    
    def inputs(self):
        """
        Returns input keywords used in the processing steps.
        """
        return list({step[key] for step in self.steps for key in step if 'input' in key})
    
    def last_used(self):
        """
        Determine idx of step when input keyword is last used and put it in dictionary
        """
        input_keywords = self.inputs()
        input_order = dict()
        for keyword in input_keywords:
            for idx, step in enumerate(self.steps):
                if step.get('keyword_1') == keyword or step.get('keyword_2') == keyword:
                    input_order[keyword] = idx
        return input_order
    
    def set_steps(self, steps):
        """
        Sets cleaned processing steps.
        """
        self.steps = steps

    def get_steps(self):
        """
        Returns:
        List of processing steps.
        """
        return self.steps
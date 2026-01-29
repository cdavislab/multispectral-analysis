import matplotlib.pyplot as plt
import numpy as np
from dataclasses import dataclass, asdict
from typing import Optional
import numpy.typing as npt
import matplotlib.typing as mpt
import h5py
from pyparsing import lru_cache
import os
from msagui.model.msa_utils import *
import msagui.model.parseH5 as parseH5
from msagui.model.metadata import ImageMeta, MetadataStore
from msagui.model.imaging_settings import ImagingSettings

class MultiSpectralModel:
    def __init__(self):
        self.metadata = MetadataStore()
        self.settings = ImagingSettings()
        self.steps = Steps()
        self.hdf5_path: str = "hdf5_data.h5"
        self.group_cache = dict()

    def add(self, file_path: str):
        """
        Adds a file to the model's dataset. Loads file path into HDF5 and populates dataframe
        """
        new_key = self.metadata.new_key()
        self.metadata.add(ImageMeta(key=new_key, group="default", kind="input"))
        parseH5.add_input(self.hdf5_path, new_key, file_path)

    def delete(self, key: str):
        """
        Deletes a file from the model's dataset.
        """
        parseH5.delete(self.hdf5_path, key)
        self.metadata.delete(key)

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
        

    def analyze_group(self, group: dict):
        self.group_cache.clear()
        last_used = self.steps.last_used()

        for i, step in enumerate(self.steps.get_steps()):
            output_keyword = step['output']
            result = self.process_step(group, step)
            if i < last_used[output_keyword]:
                self.group_cache[output_keyword] = result

    
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
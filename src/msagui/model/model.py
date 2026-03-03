import os
from typing import Callable
import numpy.typing as npt
import numpy as np
import msagui.model.msa_utils as utils
import msagui.model.parseH5 as parseH5
from msagui.model.metadata import ImageMeta, MetadataStore
from msagui.model.imaging_settings import ImagingSettings
from msagui.model.histogram_settings import HistogramSettings
from msagui.model.steps import Steps
import matplotlib.pyplot as plt
from PIL.Image import Image

import logging
logger = logging.getLogger(__name__)

class MultiSpectralModel:
    def __init__(self):
        self.metadata = MetadataStore()
        self.settings = ImagingSettings()
        self.histogram_settings = HistogramSettings()
        self.steps = Steps()
        self.hdf5_path: str = "hdf5_data.h5"
        self.group_cache = dict()
        # if hdf5_path exists, delete
        if os.path.exists(self.hdf5_path):
            os.remove(self.hdf5_path)
    def process(self, items, func: Callable, progress_callback: Callable | None) -> dict[str, Exception]:
        if not isinstance(items, list | tuple):
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

    ### Adding Files, Deleting Files, Setting Metadata ###

    def add(self, file_path: str | list[str], progress_callback: Callable | None = None) -> dict[str, Exception]:
        def add_single(fpath: str):
            new_key = self.metadata.new_key()
            meta = ImageMeta(key=new_key, nickname=fpath, group="default", kind="input")  # pyright: ignore[reportArgumentType]
            self.metadata.add(meta)
            logger.info(f"Added metadata for file: {fpath} with key: {new_key}")
            parseH5.add_input(self.hdf5_path, meta.hdf5_path, fpath)
        
        return self.process(file_path, func=add_single, progress_callback=progress_callback)

    def delete(self, idx: int | list[int], progress_callback: Callable | None = None) -> dict[str, Exception]:
        def delete_single(idx: int):
            item = self.metadata.items[idx]
            key = item.key
            logger.info(f"Deleting file with key: {key}")
            parseH5.delete(self.hdf5_path, key)
            self.metadata.delete(key)
        
        if isinstance(idx, list):
            idx = sorted(idx, reverse=True)
        return self.process(idx, func=delete_single, progress_callback=progress_callback)
    
    def set_keywords(self):
        """
        Sets keywords for images based on filename matching.
        """
        keywords = self.steps.inputs()
        basenames = self.metadata.basenames
        keyword_matches = utils.match_substr(keywords, basenames)
        for keyword, names in keyword_matches.items():
            for name in names:
                key = self.metadata.by_basename(name)[0].key
                self.metadata.change_keyword(key, keyword)

    def validate_grouping(self, metas: list[ImageMeta], keywords: set) -> bool:
        """ Validates that a group of images contains all keywords once. Returns True if valid, False otherwise."""
        for meta in metas:
            if meta.keyword in keywords:
                keywords.discard(meta.keyword)
            else:
                logger.warning(f"Keyword '{meta.keyword}' from image '{meta.nickname}' is not in the required keywords set or is duplicated in the group.")
        if len(keywords) > 0:
            return False
        return True

    def set_groups(self):
        """
        Updates image groups based on name matching after removing keywords.
        Uses pre-existing groups as a starting point to maintain consistency.
        Moves datasets in HDF5 file to new group paths accordingly.
        """
        all_input_keywords = self.steps.inputs(include_computed=True)
        basenames_trimmed = [utils.remove_substr(all_input_keywords, basename) for basename in self.metadata.basenames]
        existing_groups = self.metadata.groups()
        existing_groups = existing_groups = [group if group != "default" else -1 for group in existing_groups]
        groups_idx = utils.group_strlist(basenames_trimmed, pregroup=existing_groups)

        # Mark any groups that do not have all keywords represented as ungrouped
        user_input_keywords = self.steps.inputs(include_computed=False)
        for group_idx in set(groups_idx):
            group_items_idx = np.where(groups_idx == group_idx)[0]
            group_items = [self.metadata.items[idx] for idx in group_items_idx]
            if not self.validate_grouping(group_items, set(user_input_keywords)):
                logger.warning(f"Ungrouping items with indices {group_items_idx} due to incomplete keyword representation in group.")
                logger.warning(f"Group items: {[item.nickname for item in group_items]}, Keywords needed: {set(user_input_keywords)}")
                groups_idx[group_items_idx] = -1  # -1 indicates ungrouped

        # Change group details in metadata and move datasets in HDF5 file accordingly
        for meta, group_idx in zip(self.metadata.items, groups_idx):
            if meta.kind == 'processed':
                continue  # Skip processed items, only group input items
            if group_idx == meta.group or (group_idx == -1 and meta.group == "default"):
                continue  # No change in group, skip

            old_path = meta.hdf5_path
            meta.group = group_idx
            parseH5.move(self.hdf5_path, old_path, meta.hdf5_path)  # move dataset to new group path
            meta.common_name = utils.split_substr(all_input_keywords, meta.nickname)
            logger.info(f"Common name for {meta.nickname}: {meta.common_name}")
            assert len(meta.common_name) == 2, f"Expected common_name to have 2 parts, got {len(meta.common_name)} for file {meta.nickname}"

    def set_hdf5_path(self, hdf5_path: str):
        """
        Sets the HDF5 file path for loading images.
        """
        self.hdf5_path = hdf5_path

    def get_steps(self):
        """
        Retrieves current processing steps from the model.
        """
        return self.steps.get_steps()

    ### Image Visualization and Analysis ###

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
    
    def make_image(self, idx: int) -> tuple[Image, dict]:
        """
        Makes processed image for given dataframe index.
        """
        item = self.metadata.items[idx]
        data = parseH5.get_data(self.hdf5_path, item.hdf5_path)  # Ensure image is loaded
        fig, axs = utils.construct_image(data, self.settings)
        if item.statistics is None:
            stats = utils.compute_statistics(data[0]) #HACK
            item.statistics = stats
        stream = utils.fig_to_img(fig, **self.settings.imsave_kwargs())
        plt.close() #fig.close()
        return stream, item.statistics

    def make_histogram(self, idx: int) -> tuple[Image, dict]:
        """
        Makes a histogram image for the item at the given metadata index.
        """
        item = self.metadata.items[idx]
        data = parseH5.get_data(self.hdf5_path, item.hdf5_path)
        fig = utils.construct_histogram(data, self.histogram_settings)
        if item.statistics is None:
            stats = utils.compute_statistics(data[0])  # HACK: use first channel
            item.statistics = stats
        stream = utils.fig_to_img(fig, **self.settings.imsave_kwargs())
        plt.close()
        return stream, item.statistics

    def process_step(self, group: dict, step: dict) -> npt.NDArray:
        """
        Processes a single step for a given group of images. Decides operation based on step dictionary.
        Determines whether to use one or two input images based on presence of value or keyword_2.
        """
        assert type(group) == dict, f"Expected group to be a dict, got {type(group)}"
        logger.info(f"Group: {group}")
        item_1 = group[step['keyword1']]
        item_2 = group.get(step['keyword2'])
        value = step.get('value')

        if item_2 is None:
            data1 = self.get_images(item_1)
            return utils.operate(data1, float(value), step['operation'])
        
        data1, data2 = self.get_images([item_1, item_2])
        return utils.operate(data1, data2, step['operation'])
        
    def add_processed(self, fpath: str, group: str, keyword: str):
        new_key = self.metadata.new_key()
        self.metadata.add(ImageMeta(key=new_key, nickname=fpath, group=group,
                                    keyword=keyword, kind="processed"))
        parseH5.add_input(self.hdf5_path, new_key, fpath)

    def clear_processed(self):
        processed_items = [item for item in self.metadata.items if item.kind == "processed"]
        for item in processed_items:
            parseH5.delete(self.hdf5_path, item.key)
            self.metadata.delete(item.key)

    def _analyze(self, group: dict, group_id: str, progress_callback: Callable):
        self.group_cache.clear()

        # Pull the last used index for each output keyword across all steps to optimize caching strategy
        last_used = self.steps.last_used()

        # Get the common name for the group to construct output nicknames.
        common_name = self.metadata.by_group(group_id)[0].common_name
        assert common_name is not None, f"Expected common_name to be set for group {group_id}"

        for i, step in enumerate(self.steps.get_steps()):
            # Perform single operation
            output_keyword = step['output_key']
            result = self.process_step(group, step)

            # Save result before continuing
            output_nickname = common_name[0] + output_keyword + common_name[1]
            meta = ImageMeta(
                key=self.metadata.new_key(),
                nickname=output_nickname,
                common_name=common_name,
                group=group_id,
                keyword=output_keyword,
                kind="processed"
            )
            self.metadata.add(meta)
            parseH5.add_processed(self.hdf5_path, meta.hdf5_path, result)
            
            # Cache the result if this step's output is used in a future step
            if i < last_used[output_keyword]:
                self.group_cache[output_keyword] = result
                group[meta.keyword] = meta.hdf5_path  

    def analyze(self, idx: int | list[int], progress_callback: Callable):
        if self.steps.get_steps() == []:
            return ValueError("No processing steps defined. Please set steps before analyzing.")
        
        self.set_keywords()
        self.set_groups()
        # groups = set(self.metadata.get_group(idx))
        self.clear_processed()
        groups = set(self.metadata.groups(visible_only=True))
        if "default" in groups:
            groups.discard("default")
            
        for group in groups:
            logging.info(f"Processing group: {group}")
            items = self.metadata.by_group(group)
            group_dict = {item.keyword: item.hdf5_path for item in items}
            logging.info(f"Group dict for group {group}: {group_dict}")
            self._analyze(group_dict, group, progress_callback)
    

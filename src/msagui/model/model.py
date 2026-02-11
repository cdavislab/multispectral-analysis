from typing import Callable
import numpy.typing as npt
import msagui.model.msa_utils as utils
import msagui.model.parseH5 as parseH5
from msagui.model.metadata import ImageMeta, MetadataStore
from msagui.model.imaging_settings import ImagingSettings
from msagui.model.steps import Steps
import matplotlib.pyplot as plt

class MultiSpectralModel:
    def __init__(self):
        self.metadata = MetadataStore()
        self.settings = ImagingSettings()
        self.steps = Steps()
        self.hdf5_path: str = "hdf5_data.h5"
        self.group_cache = dict()

    def process(self, items, func: Callable, progress_callback: Callable | None) -> dict[str, Exception]:
        if not isinstance(items, list):
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
            parseH5.add_input(self.hdf5_path, meta.hdf5_path, fpath)
        
        return self.process(file_path, func=add_single, progress_callback=progress_callback)

    def delete(self, idx: int | list[int], progress_callback: Callable | None = None) -> dict[str, Exception]:
        def delete_single(idx: int):
            item = self.metadata.items[idx]
            key = item.key
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

    def set_groups(self):
        """
        Updates image groups based on name matching after removing keywords.
        """
        keywords = self.steps.inputs()
        basenames_trimmed = [utils.remove_substr(keywords, basename) for basename in self.metadata.basenames]
        groups_idx = utils.group_strlist(basenames_trimmed)

        for meta, group_idx in zip(self.metadata.items, groups_idx):
            old_path = meta.hdf5_path
            meta.group = group_idx
            parseH5.move(self.hdf5_path, old_path, meta.hdf5_path)  # move dataset to new group path
            
        

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
    
    def make_image(self, idx: int) -> npt.NDArray:
        """
        Makes processed image for given dataframe index.
        """
        item = self.metadata.items[idx]
        key = item.key
        data = parseH5.get_data(self.hdf5_path, key)  # Ensure image is loaded
        fig, axs = utils.construct_image(data, self.settings)
        if item.statistics is None:
            stats = utils.compute_statistics(data[0]) #HACK
            item.statistics = stats
        stream = utils.fig_to_img(fig, **self.settings.imsave_kwargs())
        plt.close() #fig.close()
        return stream, item.statistics # pyright: ignore[reportReturnType]

    def process_step(self, group: dict, step: dict) -> npt.NDArray:
        """
        Processes a single step for a given group of images. Decides operation based on step dictionary.
        Determines whether to use one or two input images based on presence of value or keyword_2.
        """
        assert type(group) == dict, f"Expected group to be a dict, got {type(group)}"
        item_1 = group[step['keyword1']]
        item_2 = group.get(step['keyword2'])
        value = step.get('value')

        if item_2 is None:
            data1 = self.get_images(item_1)
            return utils.operate(data1, value, step['operation'])
        
        data1, data2 = self.get_images([item_1, item_2])
        return utils.operate(data1, data2, step['operation'])
        

    def add_processed(self, fpath: str, group: str, keyword: str):
        new_key = self.metadata.new_key()
        self.metadata.add(ImageMeta(key=new_key, nickname=fpath, group=group,
                                    keyword=keyword, kind="processed"))  # pyright: ignore[reportArgumentType]
        parseH5.add_input(self.hdf5_path, new_key, fpath)

    def _analyze(self, group: dict, group_id: str, progress_callback: Callable):
        self.group_cache.clear()
        last_used = self.steps.last_used()

        for i, step in enumerate(self.steps.get_steps()):
            output_keyword = step['output_key']
            result = self.process_step(group, step)
            meta = ImageMeta(
                key=self.metadata.new_key(),
                nickname=f"processed_{output_keyword}",
                group=group_id,
                keyword=output_keyword,
                kind="processed"
            )
            self.metadata.add(meta)
            parseH5.add_processed(self.hdf5_path, meta.hdf5_path, result)
            if i < last_used[output_keyword]:
                self.group_cache[output_keyword] = result
            

    def analyze(self, idx: int | list[int], progress_callback: Callable):
        groups = self.metadata.get_group(idx)
        for group in groups:
            print("[analyze] Processing group:", group)
            items = self.metadata.by_group(group)
            group_dict = {item.keyword: item.hdf5_path for item in items}
            print("[analyze] Processing group_dict:", group_dict)
            self._analyze(group_dict, group, progress_callback)
    

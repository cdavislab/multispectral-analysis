import atexit
import json
import os
import shutil
import csv
import tempfile
from dataclasses import asdict
from typing import Any, Callable
import numpy.typing as npt
import numpy as np
import h5py
import msagui.model.msa_utils as utils
import msagui.model.parseH5 as parseH5
import msagui.model.loader as loader
from msagui.model.metadata import ImageMeta, MetadataStore
from msagui.model.imaging_settings import ImagingSettings
from msagui.model.histogram_settings import HistogramSettings
from msagui.model.steps import Steps
import matplotlib.pyplot as plt
from PIL.Image import Image

import logging
logger = logging.getLogger(__name__)

class MultiSpectralModel:
    def __init__(self) -> None:
        self.metadata = MetadataStore()
        self.settings = ImagingSettings()
        self.histogram_settings = HistogramSettings()
        self.steps = Steps()
        self._temp_hdf5_path: str = self._new_temp_hdf5_path()
        self.hdf5_path: str = self._temp_hdf5_path
        self.group_cache = dict()
        logger.info(f"Using HDF5 workspace file: {self.hdf5_path}")
        atexit.register(self._cleanup_temp_hdf5)

    def _new_temp_hdf5_path(self) -> str:
        fd, path = tempfile.mkstemp(prefix="msaGUI_", suffix=".h5")
        os.close(fd)
        return path

    def _cleanup_temp_hdf5(self) -> None:
        if self.hdf5_path != self._temp_hdf5_path:
            return
        if not os.path.exists(self._temp_hdf5_path):
            return
        try:
            os.remove(self._temp_hdf5_path)
            logger.debug("Removed temporary HDF5 workspace file: %s", self._temp_hdf5_path)
        except OSError as e:
            logger.warning("Could not remove temporary HDF5 file %s: %s", self._temp_hdf5_path, e)

    def _json_default(self, value: Any) -> Any:
        if isinstance(value, np.integer | np.floating | np.bool_):
            return value.item()
        if isinstance(value, np.ndarray):
            return value.tolist()
        raise TypeError(f"Object of type {type(value)} is not JSON serializable")

    def _write_session_metadata(self, view_state: dict[str, Any] | None = None) -> None:
        session_payload: dict[str, Any] = {
            "imaging": self.settings.to_dict(),
            "histogram": self.histogram_settings.to_dict(),
            "steps": self.steps.get_steps(),
            "metadata": [asdict(item) for item in self.metadata.items],
        }
        if view_state is not None:
            session_payload["view"] = view_state

        with h5py.File(self.hdf5_path, "a") as f:
            settings_group = f.require_group("settings")
            for key, value in session_payload.items():
                json_text = json.dumps(value, default=self._json_default)
                if key in settings_group:
                    del settings_group[key]
                dset = settings_group.create_dataset(key, data=json_text)
                dset.attrs["type"] = "json"

    def _read_session_metadata(self, file_path: str) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        with h5py.File(file_path, "r") as f:
            if "settings" not in f:
                return payload
            settings_group = f["settings"]
            if not isinstance(settings_group, h5py.Group):
                return payload
            for key in settings_group.keys():
                raw_value = settings_group[key][()]
                if isinstance(raw_value, bytes):
                    json_text = raw_value.decode("utf-8")
                else:
                    json_text = str(raw_value)
                payload[key] = json.loads(json_text)
        return payload

    def save_session(self, target_path: str, view_state: dict[str, Any] | None = None) -> str:
        self._write_session_metadata(view_state=view_state)
        shutil.copy(self.hdf5_path, target_path)
        logger.info("Session exported to %s", target_path)
        return target_path

    def load_session(self, source_path: str) -> dict[str, Any]:
        session_payload = self._read_session_metadata(source_path)

        temp_path = self._new_temp_hdf5_path()
        shutil.copy(source_path, temp_path)

        if self.hdf5_path == self._temp_hdf5_path and os.path.exists(self._temp_hdf5_path):
            try:
                os.remove(self._temp_hdf5_path)
            except OSError as e:
                logger.warning("Could not remove temporary HDF5 file %s: %s", self._temp_hdf5_path, e)

        self._temp_hdf5_path = temp_path
        self.hdf5_path = temp_path
        self.group_cache = {}

        if "imaging" in session_payload:
            self.settings.update_from_dict(session_payload["imaging"])
        if "histogram" in session_payload:
            self.histogram_settings.update_from_dict(session_payload["histogram"])
        if "steps" in session_payload:
            self.steps.set_steps(session_payload["steps"])

        metadata_items = session_payload.get("metadata", [])
        restored_metadata = MetadataStore()
        for item in metadata_items:
            restored_metadata.add(ImageMeta(**item))
        self.metadata = restored_metadata

        logger.info("Session loaded from %s", source_path)
        return session_payload.get("view", {})

    def process(
        self,
        items: Any,
        func: Callable[[Any], None],
        progress_callback: Callable[[], None] | None,
    ) -> dict[Any, Exception]:
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
        def add_single(fpath: str) -> None:
            loader.load(fpath)
            new_key = self.metadata.new_key()
            meta = ImageMeta(key=new_key, nickname=fpath, group="default", kind="input")  # pyright: ignore[reportArgumentType]
            self.metadata.add(meta)
            logger.debug("Added metadata for file: %s with key: %s", fpath, new_key)
            parseH5.add_input(self.hdf5_path, meta.hdf5_path, fpath)
        
        return self.process(file_path, func=add_single, progress_callback=progress_callback)

    def delete(self, idx: int | list[int], progress_callback: Callable | None = None) -> dict[str, Exception]:
        def delete_single(idx: int) -> None:
            item = self.metadata.items[idx]
            key = item.key
            logger.debug("Deleting file with key: %s", key)
            parseH5.delete(self.hdf5_path, item.hdf5_path)
            self.group_cache.clear()
            self.metadata.delete(key)
        
        if isinstance(idx, list):
            idx = sorted(idx, reverse=True)
        return self.process(idx, func=delete_single, progress_callback=progress_callback)
    
    def set_keywords(self) -> None:
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

    def validate_grouping(self, metas: list[ImageMeta], keywords: set[str]) -> bool:
        """ Validates that a group of images contains all keywords once. Returns True if valid, False otherwise."""
        for meta in metas:
            if meta.keyword in keywords:
                keywords.discard(meta.keyword)
            else:
                logger.warning(f"Keyword '{meta.keyword}' from image '{meta.nickname}' is not in the required keywords set or is duplicated in the group.")
        if len(keywords) > 0:
            return False
        return True

    def set_groups(self) -> None:
        """
        Updates image groups based on name matching after removing keywords.
        Uses pre-existing groups as a starting point to maintain consistency.
        Moves datasets in HDF5 file to new group paths accordingly.
        """
        all_input_keywords = self.steps.inputs(include_computed=True)
        fullpaths_trimmed = [
            utils.remove_substr(all_input_keywords, nickname)
            for nickname in self.metadata.nicknames()
        ]
        existing_groups = [meta.group if meta.group != "default" else -1 for meta in self.metadata.items]
        groups_idx = utils.group_strlist(fullpaths_trimmed, pregroup=existing_groups)

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
            logger.debug("Common name for %s: %s", meta.nickname, meta.common_name)
            assert len(meta.common_name) == 2, f"Expected common_name to have 2 parts, got {len(meta.common_name)} for file {meta.nickname}"

    def export_stats(self, file_path: str | None = None, directory: str | None = None) -> str:
        """Write per-image statistics to a CSV file.

        Only items whose ``statistics`` dict has been populated (i.e. images
        that have been displayed or analysed) are included.

        Parameters
        ----------
        file_path:
            Full destination path for the CSV.  Takes priority over *directory*.
        directory:
            Folder to write ``statistics.csv`` into.  Falls back to the
            current working directory when neither this nor *file_path* is given.

        Returns
        -------
        str
            The path of the written file.
        """
        items_with_stats = [
            item for item in self.metadata.items
            if item.statistics is not None
        ]

        if not items_with_stats:
            logger.warning("export_stats: no statistics available yet.")
            return ""

        if file_path is None:
            export_dir = directory or os.getcwd()
            os.makedirs(export_dir, exist_ok=True)
            file_path = os.path.join(export_dir, "statistics.csv")

        # Build column names from the first item's stats dict.
        stat_keys = list(items_with_stats[0].statistics.keys())
        fieldnames = ["nickname", "group", "keyword", "kind"] + stat_keys

        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for item in items_with_stats:
                row = {
                    "nickname": item.nickname,
                    "group":    item.group,
                    "keyword":  item.keyword,
                    "kind":     item.kind,
                }
                row.update(item.statistics)
                writer.writerow(row)

        logger.info(f"Statistics exported to {file_path}")
        return file_path

    def export_filelist(self, file_path: str) -> None:
        """Write the file paths of all input images to a CSV with a 'fpath' column."""
        self.metadata.export_filelist(file_path)
        logger.info(f"File list exported to {file_path}")

    def set_hdf5_path(self, hdf5_path: str) -> None:
        """
        Sets the HDF5 file path for loading images.
        """
        if self.hdf5_path == self._temp_hdf5_path and os.path.exists(self._temp_hdf5_path):
            try:
                os.remove(self._temp_hdf5_path)
            except OSError as e:
                logger.warning("Could not remove temporary HDF5 file %s: %s", self._temp_hdf5_path, e)
        self.hdf5_path = hdf5_path

    def get_steps(self) -> list[dict[str, Any]]:
        """
        Retrieves current processing steps from the model.
        """
        return self.steps.get_steps()

    ### Image Visualization and Analysis ###

    def get_images(self, keys: str | list[str]) -> npt.NDArray[Any] | list[npt.NDArray[Any]]:
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
    
    def make_image(
        self,
        idx: int,
        progress_callback: Callable[[], None] | None = None,
    ) -> tuple[Image, dict[str, float | int]]:
        """
        Makes processed image for given dataframe index.
        """
        if progress_callback:
            progress_callback()
        item = self.metadata.items[idx]
        data = parseH5.get_data(self.hdf5_path, item.hdf5_path)  # Ensure image is loaded
        if progress_callback:
            progress_callback()
        fig, axs = utils.construct_image(data, self.settings)
        _ = axs
        if progress_callback:
            progress_callback()
        if item.statistics is None:
            stats = utils.compute_statistics(data[0])
            item.statistics = stats
        if progress_callback:
            progress_callback()
        stream = utils.fig_to_img(fig, **self.settings.imsave_kwargs())
        plt.close()
        if progress_callback:
            progress_callback()
        return stream, item.statistics

    def make_histogram(
        self,
        idx: int,
        progress_callback: Callable[[], None] | None = None,
    ) -> tuple[Image, dict[str, float | int]]:
        """
        Makes a histogram image for the item at the given metadata index.
        """
        if progress_callback:
            progress_callback()
        item = self.metadata.items[idx]
        data = parseH5.get_data(self.hdf5_path, item.hdf5_path)
        if progress_callback:
            progress_callback()
        fig = utils.construct_histogram(data, self.histogram_settings)
        if progress_callback:
            progress_callback()
        if item.statistics is None:
            stats = utils.compute_statistics(data[0])
            item.statistics = stats
        if progress_callback:
            progress_callback()
        stream = utils.fig_to_img(fig, **self.settings.imsave_kwargs())
        plt.close()
        if progress_callback:
            progress_callback()
        return stream, item.statistics

    def make_group_image(
        self,
        group_id: str | int,
        progress_callback: Callable[[], None] | None = None,
    ) -> tuple[Image, dict[str, Any]]:
        """
        Makes a composite image showing all images in a group.
        Each subplot is titled with the item's keyword.
        Returns a blank statistics dict.
        """
        if progress_callback:
            progress_callback()
        items = [item for item in self.metadata.by_group(group_id)]
        paths = [item.hdf5_path for item in items]
        data_list = parseH5.get_data(self.hdf5_path, paths)
        if progress_callback:
            progress_callback()
        fig, axs = utils.construct_image(data_list, self.settings)
        axs_flat = np.atleast_1d(axs).flatten()
        for i, item in enumerate(items):
            axs_flat[i].set_title(item.keyword, fontsize=self.settings.font_size,
                                   fontfamily=self.settings.font,
                                   fontweight=self.settings.font_weight)
        fig.tight_layout()
        if progress_callback:
            progress_callback()
        stream = utils.fig_to_img(fig, **self.settings.imsave_kwargs())
        plt.close()
        if progress_callback:
            progress_callback()
        return stream, {}

    def make_group_histogram(
        self,
        group_id: str | int,
        progress_callback: Callable[[], None] | None = None,
    ) -> tuple[Image, dict[str, Any]]:
        """
        Makes a composite histogram figure for all images in a group.
        Each subplot is titled with the item's keyword.
        Returns a blank statistics dict.
        """
        if progress_callback:
            progress_callback()
        items = [item for item in self.metadata.by_group(group_id)]
        paths = [item.hdf5_path for item in items]
        data_list = parseH5.get_data(self.hdf5_path, paths)
        if progress_callback:
            progress_callback()
        fig = utils.construct_histogram(data_list, self.histogram_settings)
        axs_flat = np.atleast_1d(fig.axes).flatten()
        for i, item in enumerate(items):
            axs_flat[i].set_title(item.keyword)
        fig.tight_layout()
        if progress_callback:
            progress_callback()
        stream = utils.fig_to_img(fig, **self.settings.imsave_kwargs())
        plt.close()
        if progress_callback:
            progress_callback()
        return stream, {}

    def process_step(self, group: dict[str, str], step: dict[str, Any]) -> npt.NDArray[Any]:
        """
        Processes a single step for a given group of images. Decides operation based on step dictionary.
        Determines whether to use one or two input images based on presence of value or keyword_2.
        """
        assert type(group) == dict, f"Expected group to be a dict, got {type(group)}"
        logger.debug("Group: %s", group)
        item_1 = group[step['keyword1']]
        item_2 = group.get(step['keyword2'])
        value = step.get('value')

        if item_2 is None:
            data1 = self.get_images(item_1)
            return utils.operate(data1, float(value), step['operation'])
        
        data1, data2 = self.get_images([item_1, item_2])
        return utils.operate(data1, data2, step['operation'])
        
    def add_processed(self, fpath: str, group: str, keyword: str) -> None:
        new_key = self.metadata.new_key()
        meta = ImageMeta(
            key=new_key,
            nickname=fpath,
            group=group,
            keyword=keyword,
            kind="processed",
        )
        self.metadata.add(meta)
        parseH5.add_input(self.hdf5_path, meta.hdf5_path, fpath)

    def clear_processed(self) -> None:
        processed_items = [item for item in self.metadata.items if item.kind == "processed"]
        for item in processed_items:
            parseH5.delete(self.hdf5_path, item.hdf5_path)
            self.metadata.delete(item.key)

    def _find_group_shape_mismatches(self) -> list[str]:
        """Return human-readable shape mismatch descriptions for grouped input images."""
        def _short_path(path: str, max_parts: int = 4) -> str:
            norm = os.path.normpath(path)
            parts = norm.split(os.sep)
            if len(parts) <= max_parts:
                return norm
            return os.path.join("...", *parts[-max_parts:])

        required_keywords = set(self.steps.inputs(include_computed=False))
        if not required_keywords:
            return []

        mismatches: list[str] = []
        groups = set(self.metadata.groups(visible_only=True))
        if "default" in groups:
            groups.discard("default")

        for group_id in groups:
            items = [
                item
                for item in self.metadata.by_group(group_id)
                if item.kind == "input" and item.keyword in required_keywords
            ]
            if len(items) < 2:
                continue

            shape_by_keyword: dict[str, tuple[int, ...]] = {}
            path_by_keyword: dict[str, str] = {}
            for item in items:
                image = self.get_images(item.hdf5_path)
                shape = tuple(image.shape)
                if item.keyword is None:
                    continue
                shape_by_keyword[item.keyword] = shape
                path_by_keyword[item.keyword] = item.nickname

            if len(shape_by_keyword) < 2:
                continue

            unique_shapes = set(shape_by_keyword.values())
            if len(unique_shapes) <= 1:
                continue

            common_name = items[0].common_name
            group_label = "".join(common_name).strip() if common_name else str(group_id)
            keyword_lines: list[str] = []
            for keyword in sorted(shape_by_keyword):
                path = path_by_keyword[keyword]
                keyword_lines.append(
                    f"    {keyword}: shape={shape_by_keyword[keyword]}\n"
                    f"      file: {os.path.basename(path)}\n"
                    f"      path: {_short_path(path)}"
                )
            details = "\n".join(keyword_lines)
            mismatches.append(f"- Group: {group_label}\n{details}")

        return mismatches

    def _analyze(
        self,
        group: dict[str, str],
        group_id: str | int,
        progress_callback: Callable[[], None],
    ) -> None:
        self.group_cache.clear()

        # Pull the last used index for each output keyword across all steps to optimize caching strategy
        last_used = self.steps.last_used()

        # Get the common name for the group to construct output nicknames.
        common_name = self.metadata.by_group(group_id)[0].common_name
        assert common_name is not None, f"Expected common_name to be set for group {group_id}"
        group_label = "".join(common_name).strip() or str(group_id)

        for i, step in enumerate(self.steps.get_steps()):
            progress_callback()
            # Perform single operation
            output_keyword = step['output_key']
            try:
                result = self.process_step(group, step)
            except Exception as e:
                msg = (
                    f"Failed processing step {i + 1} for group '{group_label}' "
                    f"(operation={step.get('operation')}, output_key={output_keyword}): {e}"
                )
                logger.exception(msg)
                raise RuntimeError(msg) from e

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
            try:
                parseH5.add_processed(self.hdf5_path, meta.hdf5_path, result)
            except Exception as e:
                msg = (
                    f"Failed saving processed output for step {i + 1} in group '{group_label}' "
                    f"(output_key={output_keyword}): {e}"
                )
                logger.exception(msg)
                raise RuntimeError(msg) from e
            
            # Cache the result if this step's output is used in a future step
            if i < last_used[output_keyword]:
                self.group_cache[output_keyword] = result
                group[meta.keyword] = meta.hdf5_path  

    def analyze(self, idx: int | list[int], progress_callback: Callable[[], None]) -> ValueError | None:
        if self.steps.get_steps() == []:
            logger.warning("Analyze aborted: no processing steps defined")
            return ValueError("No processing steps defined. Please set steps before analyzing.")

        selected_count = len(idx) if isinstance(idx, list) else 1
        logger.info("Analyze started for %d selected item(s)", selected_count)
        logger.info("Configured processing step count: %d", len(self.steps.get_steps()))
        
        self.set_keywords()
        self.set_groups()

        shape_mismatches = self._find_group_shape_mismatches()
        if shape_mismatches:
            max_rows = 10
            shown = shape_mismatches[:max_rows]
            suffix = ""
            if len(shape_mismatches) > max_rows:
                suffix = f"\n... and {len(shape_mismatches) - max_rows} more group(s)."
            message = (
                "Input image sizes do not match within one or more groups. "
                "Please align/crop those files before analyzing.\n\n"
                + "\n".join(shown)
                + suffix
            )
            logger.warning("Analyze aborted due to shape mismatch: %s", message)
            return ValueError(message)

        # groups = set(self.metadata.get_group(idx))
        self.clear_processed()
        groups = set(self.metadata.groups(visible_only=True))
        if "default" in groups:
            groups.discard("default")

        logger.info("Analyze will process %d grouped item set(s)", len(groups))
            
        for group in groups:
            logger.info(f"Processing group: {group}")
            items = self.metadata.by_group(group)
            group_dict = {item.keyword: item.hdf5_path for item in items}
            logger.debug("Group dict for group %s: %s", group, group_dict)
            self._analyze(group_dict, group, progress_callback)

        logger.info("Analyze completed")
    

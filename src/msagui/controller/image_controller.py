import time
import math
from typing import Any
from msagui.view.progress_bar import ProgressBar


class ImageController:
    def __init__(self, model: Any, view: Any) -> None:
        self.model = model
        self.view = view

    def display_images(self, index: int) -> None:
        """Display a processed image and statistics for the selected index."""
        progress_tick, progress_close = self._make_delayed_progress(title="Loading Image", total_steps=5)
        try:
            img, stats = self.model.make_image(index, progress_callback=progress_tick)
            self.view.display.update(img)
            self.display_statistics(stats)
        finally:
            progress_close()

    def display_histograms(self, index: int) -> None:
        """Display a histogram for the image at *index*."""
        progress_tick, progress_close = self._make_delayed_progress(title="Loading Histogram", total_steps=5)
        try:
            img, stats = self.model.make_histogram(index, progress_callback=progress_tick)
            self.view.display.update(img)
            self.display_statistics(stats)
        finally:
            progress_close()

    def display_group(self, group_id: str | int) -> None:
        """Display a composite image of all images in the group."""
        progress_tick, progress_close = self._make_delayed_progress(title="Loading Group Image", total_steps=4)
        try:
            img, _ = self.model.make_group_image(group_id, progress_callback=progress_tick)
            self.view.display.update(img)
            self.view.labels.update('Statistics', '')
        finally:
            progress_close()

    def display_group_histogram(self, group_id: str | int) -> None:
        """Display a composite histogram for all images in the group."""
        progress_tick, progress_close = self._make_delayed_progress(title="Loading Group Histogram", total_steps=4)
        try:
            img, _ = self.model.make_group_histogram(group_id, progress_callback=progress_tick)
            self.view.display.update(img)
            self.view.labels.update('Statistics', '')
        finally:
            progress_close()

    def _make_delayed_progress(
        self,
        title: str,
        total_steps: int,
        delay_seconds: float = 1.0,
    ) -> tuple[Any, Any]:
        """Create a callback pair that shows a progress bar only after a delay."""
        started_at = time.perf_counter()
        progress: ProgressBar | None = None

        def tick() -> None:
            nonlocal progress
            elapsed = time.perf_counter() - started_at
            if progress is None and elapsed >= delay_seconds:
                progress = ProgressBar(title=title, total=total_steps)
                progress.draw_progress()
            if progress is not None:
                progress.step()

        def close() -> None:
            if progress is not None and progress.winfo_exists():
                progress.destroy()

        return tick, close
        
    def _format_statistics(self, stats: dict[str, Any]) -> str:
        """Format per-image statistics for display in a two-line label."""

        def get_value(*keys: str) -> Any:
            for key in keys:
                if key in stats and stats[key] is not None:
                    return stats[key]
            return None

        mean = get_value("mean")
        median = get_value("median")
        max_signal = get_value("max_signal", "max")
        std_dev = get_value("standard_deviation", "stdev")
        std_err = get_value("standard_error", "se")
        count = get_value("count")

        def fmt_float(value: Any) -> str:
            if value is None:
                return "—"
            val = float(value)
            return "—" if not math.isfinite(val) else f"{val:.3f}"

        def fmt_count(value: Any) -> str:
            return "—" if value is None else f"{int(value):,}"

        line1 = f"Mean: {fmt_float(mean)} | Median: {fmt_float(median)} | Max: {fmt_float(max_signal)}"
        line2 = f"Std Dev: {fmt_float(std_dev)} | Std Err: {fmt_float(std_err)} | Count: {fmt_count(count)}"
        return line1 + "\n" + line2

    def display_statistics(self, stats: dict[str, Any]) -> None:
        """Display statistics text unless currently in group-view mode."""
        if self.view.show_groups.get():
            self.view.labels.update('Statistics', "Group view: per-image statistics hidden.")
            return
        self.view.labels.update('Statistics', self._format_statistics(stats))

    def update_display(self, idx: int | str) -> None:
        """Route to the correct display mode based on view toggles."""
        if self.view.show_groups.get():
            if self.view.show_histograms.get():
                self.display_group_histogram(idx)
            else:
                self.display_group(idx)
        elif self.view.show_histograms.get():
            self.display_histograms(idx)
        else:
            self.display_images(idx)
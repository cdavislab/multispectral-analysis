from typing import Any


class ImageController:
    def __init__(self, model: Any, view: Any) -> None:
        self.model = model
        self.view = view

    def display_images(self, index: int) -> None:
        """Display a processed image and statistics for the selected index."""
        img, stats = self.model.make_image(index)
        self.view.display.update(img)
        self.display_statistics(stats)

    def display_histograms(self, index: int) -> None:
        """Display a histogram for the image at *index*."""
        img, stats = self.model.make_histogram(index)
        self.view.display.update(img)
        self.display_statistics(stats)

    def display_group(self, group_id: str | int) -> None:
        """Display a composite image of all images in the group."""
        img, _ = self.model.make_group_image(group_id)
        self.view.display.update(img)
        self.view.labels.update('Statistics', '')

    def display_group_histogram(self, group_id: str | int) -> None:
        """Display a composite histogram for all images in the group."""
        img, _ = self.model.make_group_histogram(group_id)
        self.view.display.update(img)
        self.view.labels.update('Statistics', '')
        
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
            return "—" if value is None else f"{float(value):.3f}"

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
import csv
import logging
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
from typing import Any
from msagui.view.steps_view import MultiCorrectionsDialog

_STEP_FIELDS = ["keyword1", "operation", "keyword2", "value", "output_key"]

logger = logging.getLogger(__name__)

class StepsController:
    def __init__(self, model: Any, view: Any) -> None:
        self.model = model
        self.view = view
        self.dialog: MultiCorrectionsDialog | None = None
        
    def open(self) -> None:
        """Open dialog to input multiple corrections and factors."""
        logger.debug("Opening steps dialog")
        if self.dialog is not None:
            try:
                if self.dialog.winfo_exists():
                    self.dialog.lift()
                    self.dialog.focus_force()
                    logger.debug("Reusing existing steps dialog")
                    return
            except Exception:
                logger.exception("Failed to focus existing steps dialog; recreating")
                self.dialog = None

        self.dialog = MultiCorrectionsDialog(self.view.root, self.model.get_steps())
        self.dialog.bind("<Destroy>", self._on_dialog_destroyed)
        self.dialog.save_button.config(command=self.close)
        self.dialog.import_button.config(command=self.import_steps)
        self.dialog.export_button.config(command=self.export_steps)

    def _on_dialog_destroyed(self, _event: Any = None) -> None:
        """Clear cached dialog reference when the dialog is destroyed."""
        if self.dialog is None:
            return
        if _event is not None and _event.widget is not self.dialog:
            return
        self.dialog = None

    def _parse_steps_csv(self, reader: csv.DictReader) -> list[dict[str, str]]:
        """Validate and parse step rows from a DictReader."""
        header = reader.fieldnames or []
        if header != _STEP_FIELDS:
            expected = ", ".join(_STEP_FIELDS)
            found_full = ", ".join(header) if header else "<missing header>"
            found = (found_full[:50] + "...") if len(found_full) > 50 else found_full
            raise ValueError(
                "Invalid step file format.\n\n"
                f"Expected header:\n{expected}\n\n"
                f"Found:\n{found}"
            )

        steps = []
        for row_idx, row in enumerate(reader, start=2):
            if any(k not in row for k in _STEP_FIELDS):
                raise ValueError(f"Invalid row format at line {row_idx}.")
            cleaned = {k: (row.get(k, "") or "").strip() for k in _STEP_FIELDS}
            steps.append(cleaned)

        validation_errors = self._validate_steps(steps)
        if validation_errors:
            raise ValueError(
                "Invalid step definitions in imported file:\n\n" + "\n".join(validation_errors)
            )
        return steps

    def _validate_steps(self, steps: list[dict[str, str]]) -> list[str]:
        """Return human-readable validation errors for a full step list."""
        validation_errors: list[str] = []

        all_input_keywords: set[str] = set()
        for step in steps:
            keyword1 = step.get("keyword1", "").strip()
            keyword2 = step.get("keyword2", "").strip()
            if keyword1:
                all_input_keywords.add(keyword1)
            if keyword2:
                all_input_keywords.add(keyword2)

        seen_output_keys: set[str] = set()
        for row_num, step in enumerate(steps, start=1):
            keyword1 = step.get("keyword1", "").strip()
            keyword2 = step.get("keyword2", "").strip()
            output_key = step.get("output_key", "").strip()

            if not (keyword1 and step.get("operation", "").strip() and output_key):
                continue

            if output_key == keyword1:
                validation_errors.append(
                    f"Step {row_num}: output key cannot match keyword1 ('{output_key}')."
                )
            if keyword2 and output_key == keyword2:
                validation_errors.append(
                    f"Step {row_num}: output key cannot match keyword2 ('{output_key}')."
                )

            if output_key in all_input_keywords:
                validation_errors.append(
                    f"Step {row_num}: output key '{output_key}' cannot match any input keyword used in steps."
                )

            if output_key in seen_output_keys:
                validation_errors.append(
                    f"Step {row_num}: output key '{output_key}' is duplicated across steps."
                )
            seen_output_keys.add(output_key)

        return validation_errors

    def import_steps(self) -> None:
        """Load steps from a CSV file and populate the dialog view."""
        if self.dialog is None:
            return
        dialog = self.dialog

        file_path = filedialog.askopenfilename(
            parent=dialog,
            title="Import Steps",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not file_path:
            logger.debug("Steps import canceled by user")
            return
        try:
            with open(file_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                steps = self._parse_steps_csv(reader)
        except ValueError as e:
            logger.warning("Invalid steps CSV format for %s: %s", file_path, e)
            messagebox.showerror("Import Error", str(e), parent=dialog)
            return
        except Exception as e:
            logger.exception("Failed to import steps from %s", file_path)
            messagebox.showerror("Import Error", f"Failed to read file:\n{e}", parent=dialog)
            return
        logger.info("Imported %d step(s) from %s", len(steps), file_path)
        dialog.load_step_data(steps)

    def export_steps(self) -> None:
        """Write the current dialog step entries to a CSV file."""
        if self.dialog is None:
            return
        dialog = self.dialog

        file_path = filedialog.asksaveasfilename(
            parent=dialog,
            title="Export Steps",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not file_path:
            logger.debug("Steps export canceled by user")
            return
        steps = dialog.get_step_data()
        try:
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=_STEP_FIELDS)
                writer.writeheader()
                writer.writerows(steps)
            logger.info("Exported %d step(s) to %s", len(steps), file_path)
        except Exception as e:
            logger.exception("Failed to export steps to %s", file_path)
            messagebox.showerror("Export Error", f"Failed to write file:\n{e}", parent=dialog)
        
    def close(self) -> None:
        """Collect all steps and close dialog."""
        logger.debug("Saving steps and closing dialog")
        if self.dialog is None:
            return

        steps = []
        for row_num, row in enumerate(self.dialog.step_rows, start=1):
            _, keyword, operation, keyword2, value, output_key, _, _, _ = row
            step = {
                "keyword1": keyword.get().strip(),
                "operation": operation.get().strip(),
                "keyword2": keyword2.get().strip(),
                "value": value.get().strip(),
                "output_key": output_key.get().strip()
            }
            if step["keyword1"] and step["operation"] and step["output_key"]:
                steps.append(step)

        validation_errors = self._validate_steps(steps)

        if validation_errors:
            messagebox.showerror(
                "Invalid Step Configuration",
                "Please fix the following before saving:\n\n" + "\n".join(validation_errors),
                parent=self.dialog,
            )
            logger.warning("Step validation failed: %s", validation_errors)
            return

        self.dialog.destroy()
        logger.debug("Collected steps: %s", steps)
        self.model.steps.set_steps(steps)
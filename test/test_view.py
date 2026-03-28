import pytest
import tkinter as tk
from collections.abc import Iterator
from typing import Any
from msagui.view.main_view import MultispectralView
from msagui.view.display import DisplayView, ListboxView, WidgetsView
from msagui.view.progress_bar import ProgressBar

@pytest.fixture
def tk_root() -> Iterator[tk.Tk]:
    root = tk.Tk()
    yield root
    root.destroy()

def test_multispectral_view_initialization(tk_root: tk.Tk) -> None:
    """Verify main view initializes core widget groups."""
    view = MultispectralView(tk_root)
    assert view.root == tk_root
    assert hasattr(view, 'buttons')
    assert hasattr(view, 'labels')
    assert hasattr(view, 'listbox')
    assert hasattr(view, 'display')

def test_multispectral_view_get_widget(tk_root: tk.Tk) -> None:
    """Placeholder for get_widget behavior checks (currently intentionally empty)."""
    pass
    # view = MultispectralView(tk_root)
    # widget = view.get_widget("Filename")
    # assert widget is not None
    # assert widget.cget("text") == "Filename"
    # with pytest.raises(ValueError):
    #     view.get_widget("NonExistentWidget")

def test_show_error_formats_file_specific_messages(tk_root: tk.Tk, monkeypatch: Any) -> None:
    """Verify show_error popup includes per-file reason details."""
    view = MultispectralView(tk_root)
    called: dict[str, str] = {}

    def fake_showerror(title: str, message: str) -> None:
        called["title"] = title
        called["message"] = message

    monkeypatch.setattr("msagui.view.main_view.messagebox.showerror", fake_showerror)

    view.show_error({"/tmp/bad.csv": ValueError("contains non-numeric text")})

    assert called["title"] == "Input Data Error"
    assert "/tmp/bad.csv" in called["message"]
    assert "non-numeric text" in called["message"]

def test_listbox_view_update_and_selection(tk_root: tk.Tk) -> None:
    """Verify listbox updates entries and returns selected indices."""
    view = MultispectralView(tk_root)
    listbox_view = ListboxView(view.paned_window)
    files = ["file1.tif", "file2.tif", "file3.tif"]
    listbox_view.update(files)
    assert listbox_view.file_list.size() == 3
    # Select first and last
    listbox_view.file_list.selection_set(0)
    listbox_view.file_list.selection_set(2)
    selected = listbox_view.get_selected_indices()
    assert selected == [0, 2]

def test_widgets_view_update(tk_root: tk.Tk) -> None:
    """Verify WidgetsView updates existing keys and rejects unknown keys."""
    widgets = {"TestLabel": dict(row=0, column=0, rowspan=1, columnspan=1, sticky="nsew")}
    widgets_view = WidgetsView(tk_root, widgets, tk.Label) # pyright: ignore[reportArgumentType]
    widgets_view.update("TestLabel", "UpdatedText")
    assert widgets_view.items["TestLabel"].cget("text") == "UpdatedText"
    with pytest.raises(ValueError):
        widgets_view.update("NonExistent", "Value")

def test_progress_bar_steps(monkeypatch: Any) -> None:
    """Verify progress bar step increments progress without exceeding max."""
    pb = ProgressBar(total=10)
    pb.progress = 0
    pb.step()
    assert pb.progress > 0
    pb.progress = 99
    pb.step()
    assert pb.progress <= 100
    pb.destroy()

def test_progress_bar_context_manager() -> None:
    """Verify progress bar context manager yields and cleans up dialog."""
    with ProgressBar(total=5) as pb:
        assert isinstance(pb, ProgressBar)
        pb.step()
        pb.draw_progress()
        assert pb.progress > 1
    # Should be destroyed after context

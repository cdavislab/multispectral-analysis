import pytest
import tkinter as tk
from msagui.view.main_view import MultispectralView
from msagui.view.display import DisplayView, ListboxView, WidgetsView
from msagui.view.progress_bar import ProgressBar

@pytest.fixture
def tk_root():
    root = tk.Tk()
    yield root
    root.destroy()

def test_multispectral_view_initialization(tk_root):
    view = MultispectralView(tk_root)
    assert view.root == tk_root
    assert hasattr(view, 'buttons')
    assert hasattr(view, 'labels')
    assert hasattr(view, 'listbox')
    assert hasattr(view, 'display')

def test_multispectral_view_get_widget(tk_root):
    pass
    # view = MultispectralView(tk_root)
    # widget = view.get_widget("Filename")
    # assert widget is not None
    # assert widget.cget("text") == "Filename"
    # with pytest.raises(ValueError):
    #     view.get_widget("NonExistentWidget")

def test_listbox_view_update_and_selection(tk_root):
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

def test_widgets_view_update(tk_root):
    widgets = {"TestLabel": dict(row=0, column=0, rowspan=1, columnspan=1, sticky="nsew")}
    widgets_view = WidgetsView(tk_root, widgets, tk.Label) # pyright: ignore[reportArgumentType]
    widgets_view.update("TestLabel", "UpdatedText")
    assert widgets_view.items["TestLabel"].cget("text") == "UpdatedText"
    with pytest.raises(ValueError):
        widgets_view.update("NonExistent", "Value")

def test_progress_bar_steps(monkeypatch):
    pb = ProgressBar(total=10)
    pb.progress = 0
    pb.step()
    assert pb.progress > 0
    pb.progress = 99
    pb.step()
    assert pb.progress <= 100
    pb.destroy()

def test_progress_bar_context_manager():
    with ProgressBar(total=5) as pb:
        assert isinstance(pb, ProgressBar)
        pb.step()
        pb.draw_progress()
        assert pb.progress > 1
    # Should be destroyed after context

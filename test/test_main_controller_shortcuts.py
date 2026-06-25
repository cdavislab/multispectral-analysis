from msagui.controller.main_controller import ControllerDispatcher


class _BoolVar:
    def __init__(self, value: bool) -> None:
        self._value = value

    def get(self) -> bool:
        return self._value

    def set(self, value: bool) -> None:
        self._value = value


class _DropDownStub:
    def toggle_checkbox(self, checkbox: _BoolVar) -> None:
        checkbox.set(not checkbox.get())


class _ViewStub:
    def __init__(self) -> None:
        self.show_histograms = _BoolVar(False)


def test_handle_histogram_shortcut_toggles_and_breaks() -> None:
    """Ctrl+H handler toggles histogram visibility and returns 'break'."""
    dispatcher = ControllerDispatcher.__new__(ControllerDispatcher)
    dispatcher.view = _ViewStub()
    dispatcher.dropdown_ctrl = _DropDownStub()

    result = dispatcher._handle_histogram_shortcut(event=None)

    assert dispatcher.view.show_histograms.get() is True
    assert result == "break"

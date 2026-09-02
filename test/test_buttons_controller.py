from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest

from msagui.controller.buttons_controller import ButtonsController


def test_save_image_csv_writes_raw_image_values(tmp_path: Path) -> None:
    expected = np.array([[1.5, 2.0], [3.25, 4.75]])
    model = SimpleNamespace(
        metadata=SimpleNamespace(
            items=[SimpleNamespace(hdf5_path="image-1")]
        ),
        get_images=lambda path: expected,
    )
    controller = ButtonsController(model, view=SimpleNamespace())
    output_path = tmp_path / "nested" / "image-1.csv"

    controller._save_image_csv(
        str(output_path),
        {"kind": "item_image", "idx": 0},
    )

    np.testing.assert_allclose(np.loadtxt(output_path, delimiter=","), expected)


def test_save_image_csv_rejects_non_image_tasks(tmp_path: Path) -> None:
    model = SimpleNamespace(
        metadata=SimpleNamespace(items=[]),
        get_images=lambda path: np.ones((2, 2)),
    )
    controller = ButtonsController(model, view=SimpleNamespace())

    with pytest.raises(ValueError, match="individual images"):
        controller._save_image_csv(
            str(tmp_path / "group.csv"),
            {"kind": "group_image", "group_id": "group-1"},
        )
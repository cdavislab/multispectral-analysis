from pathlib import Path

import numpy as np
import pytest

from msagui.model.loader import load


def test_load_csv_with_non_numeric_text_raises_friendly_error(tmp_path: Path) -> None:
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text("1,2,3\n4,hello,6\n")

    with pytest.raises(ValueError, match="contains non-numeric text"):
        load(str(bad_csv))


def test_load_unsupported_extension_raises_friendly_error(tmp_path: Path) -> None:
    bad_file = tmp_path / "bad.txt"
    bad_file.write_text("1,2,3\n")

    with pytest.raises(ValueError, match="unsupported file type"):
        load(str(bad_file))


def test_load_valid_numeric_csv_succeeds(tmp_path: Path) -> None:
    good_csv = tmp_path / "good.csv"
    expected = np.array([[1.0, 2.0], [3.0, 4.0]])
    np.savetxt(good_csv, expected, delimiter=",")

    result = load(str(good_csv))
    assert np.allclose(result, expected)


def test_load_empty_csv_raises_friendly_error(tmp_path: Path) -> None:
    empty_csv = tmp_path / "empty.csv"
    empty_csv.write_text("")

    with pytest.raises(ValueError, match="contains no data"):
        load(str(empty_csv))

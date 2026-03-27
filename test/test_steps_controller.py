import csv
import io

import pytest

from msagui.controller.steps_controller import StepsController


def _controller() -> StepsController:
    return StepsController(model=None, view=None)


def test_validate_steps_allows_output_used_later_as_input() -> None:
    """Output keys may be reused as inputs in later steps."""
    steps = [
        {"keyword1": "A", "operation": "+", "keyword2": "B", "value": "", "output_key": "C"},
        {"keyword1": "C", "operation": "*", "keyword2": "D", "value": "", "output_key": "E"},
    ]

    errors = _controller()._validate_steps(steps)
    assert errors == []


def test_validate_steps_blocks_output_used_earlier_as_input() -> None:
    """Output keys are invalid when the same keyword is consumed before it is produced."""
    steps = [
        {"keyword1": "C", "operation": "*", "keyword2": "D", "value": "", "output_key": "E"},
        {"keyword1": "A", "operation": "+", "keyword2": "B", "value": "", "output_key": "C"},
    ]

    errors = _controller()._validate_steps(steps)
    assert any("input key" in err for err in errors)


def test_validate_steps_blocks_duplicate_output_keys() -> None:
    """Duplicate output keys remain disallowed across steps."""
    steps = [
        {"keyword1": "A", "operation": "+", "keyword2": "B", "value": "", "output_key": "C"},
        {"keyword1": "D", "operation": "*", "keyword2": "E", "value": "", "output_key": "C"},
    ]

    errors = _controller()._validate_steps(steps)
    assert any("duplicated across steps" in err for err in errors)


def test_parse_steps_csv_allows_output_used_later_as_input() -> None:
    """CSV import accepts steps where a produced output is consumed in later rows."""
    csv_text = (
        "keyword1,operation,keyword2,value,output_key\n"
        "A,+,B,,C\n"
        "C,*,D,,E\n"
    )
    reader = csv.DictReader(io.StringIO(csv_text))

    steps = _controller()._parse_steps_csv(reader)
    assert len(steps) == 2
    assert steps[0]["output_key"] == "C"
    assert steps[1]["keyword1"] == "C"


def test_parse_steps_csv_allows_output_used_before_produced() -> None:
    """CSV import does not enforce cross-step semantic ordering."""
    csv_text = (
        "keyword1,operation,keyword2,value,output_key\n"
        "C,*,D,,E\n"
        "A,+,B,,C\n"
    )
    reader = csv.DictReader(io.StringIO(csv_text))

    steps = _controller()._parse_steps_csv(reader)
    assert len(steps) == 2


def test_parse_steps_csv_rejects_invalid_header() -> None:
    """CSV import still validates required header fields."""
    csv_text = (
        "keyword1,operation,keyword2,value\n"
        "A,+,B,\n"
    )
    reader = csv.DictReader(io.StringIO(csv_text))

    with pytest.raises(ValueError, match="Invalid step file format"):
        _controller()._parse_steps_csv(reader)

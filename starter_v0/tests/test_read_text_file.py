"""Offline tests for uploaded TXT reading."""
import importlib
from pathlib import Path

import pytest

from tools import TOOL_FUNCTIONS

module = importlib.import_module("tools.read_text_file.tool")


@pytest.fixture
def uploaded_text(tmp_path, monkeypatch):
    monkeypatch.setattr(module, "UPLOADS_DIR", tmp_path)
    file_id = "a" * 32 + ".txt"
    (tmp_path / file_id).write_bytes("\ufeffDòng một\r\nDòng hai\r\nDòng ba".encode("utf-8"))
    return file_id


def test_read_text_file_reads_requested_lines_and_paginates(uploaded_text):
    first = TOOL_FUNCTIONS["read_text_file"](uploaded_text, max_lines=2)
    assert first["content"] == "Dòng một\nDòng hai"
    assert first["total_lines"] == 3
    assert first["end_line"] == 2
    assert first["lines_returned"] == 2
    assert first["has_more"] is True
    assert first["untrusted_content"] is True
    last = TOOL_FUNCTIONS["read_text_file"](uploaded_text, start_line=first["next_line"])
    assert last["content"] == "Dòng ba"
    assert last["has_more"] is False
    assert last["next_line"] is None


@pytest.mark.parametrize("kwargs", [
    {"file_id": "../../secret.txt"}, {"file_id": None},
    {"start_line": 0}, {"start_line": "1"}, {"start_line": True},
    {"max_lines": 0}, {"max_lines": 201}, {"max_lines": "5"},
])
def test_read_text_file_rejects_bad_input(uploaded_text, kwargs):
    result = TOOL_FUNCTIONS["read_text_file"](**{"file_id": uploaded_text, **kwargs})
    assert result["error"] == "ValueError"


def test_read_text_file_permission_error_returns_dict(uploaded_text, monkeypatch):
    def denied(*args, **kwargs):
        raise PermissionError("Access denied")
    monkeypatch.setattr(Path, "open", denied)
    assert TOOL_FUNCTIONS["read_text_file"](uploaded_text)["error"] == "PermissionError"


def test_read_text_file_missing_file_returns_dict(uploaded_text):
    assert TOOL_FUNCTIONS["read_text_file"]("b" * 32 + ".txt")["error"] == "FileNotFoundError"


@pytest.mark.parametrize("data", [b"\xff\xfe", b"binary\x00data", b"x" * (256 * 1024 + 1)])
def test_read_text_file_rejects_encoding_binary_and_oversize(uploaded_text, data):
    (module.UPLOADS_DIR / uploaded_text).write_bytes(data)
    assert "error" in TOOL_FUNCTIONS["read_text_file"](uploaded_text)


def test_read_text_file_empty_and_beyond_eof(uploaded_text):
    result = TOOL_FUNCTIONS["read_text_file"](uploaded_text, start_line=50)
    assert result["content"] == ""
    assert result["end_line"] is None
    assert result["has_more"] is False
    (module.UPLOADS_DIR / uploaded_text).write_bytes(b"")
    result = TOOL_FUNCTIONS["read_text_file"](uploaded_text)
    assert result["total_lines"] == 0
    assert result["lines_returned"] == 0

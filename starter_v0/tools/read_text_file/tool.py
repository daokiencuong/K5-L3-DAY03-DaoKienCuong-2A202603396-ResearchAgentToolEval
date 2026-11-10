"""Read a bounded range of lines from an uploaded UTF-8 TXT file."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

UPLOADS_DIR = Path(__file__).resolve().parents[2] / "text_uploads"
MAX_FILE_BYTES = 256 * 1024


def validate_text_file(data: bytes) -> str:
    if len(data) > MAX_FILE_BYTES:
        raise ValueError("TXT file must be at most 256 KiB")
    text = data.decode("utf-8-sig")
    if "\x00" in text:
        raise ValueError("Binary files are not supported; upload UTF-8 TXT")
    return text


def read_text_file(file_id: str = "", start_line: int = 1, max_lines: int = 100) -> dict[str, Any]:
    try:
        if not isinstance(file_id, str) or not re.fullmatch(r"[a-f0-9]{32}\.txt", file_id):
            raise ValueError("Use the exact file_id supplied after uploading a TXT file")
        if type(start_line) is not int or start_line < 1:
            raise ValueError("start_line must be an integer >= 1")
        if type(max_lines) is not int or not 1 <= max_lines <= 200:
            raise ValueError("max_lines must be an integer between 1 and 200")
        path = (UPLOADS_DIR / file_id).resolve()
        if not path.is_relative_to(UPLOADS_DIR.resolve()):
            raise ValueError("File must be inside text_uploads")
        with path.open("rb") as handle:
            data = handle.read(MAX_FILE_BYTES + 1)
        lines = validate_text_file(data).splitlines()
        selected = lines[start_line - 1:start_line - 1 + max_lines]
        end_line = start_line + len(selected) - 1 if selected else None
        return {
            "tool": "read_text_file", "file_id": file_id,
            "content": "\n".join(selected), "total_lines": len(lines),
            "start_line": start_line, "end_line": end_line,
            "lines_returned": len(selected),
            "has_more": bool(selected) and end_line < len(lines),
            "next_line": end_line + 1 if selected and end_line < len(lines) else None,
            "untrusted_content": True,
        }
    except Exception as exc:
        return {"tool": "read_text_file", "error": type(exc).__name__, "message": str(exc)}

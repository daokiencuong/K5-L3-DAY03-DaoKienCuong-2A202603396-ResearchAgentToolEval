"""Export collected research items without making network requests."""
from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any
from uuid import uuid4

EXPORTS_DIR = Path(__file__).resolve().parents[2] / "exports"
COLUMNS = ("title", "url", "source", "summary")


def _spreadsheet_text(value: str) -> str:
    # CSV readers may interpret untrusted source text as a formula.
    if value.lstrip().startswith(("=", "+", "-", "@")) or value.startswith(("\t", "\r", "\n")):
        return "'" + value
    return value


def export_report(
    items: list[dict[str, Any]] | None = None,
    file_format: str = "md",
    filename: str = "research_report",
    headline: str = "",
) -> dict[str, Any]:
    """Return an exported file path, or an error dict; never overwrite files."""
    path = None
    try:
        if not isinstance(file_format, str) or file_format not in {"md", "csv", "xlsx"}:
            raise ValueError("file_format must be md, csv, or xlsx")
        if not isinstance(filename, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", filename):
            raise ValueError("filename must be 1-80 letters, digits, underscores or hyphens, without extension")
        if not isinstance(headline, str):
            raise ValueError("headline must be a string")
        if not isinstance(items, list) or not items:
            raise ValueError("items must be a non-empty list of research objects")
        rows = []
        for item in items:
            if not isinstance(item, dict):
                raise ValueError("each item must be an object")
            row = {}
            for column in COLUMNS:
                value = item.get(column)
                if value is not None and not isinstance(value, str):
                    raise ValueError(f"{column} must be a string or null")
                row[column] = value or ""
            if not any(row.values()):
                raise ValueError("each item must contain at least one non-empty research field")
            rows.append(row)

        EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
        # Exclusive creation plus unique suffix protects previous reports.
        candidate = EXPORTS_DIR / f"{filename}_{uuid4().hex}.{file_format}"
        with candidate.open("xb") as handle:
            path = candidate
            if file_format == "xlsx":
                from openpyxl import Workbook
                from openpyxl.styles import Alignment, Font

                workbook = Workbook()
                sheet = workbook.active
                sheet.title = "Research sources"
                sheet.append(list(COLUMNS))
                for row in rows:
                    sheet.append([row[column] for column in COLUMNS])
                # Explicit text cells prevent formula evaluation, preserving raw text.
                for cells in sheet.iter_rows():
                    for cell in cells:
                        cell.data_type = "s"
                        cell.alignment = Alignment(vertical="top", wrap_text=True)
                for cell in sheet[1]:
                    cell.font = Font(bold=True)
                for column, width in zip("ABCD", (40, 55, 25, 80)):
                    sheet.column_dimensions[column].width = width
                sheet.freeze_panes = "A2"
                sheet.auto_filter.ref = sheet.dimensions
                workbook.save(handle)
            else:
                import io

                output = io.StringIO(newline="")
                if file_format == "csv":
                    writer = csv.DictWriter(output, fieldnames=COLUMNS)
                    writer.writeheader()
                    writer.writerows({key: _spreadsheet_text(value) for key, value in row.items()} for row in rows)
                    content = output.getvalue().encode("utf-8-sig")
                else:
                    output.write(f"# {headline or 'Research report'}\n\n")
                    for index, row in enumerate(rows, 1):
                        output.write(f"## {index}. {row['title'] or 'Untitled'}\n\n")
                        output.write(f"URL: {row['url']}\n\nSource: {row['source']}\n\n{row['summary']}\n\n")
                    content = output.getvalue().encode("utf-8")
                handle.write(content)
        return {
            "tool": "export_report", "status": "exported",
            "file_path": str(path.resolve()), "file_format": file_format,
            "item_count": len(rows),
        }
    except Exception as exc:
        if path is not None:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
        return {"tool": "export_report", "error": type(exc).__name__, "message": str(exc)}

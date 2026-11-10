---
name: export_report
track: core
kind: local_formatter
requires_env: []
inputs: [items, file_format, filename, headline]
outputs: [status, file_path, file_format, item_count]
side_effect: local_file_write
requires_confirmation: false
---
# export_report

Export already-collected research items to Markdown, CSV or Excel (.xlsx).
Use when the user explicitly requests a file export. Do not search for data,
invent items, or export automatically. Missing data should be collected first.

Pass the `items` array from lookup or compatible tools, not the entire response.
Fields: title, url, source, summary (string or null; missing fields become empty).
Extra fields such as score are ignored. Empty items or invalid input return an
error dict. filename is a basename without extension (ASCII letters/digits/_/-).

Files are uniquely named under starter_v0/exports; existing files are not replaced.
CSV uses UTF-8 BOM and neutralizes spreadsheet formula prefixes. XLSX cells are
explicit text. Excel requires openpyxl from requirements.txt.
headline is used for Markdown only. Successful output returns an absolute local
file_path; it is not a public download URL. The UI must provide a download button.

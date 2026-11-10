"""Contract tests: tools.yaml (what the MODEL sees) must match the Python code (what RUNS).

These pass on the starter code. Keep them green every time you rename, add, or change a tool.
"""
from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest
import yaml

from tools import TOOL_FUNCTIONS, load_tool_declarations, to_openai_tools

ROOT = Path(__file__).resolve().parents[1]
VERSION_TOOLS = {
    "v0": "tools.yaml",
    "v1": "tools_v1.yaml",
}

DECLARATIONS_BY_VERSION = {
    version: load_tool_declarations(ROOT / "artifacts" / filename)
    for version, filename in VERSION_TOOLS.items()
}

TOOL_CASES = [
    pytest.param(
        version,
        declaration,
        id=f"{version}-{declaration['name']}",
    )
    for version, declarations in DECLARATIONS_BY_VERSION.items()
    for declaration in declarations
]

EVAL_CONFIGS = [
    ("eval_base.json", "v0"),
    ("eval_base.json", "v1"),
    ("eval_research_extension.json", "v0"),
    ("eval_research_extension.json", "v1"),
    ("eval_group.json", "v1"),
]

@pytest.mark.parametrize("version", VERSION_TOOLS)
def test_tool_names_are_unique(version):
    declarations = DECLARATIONS_BY_VERSION[version]
    names = [item["name"] for item in declarations]
    assert len(names) == len(set(names))


@pytest.mark.parametrize("version,declaration", TOOL_CASES)
def test_every_declared_tool_has_implementation(version, declaration):
    name = declaration["name"]
    assert name in TOOL_FUNCTIONS, f"{version}: {name} chưa có implementation"


@pytest.mark.parametrize("version,declaration", TOOL_CASES)
def test_declared_params_exist_in_function_signature(version, declaration):
    name = declaration["name"]
    func = TOOL_FUNCTIONS[name]
    accepted = set(inspect.signature(func).parameters)
    declared = set(declaration.get("parameters", {}).get("properties", {}))
    assert declared <= accepted, (
        f"{version}/{name}: tham số không được hàm hỗ trợ: "
        f"{declared - accepted}"
    )


@pytest.mark.parametrize("version,declaration", TOOL_CASES)
def test_required_params_are_declared(version, declaration):
    params = declaration.get("parameters", {})
    missing = set(params.get("required", [])) - set(params.get("properties", {}))
    assert not missing, f"{version}/{declaration['name']}: {missing}"


@pytest.mark.parametrize("version,declaration", TOOL_CASES)
def test_description_is_not_empty(version, declaration):
    assert declaration.get("description", "").strip(), (
        f"{version}/{declaration['name']}: thiếu description"
    )


@pytest.mark.parametrize("version", VERSION_TOOLS)
def test_openai_tool_schema_shape(version):
    for tool in to_openai_tools(DECLARATIONS_BY_VERSION[version]):
        assert tool["type"] == "function"
        assert tool["function"]["parameters"]["type"] == "object"


@pytest.mark.parametrize("version,declaration", TOOL_CASES)
def test_tool_folder_has_tool_md_with_matching_name(version, declaration):
    name = declaration["name"]
    matches = []
    for tool_md in (ROOT / "tools").glob("*/TOOL.md"):
        front = tool_md.read_text(encoding="utf-8").split("---")[1]
        if (yaml.safe_load(front) or {}).get("name") == name:
            matches.append(tool_md)
    assert matches, f"{version}/{name}: thiếu TOOL.md có name khớp"


@pytest.mark.parametrize("eval_file,version", EVAL_CONFIGS)
def test_eval_cases_only_expect_declared_tools(eval_file, version):
    declared = {
        item["name"] for item in DECLARATIONS_BY_VERSION[version]
    }
    data = json.loads(
        (ROOT / "data" / eval_file).read_text(encoding="utf-8")
    )
    for case in data.get("cases", []):
        for call in case.get("expect", {}).get("tool_calls", []):
            assert call["name"] in declared, (
                f"{version}/{eval_file}:{case['id']} "
                f"expects undeclared tool {call['name']}"
            )
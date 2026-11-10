import json
import hashlib
from pathlib import Path

runs = [
    ('v0', 'starter_v0/runs/v0_B_base_openai_20261110T124508385370.json'),
    ('v1', 'starter_v0/runs/v1_B_base_openai_20261110T124619855103.json'),
    ('v2', 'starter_v0/runs/v2_B_base_openai_20261110T124718950146.json'),
]

print("=====================================================================")
print("1. KIỂM TRA PROMPT & TOOLS HASH CỦA TỪNG VERSION")
print("=====================================================================")

def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

files_to_check = {
    'v0': ('starter_v0/artifacts/system_prompt.md', 'starter_v0/artifacts/tools.yaml'),
    'v1': ('starter_v0/artifacts/system_prompt_v1.md', 'starter_v0/artifacts/tools_v1.yaml'),
    'v2': ('starter_v0/artifacts/system_prompt_v2.md', 'starter_v0/artifacts/tools_v2.yaml'),
}

for ver, (p_file, t_file) in files_to_check.items():
    p_hash = sha256_file(p_file)
    t_hash = sha256_file(t_file)
    print(f"[{ver.upper()} Physical Files]")
    print(f"  Prompt file : {p_file}")
    print(f"  Prompt hash : {p_hash}")
    print(f"  Tools file  : {t_file}")
    print(f"  Tools hash  : {t_hash}")
    print()

print("=====================================================================")
print("2. ĐỐI CHIẾU METADATA TRONG RUN FILES")
print("=====================================================================")

for label, rpath in runs:
    with open(rpath, encoding='utf-8') as f:
        data = json.load(f)
    print(f"Run file: {rpath}")
    print(f"  Recorded version         : {data.get('version')}")
    print(f"  Recorded artifact_version: {data.get('artifact_version')}")
    print(f"  Recorded prompt_hash     : {data.get('prompt_hash')}")
    print(f"  Recorded tools_hash      : {data.get('tools_hash')}")
    print(f"  Recorded system_prompt   : {data.get('system_prompt')}")
    print(f"  Recorded tools           : {data.get('tools')}")
    
    # Verify hash match
    expected_p_hash = sha256_file(files_to_check[label][0])
    expected_t_hash = sha256_file(files_to_check[label][1])
    p_match = (data.get('prompt_hash') == expected_p_hash)
    t_match = (data.get('tools_hash') == expected_t_hash)
    print(f"  -> Prompt hash khớp file artifacts?: {'CHÍNH XÁC (TRUE)' if p_match else 'KHÔNG KHỚP'}")
    print(f"  -> Tools hash khớp file artifacts? : {'CHÍNH XÁC (TRUE)' if t_match else 'KHÔNG KHỚP'}")
    print()

print("=====================================================================")
print("3. KẾT QUẢ VÀ SỰ KHÁC BIỆT ĐÁNH GIÁ (ACCURACY & FAILURES)")
print("=====================================================================")

for label, rpath in runs:
    with open(rpath, encoding='utf-8') as f:
        data = json.load(f)
    summary = data.get('summary', {})
    print(f"--- Version {label.upper()} ---")
    print(f"  Case Accuracy         : {summary.get('case_accuracy', 0)*100:.1f}% ({summary.get('passed_cases')}/{summary.get('total_cases')})")
    print(f"  Tool Routing Accuracy : {summary.get('tool_routing_accuracy', 0)*100:.1f}%")
    print(f"  Argument Accuracy     : {summary.get('argument_accuracy', 0)*100:.1f}%")
    print(f"  Multiturn Accuracy    : {summary.get('multiturn_accuracy', 0)*100:.1f}%")
    print(f"  Failure counts        : {summary.get('failure_counts')}")
    
    failed_cases = []
    for c in data.get('results', []):
        res = c.get('result', {})
        if not res.get('passed'):
            failed_cases.append({
                'id': c['id'],
                'input': c.get('input'),
                'expect': c.get('expect'),
                'actual': res.get('actual_tool_calls'),
                'failure_type': res.get('failure_type'),
                'mismatches': res.get('mismatches')
            })
    print(f"  Danh sách case FAIL ({len(failed_cases)} cases):")
    for fc in failed_cases:
        print(f"    * {fc['id']} ({fc['failure_type']}):")
        print(f"        Input: {fc['input']}")
        print(f"        Kỳ vọng : {fc['expect']}")
        print(f"        Thực tế : {fc['actual']}")
    print()


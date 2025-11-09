import json, os, sys, glob
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from src.mcp_tool import generate

CASES = [
    '王强压低声音说：“别出声。”',
    '远处传来呼喊：“快躲起来！”',
    '李四大喊：“这边！”',
    '旁白：“他们以为安全。”',
    '张三问：“你看见了吗？”',
    '门外有人喊：“开门！”',
    '王五说道：“安静。”',
    '陈晓低声道：“别动。”',
    '画外音：“夜色深沉。”',
    '电话那头传来声音：“喂？”'
]

def run_inline_cases():
    for i, t in enumerate(CASES, 1):
        res = generate({"text": t})
        assert isinstance(res, dict) and "shots" in res and isinstance(res["shots"], list) and len(res["shots"]) >= 1
        first = res["shots"][0]
        assert "dialogue" in first and "character" in first["dialogue"] and "line" in first["dialogue"]
        print(f"\n=== Inline Case {i} ===\nInput: {t}\nOutput (shots count): {len(res['shots'])}")


def run_file_cases():
    case_dir = os.path.join(os.path.dirname(__file__), "cases")
    files = sorted(glob.glob(os.path.join(case_dir, "case*.md")))
    if not files:
        print("No case files found.")
        return
    for path in files:
        with open(path, "r", encoding="utf-8") as f:
            t = f.read()
        res = generate({"text": t})
        assert isinstance(res, dict) and "shots" in res and isinstance(res["shots"], list) and len(res["shots"]) >= 1
        first = res["shots"][0]
        assert "dialogue" in first and "character" in first["dialogue"] and "line" in first["dialogue"]
        print(f"\n=== File Case {os.path.basename(path)} ===\nOutput (shots count): {len(res['shots'])}")


def main():
    run_inline_cases()
    run_file_cases()

if __name__ == "__main__":
    main()
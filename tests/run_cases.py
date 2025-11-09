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
        # 描述校验：不得与台词完全相同；VO/O.S. 应有规范前缀；普通对话包含景别/机位提示词
        desc = (first.get("description") or "").strip()
        line = (first["dialogue"].get("line") or "").strip()
        tone = (first["dialogue"].get("tone") or "").strip()
        assert desc and desc != line, "description 不应与台词完全相同，需转换重写"
        if tone.startswith("voice-over"):
            assert desc.startswith("旁白（VO）："), "旁白镜头的描述需以 '旁白（VO）：' 开头"
        elif tone.startswith("off-screen"):
            assert "画外音（O.S.）——" in desc, "画外音镜头的描述需包含 '画外音（O.S.）——'"
        else:
            cues = ["近景", "中景", "特写", "全景", "跟拍", "跟随"]
            assert any(c in desc for c in cues), "普通对话镜头描述应包含景别/机位提示词"
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
        # 对首镜头进行描述校验（与内联一致）
        desc = (first.get("description") or "").strip()
        line = (first["dialogue"].get("line") or "").strip()
        tone = (first["dialogue"].get("tone") or "").strip()
        assert desc and desc != line, "description 不应与台词完全相同，需转换重写"
        if tone.startswith("voice-over"):
            assert desc.startswith("旁白（VO）："), "旁白镜头的描述需以 '旁白（VO）：' 开头"
        elif tone.startswith("off-screen"):
            assert "画外音（O.S.）——" in desc, "画外音镜头的描述需包含 '画外音（O.S.）——'"
        else:
            cues = ["近景", "中景", "特写", "全景", "跟拍", "跟随"]
            assert any(c in desc for c in cues), "普通对话镜头描述应包含景别/机位提示词"
        # 纯旁白用例断言：case11 应全部为旁白且 tone 为 voice-over，数量不超过 3
        if os.path.basename(path) == "case11.md":
            shots = res["shots"]
            assert len(shots) <= 3, "旁白镜头数量不应超过 3"
            for s in shots:
                d = s.get("dialogue", {})
                assert d.get("character") == "旁白", "case11 角色应为旁白"
                assert d.get("tone") in ("voice-over", "旁白"), "case11 语气应为 voice-over"
        print(f"\n=== File Case {os.path.basename(path)} ===\nOutput (shots count): {len(res['shots'])}")


def main():
    run_inline_cases()
    run_file_cases()
    # 针对“测试文稿.md”强制旁白模式的专项验证
    story_path = os.path.join(os.path.dirname(__file__), "测试文稿.md")
    if os.path.exists(story_path):
        with open(story_path, "r", encoding="utf-8") as f:
            t = f.read()
        res = generate({"text": t, "narration_limit": 3, "mode": "narration"})
        assert isinstance(res, dict) and "shots" in res and isinstance(res["shots"], list) and len(res["shots"]) >= 1
        shots = res["shots"]
        assert len(shots) <= 3, "测试文稿 旁白镜头数量不应超过 3"
        for s in shots:
            d = s.get("dialogue", {})
            assert d.get("character") == "旁白", "测试文稿 角色应为旁白"
            assert d.get("tone") in ("voice-over", "旁白"), "测试文稿 语气应为 voice-over"
        print(f"\n=== Story Doc 测试文稿.md ===\nOutput (shots count): {len(res['shots'])}")

if __name__ == "__main__":
    main()
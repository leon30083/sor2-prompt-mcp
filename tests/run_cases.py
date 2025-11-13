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

# 构图偏好测试用例：包含多人/群像词汇，验证 mono_or_empty 下输出避免群像措辞
COMPOSITION_CASES = [
    '张三和李四同时喊：“快跑！”',
    '他们围在一起说：“稳住！”',
    '众人齐声道：“准备！”',
    '王强与陈晓对视，说：“别出声。”',
    '两人同时说：“我在这儿！”',
    '一行人中，李四喊：“注意安全！”',
    '大家你一言我一语：“快点！”',
    '三人围在桌边说：“开工！”',
    '同学们起哄：“上！”',
    '他们商量着：“分头行动。”'
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
    # 构图偏好专项：mono_or_empty 避免群像/多人同框词
    for i, t in enumerate(COMPOSITION_CASES, 1):
        res = generate({"text": t, "composition_policy": "mono_or_empty"})
        assert isinstance(res, dict) and "shots" in res and isinstance(res["shots"], list) and len(res["shots"]) >= 1
        first = res["shots"][0]
        desc = (first.get("description") or "").strip()
        cine = (first.get("cinematography") or "").strip()
        # 不应出现群像/多人措辞
        banned = ["两人", "二人", "三人", "众人", "大家", "群像", "合影", "对视"]
        assert not any(b in desc for b in banned), f"composition_policy 应避免群像措辞，当前描述: {desc}"
        assert not any(b in cine for b in ["two-shot", "group" ]), f"composition_policy 应避免两人镜头/群像，当前摄影机: {cine}"
        print(f"\n=== Composition Pref Case {i} ===\nInput: {t}\nDesc: {desc}\nCine: {cine}")

    # Fallback 追加用例：覆盖剪影/背影/天际线三类（其余在现有回归输出中已出现：脚步/手部/空镜）
    extra_cases = [
        ("剪影下，他们齐声喊：“上！”", "silhouette"),
        ("在背影里，众人一起说：“准备！”", "Back view framing"),
        ("天际线之下，他们齐声说：“出发！”", "Skyline"),
    ]
    for i, (t, expect_kw) in enumerate(extra_cases, 1):
        res = generate({"text": t, "composition_policy": "mono_or_empty"})
        assert isinstance(res, dict) and "shots" in res and isinstance(res["shots"], list) and len(res["shots"]) >= 1
        first = res["shots"][0]
        desc = (first.get("description") or "").strip()
        cine = (first.get("cinematography") or "").strip()
        banned = ["两人", "二人", "三人", "众人", "大家", "群像", "合影", "对视"]
        assert not any(b in desc for b in banned), f"extra Fallback 应避免群像措辞，当前描述: {desc}"
        assert not any(b in cine for b in ["two-shot", "group" ]), f"extra Fallback 应避免两人镜头/群像，当前摄影机: {cine}"
        assert expect_kw in cine, f"期望包含关键词 {expect_kw}，当前摄影机: {cine}"
        print(f"\n=== Composition Fallback Extra {i} ===\nInput: {t}\nDesc: {desc}\nCine: {cine}")

    # 相邻镜头差异化专项：对话模式（含两个相似的多人台词）
    t_dialogue = "他们齐声喊：\"上！\"\n他们齐声喊：\"现在！\""
    res = generate({"text": t_dialogue, "composition_policy": "mono_or_empty"})
    assert isinstance(res, dict) and "shots" in res and isinstance(res["shots"], list) and len(res["shots"]) >= 2
    s0, s1 = res["shots"][0], res["shots"][1]
    c0 = (s0.get("cinematography") or "").strip()
    c1 = (s1.get("cinematography") or "").strip()
    assert c0 != c1, f"相邻镜头应在机位/运动上存在差异，当前 c0==c1: {c0}"
    print(f"\n=== Adjacent Diversity (dialogue) ===\nC0: {c0}\nC1: {c1}")

    # 相邻镜头差异化专项：旁白/叙述模式（两句群像描述，无引号）
    t_narr = "他们一起在巷口等待。众人缓慢移动到空地。"
    res2 = generate({"text": t_narr, "composition_policy": "mono_or_empty"})
    assert isinstance(res2, dict) and "shots" in res2 and isinstance(res2["shots"], list) and len(res2["shots"]) >= 2
    s0, s1 = res2["shots"][0], res2["shots"][1]
    c0 = (s0.get("cinematography") or "").strip()
    c1 = (s1.get("cinematography") or "").strip()
    assert c0 != c1, f"相邻镜头应在机位/运动上存在差异（旁白），当前 c0==c1: {c0}"
    print(f"\n=== Adjacent Diversity (narration) ===\nC0: {c0}\nC1: {c1}")
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
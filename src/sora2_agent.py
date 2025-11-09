import re
import json
from typing import List, Dict, Optional, Tuple


def normalize_text(text: str) -> str:
    text = text.replace('"', '“').replace("'", "’")
    text = text.replace('”', '”')
    text = re.sub(r"\s+", " ", text).strip()
    return text


STOPWORDS = {
    "我们", "你这", "古代", "战场", "博物", "博物馆", "馆说", "真的", "体验", "新手", "教程", "差评",
    "碎片", "沉浸", "站票", "瞬间", "反应", "长什么样", "屁股", "电话那头", "门外", "窗外", "揉着", "生疼"
}

# 常见中文姓氏（子集，含示例文本中的姓）
SURNAMES = {
    "赵","钱","孙","李","周","吴","郑","王","冯","陈","蒋","沈","韩","杨","朱","秦","许","何","吕","施","张","孔","曹","严","华","金","魏","陶","姜","谢","邹","喻","柏","水","苏","潘","范","彭","郎","鲁","韦","马","苗","方","任","袁","柳","唐","罗","薛","傅","汤","孟"
}

BAD_SUFFIXES = {"说","道","喊","问","答","传","音","压","看","挠","来","呼"}

# 便于正则类字符集匹配的姓氏集合
SURNAMES_CLASS = "赵钱孙李周吴郑王冯陈蒋沈韩杨朱秦许何吕施张孔曹严华金魏陶姜谢邹喻柏水苏潘范彭郎鲁韦马苗方任袁柳唐罗薛傅汤孟"


def is_likely_person_name(token: str) -> bool:
    if token in STOPWORDS:
        return False
    # 人名多为2-3字
    if not re.fullmatch(r"[\u4e00-\u9fa5]{2,3}", token):
        return False
    # 排除明显动词/非人名尾字
    if token[-1] in BAD_SUFFIXES or token[-1] in {"大","小","老"}:
        return False
    # 以常见姓氏开头更可信；也允许常见称谓作为角色名
    if token[0] not in SURNAMES and token not in {"妈妈","爸爸","老师","记者","警察","医生","客服"}:
        return False
    return True


def find_candidates(text: str) -> List[str]:
    names: List[str] = []
    # 使用前瞻产生重叠窗口，抓取所有2-3字片段
    for m in re.finditer(r"(?=(?P<w>[\u4e00-\u9fa5]{2,3}))", text):
        token = m.group("w")
        if is_likely_person_name(token) and token not in names:
            names.append(token)
    return names

def clip_recent_clause(pre_context: str) -> str:
    """裁剪到最近的子句，防止上一句的O.S.词影响当前判定"""
    seps = [pre_context.rfind(x) for x in ["。","！","？","；"]]
    cut = max(seps)
    return pre_context[cut+1:] if cut != -1 else pre_context


# 常见修饰/动作词，避免被误识为“角色名”
MODIFIER_TOKENS = {
    "压低声音", "低声", "小声", "大喊", "喊", "问", "答", "说道", "说", "道", "哭丧着脸", "抱怨",
    "看向", "看", "挠头", "挠", "揉", "大笑", "微笑", "叹气", "指着", "指向", "望向"
}

def clean_raw_character(raw: str, candidates: List[str]) -> str:
    """移除修饰/动作词，保留最可能的人名片段（2-3字）。"""
    cleaned = raw
    for mod in MODIFIER_TOKENS:
        cleaned = cleaned.replace(mod, "")
    # 同步移除常见非人名尾字在任意位置（如：王强压 -> 王强；远处传 -> 远处）
    for suf in BAD_SUFFIXES:
        cleaned = cleaned.replace(suf, "")
    # 去除常见非人名尾字（如：王强说 -> 王强；李四大 -> 李四）
    if cleaned and cleaned[-1] in BAD_SUFFIXES or (cleaned and cleaned[-1] in {"大","小","老"}):
        cleaned = cleaned[:-1]
    # 优先匹配候选名单
    # 先用原始片段做细化，避免清洗过度丢失姓氏
    refined = refine_name_candidate(raw, candidates)
    if refined:
        if is_likely_person_name(refined):
            return refined
    # 扫描2-3字窗口，优先姓氏开头的候选
    for wlen in (3,2):
        for i in range(0, max(0, len(cleaned) - wlen + 1)):
            sub = cleaned[i:i+wlen]
            if is_likely_person_name(sub):
                return sub
    # 若找不到，截取前2-3字作为退化
    return cleaned[:3] if len(cleaned) >= 3 else cleaned

def refine_name_candidate(raw: str, candidates: List[str]) -> str:
    """对原始捕获的角色片段进行细化：优先返回候选名单或姓氏开头的2-3字窗口"""
    # 直接匹配候选列表
    for wlen in (3,2):
        for i in range(0, max(0, len(raw) - wlen + 1)):
            sub = raw[i:i+wlen]
            if sub in candidates:
                return sub
    # 遍历寻找姓氏开头的片段
    for wlen in (3,2):
        for i in range(0, max(0, len(raw) - wlen + 1)):
            sub = raw[i:i+wlen]
            if is_likely_person_name(sub):
                return sub
    # 回退：使用候选首项或原片段前2-3字
    if candidates:
        return candidates[0]
    return raw[:3] if len(raw) >= 3 else raw


def extract_dialogues(text: str, candidates: List[str]) -> List[Tuple[str, str, str]]:
    results: List[Tuple[str, str, str]] = []

    # 0) 姓氏+名字 在冒号前的情况：王强（修饰）说：“……”
    pattern_surname_colon = re.compile(rf"([{SURNAMES_CLASS}][\u4e00-\u9fa5]{{1,2}})[^“]{{0,30}}?[：:]\s*“([^”]+)”")
    for m in pattern_surname_colon.finditer(text):
        raw_char = m.group(1)
        # 将可能携带的动词/修饰后缀清理为人名
        cleaned = refine_name_candidate(raw_char, candidates)
        line = m.group(2)
        pre = text[max(0, m.start() - 60): m.start()]
        pre = clip_recent_clause(pre)
        context = pre + raw_char
        character = cleaned if is_likely_person_name(cleaned) else (choose_nearest_candidate(pre, candidates) or (candidates[0] if candidates else "不明"))
        if any(line == exist_line for _, exist_line, _ in results):
            continue
        results.append((character, line, context))

    # 1) 角色名后紧跟冒号：妈妈：“……” / 李四（O.S.）：“……”
    pattern_name_colon = re.compile(r"([\u4e00-\u9fa5]{1,6})(?:（(?:旁白|画外|O\.S\.|OS)）)?[：:]\s*“([^”]+)”")
    for m in pattern_name_colon.finditer(text):
        raw_char = m.group(1)
        line = m.group(2)
        # 仅取引号左侧上下文，并裁剪到最近子句，避免上一句污染
        pre = text[max(0, m.start() - 60): m.start()]
        pre = clip_recent_clause(pre)
        context = pre + raw_char
        # 保留特殊角色名（旁白/画外音/解说/叙述者）
        if raw_char in {"旁白","画外音","解说","叙述者","旁白者"}:
            character = raw_char
        else:
            # 1) 直接在原始片段中抓取姓氏开头的2-3字人名
            direct_hits = re.findall(rf"[{SURNAMES_CLASS}][\u4e00-\u9fa5]{{1,2}}", raw_char)
            character = None
            if direct_hits:
                pick = direct_hits[0]
                if is_likely_person_name(pick):
                    character = pick
            # 2) 若未命中，使用清洗后的结果
            if not character:
                cleaned = clean_raw_character(raw_char, candidates)
                if is_likely_person_name(cleaned):
                    character = cleaned
            # 3) 仍未命中，回退：最近候选或根据O.S.线索置为不明
            if not character:
                if any(k in pre for k in ["隔壁","门外","屋外","屏外","远处","外头","另一间","房外","电话那头","传来","怒吼"]):
                    character = "不明"
                else:
                    character = choose_nearest_candidate(pre, candidates) or (candidates[0] if candidates else "不明")
        results.append((character, line, context))

    # 2) 角色名 + 说/道/喊… “台词”
    # 名字(2-3字) + 若干修饰/动词 + 引号台词；支持“怒吼”
    # 以常见姓氏开头的人名（2-3字）+ 修饰/动词 + 引号台词
    pattern_verb = re.compile(rf"(?:(?<=^)|(?<=[\s，。,！？]))([{SURNAMES_CLASS}][\u4e00-\u9fa5]{1,2})(?:（(?:旁白|画外|O\.S\.|OS)）)?[^“]{0,30}?(?:道|说|喊|问|答|低声|压低声音|哭丧着脸|抱怨|怒吼)[，,:：]?\s*“([^”]+)”")
    for m in pattern_verb.finditer(text):
        raw_char = m.group(1)
        line = m.group(2)
        # 仅取引号左侧上下文并裁剪到最近子句
        pre = text[max(0, m.start() - 60): m.start()]
        pre = clip_recent_clause(pre)
        context = pre + raw_char
        # 优先使用左侧最近候选名（更稳定地抓到“王强”、“李四”等）
        nearest = choose_nearest_candidate(context, candidates)
        if nearest:
            character = nearest
        else:
            # 进一步：从左侧最近子句中直接抓取姓氏+名字模式
            surname_hits = re.findall(rf"[{SURNAMES_CLASS}][\u4e00-\u9fa5]{{1,2}}", pre)
            if surname_hits:
                pick = surname_hits[-1]
                character = pick if is_likely_person_name(pick) else raw_char
            else:
                character = raw_char if raw_char in {"旁白","画外音","解说","叙述者","旁白者"} else clean_raw_character(raw_char, candidates)
        # 若不是明显人名且出现屏外线索，视为“未知”以避免误把地点/旁白当人名
        if not is_likely_person_name(character) and any(k in context for k in ["隔壁","门外","屋外","屏外","远处","外头","另一间","房外","电话那头","传来"]):
            character = "不明"
        # 去重：若该台词已记录则跳过
        if any(line == exist_line for _, exist_line, _ in results):
            continue
        results.append((character, line, context))

    # 3) 仅有引号台词：角色未知，回退为候选首项或“不明”
    quoted = re.compile(r"“([^”]+)”")
    for m in quoted.finditer(text):
        line = m.group(1)
        # 仅取引号左侧的上下文，并裁剪到最近子句，确保O.S.词捕获但不跨句
        pre_context = text[max(0, m.start() - 60):m.start()]
        pre_context = clip_recent_clause(pre_context)
        context = pre_context
        if any(line == exist_line for _, exist_line, _ in results):
            continue
        # 从左侧最近的上下文中选择候选名
        surname_hits = re.findall(rf"[{SURNAMES_CLASS}][\u4e00-\u9fa5]{{1,2}}", pre_context)
        if surname_hits:
            pick = surname_hits[-1]
            character = pick if is_likely_person_name(pick) else None
        else:
            character = None
        if not character:
            character = choose_nearest_candidate(pre_context, candidates) or (candidates[0] if candidates else "不明")
        results.append((character, line, context))

    # 统一按台词去重，保留首次出现
    dedup: List[Tuple[str, str, str]] = []
    seen = set()
    for ch, ln, ctx in results:
        k = ln.strip()
        if k in seen:
            continue
        seen.add(k)
        dedup.append((ch, ln, ctx))

    # 依据原文中台词出现顺序排序，保持时间线
    def line_pos(ln: str) -> int:
        quoted = f"“{ln}”"
        idx = text.find(quoted)
        if idx != -1:
            return idx
        return text.find(ln)

    dedup.sort(key=lambda item: line_pos(item[1]))
    return dedup


def guess_tone(context: str, line: str) -> str:
    c = context + " " + line
    # 画面外但在场（Off-Screen）优先，避免被上一句“旁白”误触发
    if is_off_screen(context, None, line):
        if "喊" in c or "！" in line:
            return "off-screen, urgent"
        return "off-screen, audible"
    # 旁白/画外音
    if is_voice_over(context, None, line):
        # 参考：旁白与内心独白通常归为 VO（Voice-over）
        # 资料来源：知乎[电影里的画外音、内心独白和旁白…]、知乎专栏[编剧：V.O.与O.S.]、搜狐文章[详解 V.O./O.S.]
        return "voice-over, reflective"
    mapping = [
        ("压低声音", "rapid, hushed, urgent"),
        ("低声", "hushed, cautious"),
        ("惊恐", "panicked, breathy"),
        ("哭丧着脸", "whining, complaining"),
        ("抱怨", "whining, complaining"),
        ("大喊", "shouting, urgent"),
        ("急", "rapid, urgent"),
        ("紧张", "nervous, fast"),
        ("愤怒", "angry, sharp"),
        ("平静", "calm, steady"),
    ]
    for k, v in mapping:
        if k in c:
            return v
    # 根据标点简易推断
    if "！" in line or "!" in line:
        return "urgent, emphatic"
    return "neutral"


def guess_cinematography(context: str, character: str) -> str:
    c = context
    if is_off_screen(context, character, None):
        # 画面保持主对象，声音来自画外
        return f"Medium shot on in-frame subject; off-screen voice (O.S.) audible"
    if is_voice_over(context, character, None):
        # 旁白常搭配画面蒙太奇/铺垫镜头
        return "B-roll / montage under narration (VO), soft dissolve transitions"
    subject = character if character not in {"不明", "未知", "旁白"} else "in-frame subject"
    if "近景" in c or "特写" in c:
        return f"Medium close-up (MCU) on '{subject}', shallow depth of field"
    if "中景" in c or "跟随" in c or "跟拍" in c:
        return f"Medium shot, tracking '{subject}', handheld motion"
    if "远景" in c or "全景" in c:
        return f"Wide shot, static frame, '{subject}' in context"
    # 缺省：用MCU保证可读性
    return f"Medium close-up (MCU) on '{subject}', shallow depth of field"


def guess_performance(context: str, tone: str) -> str:
    c = context
    if tone.startswith("voice-over"):
        return "Narration: measured, reflective delivery"
    if tone.startswith("off-screen"):
        return "In-frame subject reacts subtly; off-screen voice carries scene"
    if "惊恐" in c:
        return "Eyes widen in sudden realization, face shows panic"
    if "哭丧着脸" in c:
        return "Face shows misery, shoulders slumped, complaining tone"
    if "压低声音" in c or "低声" in c:
        return "Leans in slightly, whispers urgently"
    if "愤怒" in c:
        return "Jaw tight, eyes narrowed, sharp delivery"
    if tone.startswith("urgent"):
        return "Breath hurried, emphatic delivery"
    return "Neutral expression, steady delivery"


def build_description(character: str, line: str, context: str) -> str:
    # 简单中文描述模板
    if is_off_screen(context, character, line):
        return f"画面外声音（O.S.）——{character}：{line}"
    if is_voice_over(context, character, line):
        return f"叠加旁白（画外音）：{line}"
    subject = character if character not in {"不明", "未知"} else "画面主体"
    base = f"近景特写{subject}，他说：{line}"
    if "哭丧着脸" in context:
        base = f"中景跟拍{subject}，他哭丧着脸，抱怨道：{line}"
    if "压低声音" in context or "低声" in context:
        base = f"近景特写{subject}，他压低声音道：{line}"
    return base


def slugify(text: str) -> str:
    text = re.sub(r"[\u4e00-\u9fa5]", "", text)  # 去中文保留英文/符号
    text = re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_")
    return text.lower() or "line"


def generate_sora2_instructions(raw_text: str, default_seconds: str = "4", narration_limit: int = 3) -> List[Dict]:
    text = normalize_text(raw_text)

    # 无对话→旁白 VO 模式：不存在引号或“角色+冒号+引号”结构时，按分句生成旁白镜头
    def has_dialogue_patterns(t: str) -> bool:
        import re
        # 仅当存在明确的台词线索时视为对话：
        # 1) 角色+冒号+引号
        if re.search(r"[\u4e00-\u9fa5]{1,6}[：:]\s*“[^”]+”", t):
            return True
        # 2) 引号内文本长度>=3 且 前文含“说/问/喊/道”等动词线索
        verb_hint = re.compile(r"(说|道|问|喊|叫|答|叹|嘀咕|低声|大喊|高喊|叫道|说道|问道)[：:]?\s*$")
        for m in re.finditer(r"“([^”]+)”", t):
            content = m.group(1)
            if len(content) >= 3:
                pre = t[max(0, m.start() - 20):m.start()]
                if verb_hint.search(pre):
                    return True
                # 或者引号内包含疑问/感叹等语气标点
                if re.search(r"[。！？?!]", content):
                    return True
        return False

    def split_sentences(t: str) -> List[str]:
        import re
        parts = re.split(r"[。！？；…\n]+", t)
        return [p.strip() for p in parts if p and p.strip()]

    if not has_dialogue_patterns(text):
        lines = split_sentences(text)
        try:
            limit = max(1, int(narration_limit))
        except Exception:
            limit = 3
        lines = lines[:limit]
        shots: List[Dict] = []
        for idx, line in enumerate(lines, start=1):
            character = "旁白"
            ctx = line
            tone = "voice-over"
            cine = guess_cinematography(ctx, character)
            perf = guess_performance(ctx, tone)
            desc = build_description(character, line, ctx)
            shot_id = f"shot_{idx:02d}_{slugify(character)}"
            shots.append({
                "shot_id": shot_id,
                "description": desc,
                "api_call": {"seconds": default_seconds},
                "cinematography": cine,
                "performance": perf,
                "dialogue": {
                    "character": character,
                    "line": line,
                    "tone": tone
                }
            })
        return shots

    # 仍为对话模式：按原逻辑抽取台词
    candidates = find_candidates(text)
    dialogues = extract_dialogues(text, candidates)
    shots: List[Dict] = []
    for idx, (character, line, ctx) in enumerate(dialogues, start=1):
        tone = guess_tone(ctx, line)
        cine = guess_cinematography(ctx, character)
        perf = guess_performance(ctx, tone)
        desc = build_description(character, line, ctx)
        shot_id = f"shot_{idx:02d}_{slugify(character)}"
        shots.append({
            "shot_id": shot_id,
            "description": desc,
            "api_call": {"seconds": default_seconds},
            "cinematography": cine,
            "performance": perf,
            "dialogue": {
                "character": (
                    "旁白" if is_voice_over(ctx, character, line) else character
                ),
                "line": line,
                "tone": tone
            }
        })
    return shots


def is_voice_over(context: Optional[str], character: Optional[str], line: Optional[str]) -> bool:
    # 仅在当前行的近邻上下文中判断，避免上一句“旁白”影响当前句
    if character and character in {"旁白", "解说", "叙述者", "旁白者"}:
        return True
    near = (context or "")[-20:]
    keywords = [
        "旁白", "画外音", "解说",
        "V.O", "VO", "(V.O)",
        "（旁白）", "（画外音）",
        "Narration"
    ]
    return any(k in near for k in keywords)


def is_off_screen(context: Optional[str], character: Optional[str], line: Optional[str]) -> bool:
    # 仅在当前句近邻上下文中判断，减少上一句词影响
    near = (context or "")[-48:] + " " + (line or "")
    # 若当前句明确包含角色名且未出现显式O.S.标记，则优先判定为在场
    # 但旁白/解说等叙述者不视为在场角色
    if (
        character
        and character not in {"旁白", "画外音", "解说", "叙述者"}
        and character in near
        and not any(tag in near for tag in ["O.S", "（O.S.）", "（画外）", "屏外"])
    ):
        return False
    keywords = [
        "O.S", "（O.S.）", "（画外）",
        "门外", "电话那头", "屋外", "隔壁",
        "屏外", "远处", "外头", "另一间", "房外",
        "窗外", "楼下", "楼上", "对讲机里", "广播", "扩音器", "扬声器"
    ]
    return any(k in near for k in keywords)


def choose_nearest_candidate(pre_context: str, candidates: List[str]) -> Optional[str]:
    """在引号左侧最近的文本中寻找最接近的候选角色名"""
    # 屏外/远处等线索存在时，避免回填“旁白/画外音”等特殊称谓
    os_cues = ["隔壁","门外","屋外","屏外","远处","外头","另一间","房外","电话那头","传来","怒吼"]
    filtered = [n for n in candidates if n not in {"旁白","画外音","解说","叙述者","旁白者"}] if any(c in pre_context for c in os_cues) else candidates
    idx = -1
    chosen = None
    for name in filtered:
        pos = pre_context.rfind(name)
        if pos > idx:
            idx = pos
            chosen = name
    return chosen


def to_json(shots: List[Dict], ensure_ascii: bool = False) -> str:
    return json.dumps(shots, ensure_ascii=ensure_ascii, indent=2)


def cli():
    import argparse, sys
    parser = argparse.ArgumentParser(description="Sora2 指令生成 CLI")
    parser.add_argument("--text", help="直接传入一段原始文本")
    parser.add_argument("--text_file", help="从文件读取原始文本")
    parser.add_argument("--seconds", help="默认镜头时长（字符串）", default="4")
    args = parser.parse_args()

    if args.text_file:
        try:
            with open(args.text_file, "r", encoding="utf-8") as f:
                sample = f.read()
        except Exception as e:
            print(f"读取文件失败: {e}")
            sys.exit(1)
    elif args.text:
        sample = args.text
    else:
        sample = (
            "汤小团瞬间反应过来，压低声音道，“我们又穿越了！孟虎，你这乌鸦嘴，刚还在博物馆说想看看真的古代战场长什么样！”\n"
            "“我哪知道摸一下锅的碎片，就能买到‘沉浸式体验’的VIP站票啊！” 孟虎哭丧着脸，揉着被硌得生疼的屁股，“这体验也太真实了吧？连个新手教程都没有！差评！”"
        )
    res = generate_sora2_instructions(sample, default_seconds=args.seconds)
    print(to_json(res))


if __name__ == "__main__":
    cli()
from typing import List, Dict

def _normalize_text(s: str) -> str:
    return (s or "").replace("\r\n", "\n").strip()


def split_by_titles(text: str) -> List[Dict]:
    """
    根据以 "###" 开头的标题将文本分段。
    返回 [{"title": str, "content": str}]
    """
    t = _normalize_text(text)
    lines = t.split("\n")
    segments: List[Dict] = []
    cur_title = None
    cur_buf: List[str] = []
    for ln in lines:
        if ln.strip().startswith("###"):
            # 先收束上一个段落
            if cur_title is not None:
                segments.append({"title": cur_title, "content": "\n".join(cur_buf).strip()})
                cur_buf = []
            # 提取标题文本
            cur_title = ln.strip().lstrip("#").strip()
        else:
            cur_buf.append(ln)
    if cur_title is not None:
        segments.append({"title": cur_title, "content": "\n".join(cur_buf).strip()})
    # 过滤空内容
    segments = [s for s in segments if _normalize_text(s.get("content"))]
    return segments


def auto_segment(text: str) -> List[Dict]:
    """
    无标题情况下的简易自动分段：按空行分段，并生成占位标题。
    """
    t = _normalize_text(text)
    parts = [p.strip() for p in t.split("\n\n") if p.strip()]
    segments: List[Dict] = []
    for i, p in enumerate(parts, start=1):
        segments.append({"title": f"片段{i}", "content": p})
    if not segments:
        segments = [{"title": "片段1", "content": t}]
    return segments


def format_script(text: str) -> List[Dict]:
    """统一入口：优先按 ### 标题分段，否则自动分段。"""
    t = _normalize_text(text)
    if "###" in t:
        segs = split_by_titles(t)
        if segs:
            return segs
    return auto_segment(t)


def fit_segment_time(shots: List[Dict], target_seconds: int, strategy: str, default_seconds: int) -> List[Dict]:
    """
    按目标时长对齐每个镜头的 seconds，仅改 api_call.seconds（字符串），不改镜头数量、构图或机位。
    支持策略：
    - scale：按比例缩放各镜头秒数（整数），至少 1s
    - pad：当总时长不足目标时，均匀填充至目标总时长（整数），至少 1s
    - trim：当总时长超出目标时，按比例缩减并不低于 1s；若仍超标，迭代逐镜头 -1 直至达标
    """
    n = max(1, len(shots))
    try:
        tgt = int(target_seconds)
    except Exception:
        tgt = default_seconds * n
    if tgt <= 0:
        tgt = default_seconds * n
    if strategy not in ("scale", "trim", "pad"):
        strategy = "scale"

    # 读取当前每镜头秒数（若不存在，使用 default_seconds）
    cur_secs = []
    for sh in shots:
        api_call = sh.get("api_call", {})
        sec_str = api_call.get("seconds")
        try:
            sec = int(sec_str) if sec_str is not None else int(default_seconds)
        except Exception:
            sec = int(default_seconds)
        cur_secs.append(max(1, sec))

    total = sum(cur_secs)
    # 构造输出镜头，保持其他字段不变
    def build_out(new_secs: List[int]) -> List[Dict]:
        out: List[Dict] = []
        for sh, ns in zip(shots, new_secs):
            sh2 = dict(sh)
            api_call = dict(sh2.get("api_call", {}))
            api_call["seconds"] = str(max(1, int(ns)))
            sh2["api_call"] = api_call
            out.append(sh2)
        return out

    # scale：按比例缩放至目标
    if strategy == "scale":
        if total <= 0:
            per = max(1, round(tgt / n))
            return build_out([per] * n)
        factor = tgt / total
        scaled = [max(1, round(sec * factor)) for sec in cur_secs]
        # 调整四舍五入后的和，确保精确匹配目标
        diff = sum(scaled) - tgt
        if diff == 0:
            return build_out(scaled)
        # 若超出，迭代在 >1 的镜头上减 1；若不足，在镜头上加 1
        i = 0
        while diff != 0 and i < 10000:  # 安全边界，防无限循环
            for idx in range(n):
                if diff > 0 and scaled[idx] > 1:
                    scaled[idx] -= 1
                    diff -= 1
                    if diff == 0:
                        break
                elif diff < 0:
                    scaled[idx] += 1
                    diff += 1
                    if diff == 0:
                        break
            i += 1
        return build_out(scaled)

    # pad：不足则均匀填充
    if strategy == "pad":
        if total >= tgt:
            return build_out(cur_secs)
        delta = tgt - total
        # 均匀分配整数增量
        inc_each = delta // n
        remainder = delta % n
        padded = [sec + inc_each for sec in cur_secs]
        for i in range(remainder):
            padded[i % n] += 1
        return build_out(padded)

    # trim：超出则按比例缩减，并应用最小 1s 限制；若仍超标，迭代减 1
    if strategy == "trim":
        if total <= tgt:
            return build_out(cur_secs)
        factor = tgt / total
        trimmed = [max(1, round(sec * factor)) for sec in cur_secs]
        diff = sum(trimmed) - tgt
        # 若仍超标，按 >1 的镜头迭代减 1，直到精确匹配目标
        i = 0
        while diff > 0 and i < 10000:
            for idx in range(n):
                if trimmed[idx] > 1:
                    trimmed[idx] -= 1
                    diff -= 1
                    if diff == 0:
                        break
            i += 1
        # 若不足（通常由于四舍五入），均匀 +1 填满
        while diff < 0 and i < 10000:
            for idx in range(n):
                trimmed[idx] += 1
                diff += 1
                if diff == 0:
                    break
            i += 1
        return build_out(trimmed)

    # 默认回退
    per = max(1, round(tgt / n))
    return build_out([per] * n)
import sys
import os
import json

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from src.mcp_tool import generate_user_style_per_segment


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_per_segment.py <input_txt>", file=sys.stderr)
        sys.exit(1)
    path = sys.argv[1]
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    payload = {"text": text, "format": True, "segment_seconds": 12, "time_fit_strategy": "scale"}
    out = generate_user_style_per_segment(payload)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

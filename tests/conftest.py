import os
import sys

# 将项目根目录加入 sys.path，确保可以导入 src 包
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
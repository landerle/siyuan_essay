import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import ensure_directories
from modules.database import init_db
from modules.file_scanner import scan_composition_dir
from modules.database import get_stats

print("正在测试...")
ensure_directories()
init_db()
result = scan_composition_dir()
print(f"扫描结果: {result}")
stats = get_stats()
print(f"统计: {stats}")
print("测试完成!")

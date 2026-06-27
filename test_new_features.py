import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import ensure_directories
from modules.database import init_db
from modules.file_scanner import scan_composition_dir

print("测试改进后的功能...")
ensure_directories()
init_db()

print("\n--- 测试扫描新增作文 (rescan=False) ---")
result = scan_composition_dir(rescan=False)
print(f"结果: 导入={result['imported']}, 跳过={result['skipped']}, 失败={len(result['failed'])}")

print("\n--- 测试重新扫描全部 (rescan=True) ---")
result = scan_composition_dir(rescan=True)
print(f"结果: 更新={result['imported']}, 跳过={result['skipped']}, 失败={len(result['failed'])}")

print("\n✅ 功能测试完成！")

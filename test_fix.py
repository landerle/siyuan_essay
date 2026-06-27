import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import ensure_directories
from modules.database import init_db, get_all_compositions
from modules.file_scanner import scan_composition_dir

print("测试修复后的重新扫描功能...")
ensure_directories()
init_db()

print("\n--- 扫描前 ---")
comps = get_all_compositions()
print(f"数据库中有 {len(comps)} 条记录")

print("\n--- 执行重新扫描 ---")
result = scan_composition_dir(rescan=True)
print(f"结果：")
print(f"- 删除记录数：{result.get('deleted', 0)}")
print(f"- 更新/导入记录数：{result['imported']}")
print(f"- 跳过记录数：{result['skipped']}")
print(f"- 失败记录数：{len(result['failed'])}")

print("\n--- 扫描后 ---")
comps = get_all_compositions()
print(f"数据库中有 {len(comps)} 条记录")
for comp in comps:
    print(f"- {comp['file_name']} (文件存在: {os.path.exists(comp['file_path'])})")

print("\n✅ 功能测试完成！")

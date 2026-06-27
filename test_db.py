import sqlite3
import os
from config import DATABASE_PATH, COMPOSITION_DIR

print(f"数据库文件：{DATABASE_PATH}")
print(f"作文目录：{COMPOSITION_DIR}")

conn = sqlite3.connect(DATABASE_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("\n--- 数据库中的作文记录 ---")
cursor.execute("SELECT * FROM compositions")
rows = cursor.fetchall()
for row in rows:
    print(f"ID: {row['id']}, 标题: {row['title']}, 文件: {row['file_name']}, 路径: {row['file_path']}")

print(f"\n总共 {len(rows)} 条记录")

print("\n--- 目录中的实际文件 ---")
files = os.listdir(COMPOSITION_DIR) if os.path.exists(COMPOSITION_DIR) else []
for f in files:
    print(f"- {f}")

conn.close()

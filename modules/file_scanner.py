import os
import shutil
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import COMPOSITION_DIR, SUPPORTED_EXTENSIONS
from modules.file_reader import read_file, extract_title
from modules.analyzer import analyze_composition
from modules.database import add_composition, is_file_imported, get_all_compositions, delete_composition


def archive_file_to_composition_dir(source_path, target_filename=None):
    """将文件归档到 compositions 目录"""
    if not os.path.exists(COMPOSITION_DIR):
        os.makedirs(COMPOSITION_DIR)
    
    # 使用目标文件名（如果提供），否则使用源文件名
    file_name = target_filename if target_filename else os.path.basename(source_path)
    dest_path = os.path.join(COMPOSITION_DIR, file_name)
    
    # 如果目标文件已存在，添加序号
    counter = 1
    name, ext = os.path.splitext(file_name)
    while os.path.exists(dest_path):
        dest_path = os.path.join(COMPOSITION_DIR, f"{name}_{counter}{ext}")
        counter += 1
    
    # 复制文件到归档目录
    shutil.copy2(source_path, dest_path)
    return dest_path


def import_single_file(file_path, archive=True, skip_check=False, original_filename=None):
    if not os.path.exists(file_path):
        return False, "文件不存在", None
    
    content = read_file(file_path)
    if not content.strip():
        return False, "文件内容为空", None
    
    # 如果需要归档，先复制文件
    archived_path = file_path
    if archive and os.path.dirname(os.path.abspath(file_path)) != os.path.abspath(COMPOSITION_DIR):
        archived_path = archive_file_to_composition_dir(file_path, original_filename)
    
    # 检查归档后的路径作为file_path
    final_path = archived_path
    
    if not skip_check and is_file_imported(final_path):
        return False, "文件已导入", final_path
    
    file_name = os.path.basename(final_path)
    title = extract_title(content, file_name)
    analysis = analyze_composition(content)
    
    composition_data = {
        "title": title,
        "file_name": file_name,
        "file_path": final_path,
        "content": content,
        "category": analysis["category"],
        "tags": analysis["tags"],
        "word_count": analysis["word_count"],
        "summary": analysis["summary"]
    }
    
    add_composition(composition_data)
    return True, "导入成功", final_path


def scan_composition_dir(rescan=False):
    if not os.path.exists(COMPOSITION_DIR):
        return {
            "imported": 0,
            "skipped": 0,
            "failed": [{"file": COMPOSITION_DIR, "reason": "目录不存在"}]
        }
    
    deleted_count = 0
    imported = 0
    skipped = 0
    failed = []
    
    # 如果是重新扫描，先清理数据库中不存在的文件记录
    if rescan:
        all_comps = get_all_compositions()
        for comp in all_comps:
            if not os.path.exists(comp['file_path']):
                success, _ = delete_composition(comp['id'])
                if success:
                    deleted_count += 1
    
    # 扫描目录中的文件
    for filename in os.listdir(COMPOSITION_DIR):
        file_path = os.path.join(COMPOSITION_DIR, filename)
        
        if not os.path.isfile(file_path):
            continue
        
        if filename.startswith("~$"):
            skipped += 1
            continue
        
        ext = os.path.splitext(filename)[1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            skipped += 1
            continue
        
        if not rescan and is_file_imported(file_path):
            skipped += 1
            continue
        
        success, reason, final_path = import_single_file(file_path, archive=False, skip_check=rescan)
        if success:
            imported += 1
        else:
            failed.append({"file": filename, "reason": reason})
    
    result = {
        "deleted": deleted_count,
        "imported": imported,
        "skipped": skipped,
        "failed": failed
    }
    
    return result

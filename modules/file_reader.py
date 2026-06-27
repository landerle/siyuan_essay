import os
from docx import Document


def read_txt(file_path):
    encodings = ['utf-8', 'gbk', 'utf-8-sig']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    return ''


def read_docx(file_path):
    try:
        doc = Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return '\n'.join(paragraphs)
    except Exception:
        return ''


def extract_title(content, file_name):
    if not content:
        base_name = os.path.splitext(os.path.basename(file_name))[0]
        return base_name.strip()
    
    lines = content.split('\n')
    first_line = lines[0].strip()
    
    if first_line and len(first_line) <= 30:
        return first_line
    
    base_name = os.path.splitext(os.path.basename(file_name))[0]
    return base_name.strip()


def read_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.txt':
        return read_txt(file_path)
    elif ext == '.docx':
        return read_docx(file_path)
    else:
        return ''

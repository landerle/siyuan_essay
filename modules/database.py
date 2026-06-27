import sqlite3
import json
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATABASE_PATH


def init_db():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS compositions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            file_name TEXT,
            file_path TEXT UNIQUE,
            content TEXT,
            category TEXT,
            tags TEXT,
            word_count INTEGER,
            summary TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS highlights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            composition_id INTEGER,
            type TEXT,
            text TEXT,
            reason TEXT,
            tags TEXT,
            created_at TEXT,
            FOREIGN KEY (composition_id) REFERENCES compositions(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            composition_id INTEGER,
            score INTEGER,
            advantages TEXT,
            problems TEXT,
            suggestions TEXT,
            revised_version TEXT,
            created_at TEXT,
            FOREIGN KEY (composition_id) REFERENCES compositions(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS favorite_sentences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            composition_id INTEGER,
            sentence TEXT,
            source_text TEXT,
            reason TEXT,
            category TEXT,
            tags TEXT,
            created_at TEXT,
            FOREIGN KEY (composition_id) REFERENCES compositions(id)
        )
    ''')
    
    conn.commit()
    conn.close()


def add_composition(data):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    tags_json = json.dumps(data.get('tags', []), ensure_ascii=False)
    
    cursor.execute('''
        INSERT OR REPLACE INTO compositions 
        (title, file_name, file_path, content, category, tags, word_count, summary, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['title'],
        data['file_name'],
        data['file_path'],
        data['content'],
        data['category'],
        tags_json,
        data['word_count'],
        data['summary'],
        now,
        now
    ))
    
    composition_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return composition_id


def update_composition(composition_id, data):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    tags_json = json.dumps(data.get('tags', []), ensure_ascii=False)
    
    cursor.execute('''
        UPDATE compositions 
        SET title=?, content=?, category=?, tags=?, word_count=?, summary=?, updated_at=?
        WHERE id=?
    ''', (
        data.get('title'),
        data.get('content'),
        data.get('category'),
        tags_json,
        data.get('word_count'),
        data.get('summary'),
        now,
        composition_id
    ))
    
    conn.commit()
    conn.close()
    return True


def get_all_compositions():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM compositions ORDER BY created_at DESC')
    rows = cursor.fetchall()
    
    compositions = []
    for row in rows:
        comp = dict(row)
        try:
            comp['tags'] = json.loads(comp['tags'])
        except:
            comp['tags'] = []
        compositions.append(comp)
    
    conn.close()
    return compositions


def get_composition_by_id(composition_id):
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM compositions WHERE id = ?', (composition_id,))
    row = cursor.fetchone()
    
    if row:
        comp = dict(row)
        try:
            comp['tags'] = json.loads(comp['tags'])
        except:
            comp['tags'] = []
        conn.close()
        return comp
    conn.close()
    return None


def is_file_imported(file_path):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM compositions WHERE file_path = ?', (file_path,))
    result = cursor.fetchone()
    
    conn.close()
    return result is not None


def search_compositions(keyword=None, category=None, tag=None):
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = 'SELECT * FROM compositions WHERE 1=1'
    params = []
    
    if keyword:
        query += ' AND (title LIKE ? OR content LIKE ?)'
        params.extend([f'%{keyword}%', f'%{keyword}%'])
    
    if category:
        query += ' AND category = ?'
        params.append(category)
    
    if tag:
        query += ' AND tags LIKE ?'
        params.append(f'%{tag}%')
    
    query += ' ORDER BY created_at DESC'
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    compositions = []
    for row in rows:
        comp = dict(row)
        try:
            comp['tags'] = json.loads(comp['tags'])
        except:
            comp['tags'] = []
        compositions.append(comp)
    
    conn.close()
    return compositions


def get_categories():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT DISTINCT category FROM compositions WHERE category IS NOT NULL ORDER BY category')
    rows = cursor.fetchall()
    
    categories = [row[0] for row in rows]
    conn.close()
    return categories


def get_all_tags():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT tags FROM compositions WHERE tags IS NOT NULL')
    rows = cursor.fetchall()
    
    all_tags = set()
    for row in rows:
        try:
            tags = json.loads(row[0])
            for tag in tags:
                all_tags.add(tag)
        except:
            pass
    
    conn.close()
    return sorted(list(all_tags))


def get_stats():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM compositions')
    total = cursor.fetchone()[0]
    
    cursor.execute('SELECT AVG(word_count) FROM compositions WHERE word_count IS NOT NULL')
    avg_word_count = cursor.fetchone()[0] or 0
    
    cursor.execute('SELECT category, COUNT(*) FROM compositions WHERE category IS NOT NULL GROUP BY category')
    category_stats = cursor.fetchall()
    
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM compositions ORDER BY created_at DESC LIMIT 5')
    recent = cursor.fetchall()
    recent_compositions = []
    for row in recent:
        comp = dict(row)
        try:
            comp['tags'] = json.loads(comp['tags'])
        except:
            comp['tags'] = []
        recent_compositions.append(comp)
    
    conn.close()
    
    return {
        'total': total,
        'avg_word_count': int(avg_word_count),
        'category_stats': dict(category_stats),
        'recent_compositions': recent_compositions
    }


def add_review(composition_id, review_data):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT INTO reviews 
        (composition_id, score, advantages, problems, suggestions, revised_version, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        composition_id,
        review_data.get('score'),
        json.dumps(review_data.get('advantages', []), ensure_ascii=False),
        json.dumps(review_data.get('problems', []), ensure_ascii=False),
        json.dumps(review_data.get('suggestions', []), ensure_ascii=False),
        review_data.get('revised_version'),
        now
    ))
    
    review_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return review_id


def get_reviews_by_composition_id(composition_id):
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM reviews WHERE composition_id = ? ORDER BY created_at DESC', (composition_id,))
    rows = cursor.fetchall()
    
    reviews = []
    for row in rows:
        review = dict(row)
        try:
            review['advantages'] = json.loads(review['advantages']) if review['advantages'] else []
            review['problems'] = json.loads(review['problems']) if review['problems'] else []
            review['suggestions'] = json.loads(review['suggestions']) if review['suggestions'] else []
        except:
            review['advantages'] = []
            review['problems'] = []
            review['suggestions'] = []
        reviews.append(review)
    
    conn.close()
    return reviews


def add_highlight(composition_id, highlight_data):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT INTO highlights 
        (composition_id, type, text, reason, tags, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        composition_id,
        highlight_data.get('type'),
        highlight_data.get('text'),
        highlight_data.get('reason'),
        json.dumps(highlight_data.get('tags', []), ensure_ascii=False),
        now
    ))
    
    highlight_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return highlight_id


def get_highlights_by_composition_id(composition_id):
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM highlights WHERE composition_id = ? ORDER BY created_at DESC', (composition_id,))
    rows = cursor.fetchall()
    
    highlights = []
    for row in rows:
        highlight = dict(row)
        try:
            highlight['tags'] = json.loads(highlight['tags']) if highlight['tags'] else []
        except:
            highlight['tags'] = []
        highlights.append(highlight)
    
    conn.close()
    return highlights


def get_all_highlights(tag=None, type=None):
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = '''
        SELECT h.*, c.title as composition_title 
        FROM highlights h 
        LEFT JOIN compositions c ON h.composition_id = c.id 
        WHERE 1=1
    '''
    params = []
    
    if type:
        query += ' AND h.type = ?'
        params.append(type)
    
    if tag:
        query += ' AND h.tags LIKE ?'
        params.append(f'%{tag}%')
    
    query += ' ORDER BY h.created_at DESC'
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    highlights = []
    for row in rows:
        highlight = dict(row)
        try:
            highlight['tags'] = json.loads(highlight['tags']) if highlight['tags'] else []
        except:
            highlight['tags'] = []
        highlights.append(highlight)
    
    conn.close()
    return highlights


def delete_composition(composition_id):
    """删除作文记录（同时关联删除 reviews 和 highlights）"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # 获取文件路径以便后续删除文件
        cursor.execute('SELECT file_path FROM compositions WHERE id = ?', (composition_id,))
        result = cursor.fetchone()
        file_path = result[0] if result else None
        
        # 删除关联的记录
        cursor.execute('DELETE FROM highlights WHERE composition_id = ?', (composition_id,))
        cursor.execute('DELETE FROM reviews WHERE composition_id = ?', (composition_id,))
        
        # 删除作文记录
        cursor.execute('DELETE FROM compositions WHERE id = ?', (composition_id,))
        
        conn.commit()
        return True, file_path
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()


def add_favorite_sentence(composition_id, sentence_data):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    tags_json = json.dumps(sentence_data.get('tags', []), ensure_ascii=False)
    
    cursor.execute('''
        INSERT INTO favorite_sentences 
        (composition_id, sentence, source_text, reason, category, tags, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        composition_id,
        sentence_data.get('sentence'),
        sentence_data.get('source_text'),
        sentence_data.get('reason'),
        sentence_data.get('category'),
        tags_json,
        now
    ))
    
    favorite_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return favorite_id


def get_favorite_sentences(tag=None, category=None):
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = '''
        SELECT f.*, c.title as composition_title 
        FROM favorite_sentences f 
        LEFT JOIN compositions c ON f.composition_id = c.id 
        WHERE 1=1
    '''
    params = []
    
    if category:
        query += ' AND f.category = ?'
        params.append(category)
    
    if tag:
        query += ' AND f.tags LIKE ?'
        params.append(f'%{tag}%')
    
    query += ' ORDER BY f.created_at DESC'
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    favorites = []
    for row in rows:
        favorite = dict(row)
        try:
            favorite['tags'] = json.loads(favorite['tags']) if favorite['tags'] else []
        except:
            favorite['tags'] = []
        favorites.append(favorite)
    
    conn.close()
    return favorites


def get_favorite_sentences_by_composition_id(composition_id):
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM favorite_sentences WHERE composition_id = ? ORDER BY created_at DESC', (composition_id,))
    rows = cursor.fetchall()
    
    favorites = []
    for row in rows:
        favorite = dict(row)
        try:
            favorite['tags'] = json.loads(favorite['tags']) if favorite['tags'] else []
        except:
            favorite['tags'] = []
        favorites.append(favorite)
    
    conn.close()
    return favorites


def delete_favorite_sentence(favorite_id):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('DELETE FROM favorite_sentences WHERE id = ?', (favorite_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        return False
    finally:
        conn.close()


def get_favorite_sentence_categories():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT DISTINCT category FROM favorite_sentences WHERE category IS NOT NULL ORDER BY category')
    rows = cursor.fetchall()
    
    categories = [row[0] for row in rows]
    conn.close()
    return categories


def get_favorite_sentence_tags():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT tags FROM favorite_sentences WHERE tags IS NOT NULL')
    rows = cursor.fetchall()
    
    all_tags = set()
    for row in rows:
        try:
            tags = json.loads(row[0])
            for tag in tags:
                all_tags.add(tag)
        except:
            pass
    
    conn.close()
    return sorted(list(all_tags))


def get_favorite_sentence_stats():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM favorite_sentences')
    total = cursor.fetchone()[0]
    
    cursor.execute('SELECT category, COUNT(*) FROM favorite_sentences WHERE category IS NOT NULL GROUP BY category')
    category_stats = cursor.fetchall()
    
    conn.close()
    
    return {
        'total': total,
        'category_stats': dict(category_stats)
    }

import re

CATEGORIES = [
    "成长感悟类",
    "亲情类",
    "友情类",
    "校园生活类",
    "写人记事类",
    "自然风景类",
    "传统文化类",
    "读后感类",
    "议论文类",
    "想象作文类",
    "其他"
]

CATEGORY_KEYWORDS = {
    "成长感悟类": ["成长", "长大", "挫折", "坚持", "失败", "成功", "勇气", "改变", "收获", "明白", "懂得"],
    "亲情类": ["妈妈", "母亲", "爸爸", "父亲", "爷爷", "奶奶", "外婆", "外公", "家", "亲情", "陪伴", "温暖"],
    "友情类": ["朋友", "同桌", "伙伴", "友谊", "帮助", "误会", "和好", "陪伴"],
    "校园生活类": ["校园", "老师", "同学", "课堂", "考试", "运动会", "班级", "课间", "操场"],
    "写人记事类": ["那一次", "记得", "难忘", "经历", "事情", "人物", "背影", "眼神"],
    "自然风景类": ["春天", "夏天", "秋天", "冬天", "风", "雨", "花", "树", "山", "河", "天空", "夕阳", "月亮"],
    "传统文化类": ["春节", "中秋", "端午", "传统", "文化", "习俗", "汉字", "诗词", "节日"],
    "读后感类": ["读后感", "这本书", "作者", "主人公", "故事告诉我", "读完", "感受"],
    "议论文类": ["我认为", "观点", "首先", "其次", "因此", "所以", "论证", "道理", "应该"],
    "想象作文类": ["假如", "未来", "梦见", "穿越", "机器人", "魔法", "星球", "时光机"]
}

TAG_KEYWORDS = {
    "成长": ["成长", "长大", "改变", "收获", "懂得"],
    "挫折": ["失败", "困难", "挫折", "低落", "沮丧"],
    "坚持": ["坚持", "努力", "不放弃", "继续"],
    "梦想": ["梦想", "理想", "目标", "未来"],
    "亲情": ["妈妈", "爸爸", "父母", "家", "亲情"],
    "母爱": ["妈妈", "母亲", "母爱"],
    "父爱": ["爸爸", "父亲", "父爱"],
    "友情": ["朋友", "同桌", "友谊", "伙伴"],
    "校园": ["校园", "老师", "同学", "课堂", "班级"],
    "考试": ["考试", "试卷", "成绩", "分数"],
    "老师": ["老师", "班主任", "语文老师"],
    "自然": ["春天", "夏天", "秋天", "冬天", "花", "草", "树", "山", "河"],
    "传统文化": ["春节", "中秋", "端午", "传统", "文化", "习俗"],
    "读书": ["书", "阅读", "读后感", "主人公"],
    "心理描写": ["心想", "心里", "紧张", "害怕", "激动", "后悔", "忐忑"],
    "动作描写": ["跑", "走", "拿", "抬头", "低头", "握住", "推开"],
    "环境描写": ["阳光", "微风", "天空", "树叶", "花香", "雨滴", "夕阳"],
    "语言生动": ["像", "仿佛", "好似", "宛如", "犹如"],
    "结尾升华": ["我明白了", "我懂得了", "从那以后", "那一刻"]
}

PUNCTUATION = "，。！？、；：\"\"''（）《》【】……——,.!?;:'\"()[] "


def count_words(content):
    if not content:
        return 0
    cleaned = content
    for p in PUNCTUATION:
        cleaned = cleaned.replace(p, '')
    cleaned = cleaned.replace('\n', '').replace('\t', '').replace(' ', '')
    return len(cleaned)


def classify_composition(content):
    if not content:
        return "其他"
    
    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            score += content.count(keyword)
        scores[category] = score
    
    max_score = max(scores.values())
    if max_score == 0:
        return "其他"
    
    for category, score in scores.items():
        if score == max_score:
            return category
    
    return "其他"


def generate_tags(content):
    if not content:
        return ["未分类"]
    
    tags = []
    for tag, keywords in TAG_KEYWORDS.items():
        for keyword in keywords:
            if keyword in content:
                tags.append(tag)
                break
    
    tags = list(set(tags))
    tags = tags[:8]
    
    if not tags:
        tags = ["未分类"]
    
    return tags


def generate_summary(content, max_length=100):
    if not content:
        return ""
    
    cleaned = content.replace('\n', ' ').replace('\t', ' ')
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    if len(cleaned) <= max_length:
        return cleaned
    
    return cleaned[:max_length] + "……"


def analyze_composition(content):
    category = classify_composition(content)
    tags = generate_tags(content)
    word_count = count_words(content)
    summary = generate_summary(content)
    
    return {
        "category": category,
        "tags": tags,
        "word_count": word_count,
        "summary": summary
    }

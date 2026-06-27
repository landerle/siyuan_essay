"""
AI 作文分析客户端
需要配置 API key 才能使用
"""
import os
import json

# 每次调用时动态检测，而不是仅在加载时检测
def check_llm_available():
    try:
        from openai import OpenAI
        return True, None
    except ImportError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)

# 默认配置
DEFAULT_BASE_URL = "https://api.deepseek.com/v1"  # DeepSeek 接口示例
DEFAULT_MODEL = "deepseek-chat"


def load_config():
    """加载配置"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载配置失败: {e}")
    return {}


def save_config(config):
    """保存配置"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存配置失败: {e}")


def get_llm_client():
    """获取 LLM 客户端"""
    available, error = check_llm_available()
    if not available:
        return None, f"OpenAI 库未安装: {error}"
    
    config = load_config()
    api_key = config.get("api_key", "")
    base_url = config.get("base_url", DEFAULT_BASE_URL)
    
    if not api_key:
        return None, "未配置 API Key"
    
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        return client, None
    except Exception as e:
        return None, f"创建客户端失败: {e}"


def test_connection():
    """测试连接"""
    client, error = get_llm_client()
    if error:
        return False, error
    
    try:
        # 发送一个简单的测试请求
        model = load_config().get("model", DEFAULT_MODEL)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "你好"}],
            max_tokens=10
        )
        return True, "✅ 连接成功！"
    except Exception as e:
        return False, f"❌ 连接失败: {str(e)}"


def ai_analyze_composition(content):
    """使用 AI 分析作文"""
    client, error = get_llm_client()
    if error:
        return {
            "success": False,
            "reason": error
        }
    
    try:
        model = load_config().get("model", DEFAULT_MODEL)
        
        prompt = f"""你是一位初中高级语文老师，请以批改学生作文的方式对以下作文进行分析。

请严格按照以下 JSON 格式输出，不要包含任何其他内容：
{{
    "category": "作文分类（亲情类/成长感悟类/校园生活类/其他）",
    "strengths": ["优点1", "优点2", "优点3"],
    "improvements": ["改进点1（要具体，指出具体哪里可以改进）", "改进点2（要具体，指出具体哪里可以改进）", "改进点3（要具体，指出具体哪里可以改进）", "改进点4（要具体，指出具体哪里可以改进）", "改进点5（要具体，指出具体哪里可以改进）"],
    "highlight_sentences": ["优秀句子1", "优秀句子2", "优秀句子3"]
}}

要求：
1. strengths 必须输出 3 个优点
2. improvements 必须输出 5 个具体改进点，要结合作文内容指出具体哪里可以改进
3. highlight_sentences 必须输出 3 个优秀句子

作文内容：
{content}
"""

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一位初中高级语文老师，你在帮学生批改作文，让学生的作文更加优秀。请严格按 JSON 格式输出。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=3000
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # 尝试解析 JSON
        try:
            result = json.loads(result_text)
            return {
                "success": True,
                "data": result
            }
        except:
            return {
                "success": True,
                "data": {"raw_response": result_text}
            }
            
    except Exception as e:
        return {
            "success": False,
            "reason": f"调用AI失败：{str(e)}"
        }


def ai_rewrite_sentence(sentence):
    """使用 AI 润色句子"""
    client, error = get_llm_client()
    if error:
        return {"success": False, "reason": error}
    
    try:
        model = load_config().get("model", DEFAULT_MODEL)
        
        prompt = f"请将以下句子润色得更优美：{sentence}"
        
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8
        )
        
        return {
            "success": True,
            "data": response.choices[0].message.content
        }
    except Exception as e:
        return {"success": False, "reason": str(e)}


ANALYSIS_MARKER_START = "\n\n--- AI 作文分析 ---\n\n"
ANALYSIS_MARKER_END = "\n--- 分析完成 ---"


def format_analysis_result(data):
    """将 AI 分析结果格式化为可读文本"""
    lines = [ANALYSIS_MARKER_START.strip()]
    
    if 'strengths' in data and data['strengths']:
        lines.append("### ✨ 优点")
        for s in data['strengths']:
            lines.append(f"- {s}")
        lines.append("")
    
    if 'improvements' in data and data['improvements']:
        lines.append("### 💭 改进建议")
        for w in data['improvements']:
            lines.append(f"- {w}")
        lines.append("")
    
    if 'highlight_sentences' in data and data['highlight_sentences']:
        lines.append("### 🌟 优秀句子")
        for h in data['highlight_sentences']:
            lines.append(f"- {h}")
        lines.append("")
    
    if 'raw_response' in data:
        lines.append("### 📋 分析结果")
        lines.append(data['raw_response'])
        lines.append("")
    
    lines.append(ANALYSIS_MARKER_END.strip())
    return "\n".join(lines) + "\n"


def has_analysis(content):
    """检查作文内容是否已包含 AI 分析"""
    return ANALYSIS_MARKER_START.strip() in content


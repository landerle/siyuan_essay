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
        
        prompt = f"""请分析以下作文，返回JSON格式：
{{
    "category": "作文分类（亲情类/成长感悟类/校园生活类/其他）",
    "strengths": ["优点1", "优点2", "优点3"],
    "weaknesses": ["缺点1", "缺点2"],
    "suggestions": ["改进建议1", "改进建议2"],
    "highlight_sentences": ["优秀句子1", "优秀句子2"]
}}

作文内容：
{content}
"""

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个专业的作文老师，擅长分析作文。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
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


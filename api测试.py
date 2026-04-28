import requests

# 填入你的智谱 API Key
API_KEY = "f95ee93c19db4b9c935d2815211ef146.8yjbjcS2vM6auXbR"
# 官方指定依赖：pip install zhipuai==2.1.5.20250726
import re
from zhipuai import ZhipuAI

# ========== 官方规范配置 ==========

MODEL_NAME = "glm-4.7-flash"

# 严格约束提示词（杜绝思考/解释）
CUT_PROMPT = """
仅执行文本分词，禁止分析、禁止解释、禁止思考过程。
规则：
1.词语单元≤5个字符
2.仅空格分隔
3.剔除所有标点/符号/括号
4.只输出分词结果，无额外文字

文本：
"""

def test_glm_cut():
    try:
        # 官方标准初始化
        client = ZhipuAI(api_key=API_KEY)

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "user", "content": CUT_PROMPT + "雪花秀顺行洁面水乳三件套装"}
            ],
            # 官方规范：关闭思考模式
            thinking={
        "type": "enabled",    # 启用深度思考模式
    },
            temperature=0.0,
            max_tokens=65536,
            stream=False,
            timeout=30  # 修复国内网络超时
        )

        # 规范取值：只取content，忽略推理字段
        content = response.choices[0].message.content.strip()
        print("✅ 模型返回分词结果：", content)

        # 清洗 + 拆分（和你原有逻辑一致）
        clean = re.sub(r'[^\w\s]', ' ', content).lower()
        word_list = [w for w in clean.split() if w]
        print("✅ 最终拆分列表：", word_list)

    except Exception as e:
        print("❌ 调用异常：", str(e))

if __name__ == "__main__":
    test_glm_cut()
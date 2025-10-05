"""
硅基流动API连接测试脚本
用于诊断连接问题
"""

import requests
import json

def test_siliconflow_api(api_key):
    """测试硅基流动API连接"""
    url = "https://api.siliconflow.cn/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "Qwen/Qwen2.5-72B-Instruct",
        "messages": [
            {
                "role": "user",
                "content": "请回复'连接测试成功'"
            }
        ],
        "max_tokens": 10,
        "temperature": 0.7
    }

    print("🔍 测试硅基流动API连接...")
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    print(f"Data: {json.dumps(data, indent=2)}")
    print("-" * 50)

    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)

        print(f"📡 响应状态码: {response.status_code}")
        print(f"📋 响应头: {dict(response.headers)}")

        if response.status_code == 200:
            result = response.json()
            print("✅ 连接成功!")
            print(f"🤖 AI回复: {result['choices'][0]['message']['content']}")
            return True
        else:
            print("❌ 连接失败!")
            print(f"📄 错误响应: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ 网络请求异常: {e}")
        return False

def check_api_key_format(api_key):
    """检查API密钥格式"""
    print(f"🔑 检查API密钥格式...")

    if not api_key:
        print("❌ API密钥为空")
        return False

    if len(api_key) < 10:
        print("❌ API密钥太短，可能不完整")
        return False

    # 检查是否包含常见的前缀
    if api_key.startswith('sk-'):
        print("✅ API密钥格式正确 (OpenAI格式)")
    elif api_key.startswith('sf-'):
        print("✅ API密钥格式正确 (SiliconFlow格式)")
    else:
        print("⚠️ API密钥格式未知，但可能仍然有效")

    # 隐藏部分密钥用于显示
    masked_key = api_key[:6] + '*' * (len(api_key) - 10) + api_key[-4:]
    print(f"🔐 API密钥: {masked_key}")

    return True

if __name__ == "__main__":
    print("🧪 硅基流动API连接诊断工具")
    print("=" * 50)

    # 请在此处输入你的API密钥
    api_key = input("请输入你的硅基流动API密钥: ").strip()

    if not api_key:
        print("❌ 未输入API密钥")
        exit(1)

    # 检查API密钥格式
    if not check_api_key_format(api_key):
        exit(1)

    print()

    # 测试连接
    success = test_siliconflow_api(api_key)

    print()
    print("=" * 50)
    if success:
        print("🎉 硅基流动API连接测试通过！")
    else:
        print("💡 故障排除建议:")
        print("1. 检查API密钥是否正确复制")
        print("2. 确认API密钥是否有效且未过期")
        print("3. 检查网络连接是否正常")
        print("4. 确认硅基流动账户是否有足够余额")
        print("5. 尝试使用其他API提供商测试")
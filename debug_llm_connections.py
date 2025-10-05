"""
LLM API 连接调试工具
用于诊断所有提供商的连接问题
"""

import requests
import json

def test_siliconflow(api_key):
    """测试硅基流动"""
    url = "https://api.siliconflow.cn/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "Qwen/Qwen2.5-72B-Instruct",
        "messages": [{"role": "user", "content": "测试"}],
        "max_tokens": 5
    }
    return make_request("硅基流动", url, headers, data)

def test_deepseek(api_key):
    """测试DeepSeek"""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": "测试"}],
        "max_tokens": 5
    }
    return make_request("DeepSeek", url, headers, data)

def test_modelscope(api_key):
    """测试魔搭社区"""
    url = "https://api.modelscope.cn/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "Qwen/Qwen2.5-72B-Instruct",
        "messages": [{"role": "user", "content": "测试"}],
        "max_tokens": 5
    }
    return make_request("魔搭社区", url, headers, data)

def test_openrouter(api_key):
    """测试OpenRouter"""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "anthropic/claude-3.5-sonnet",
        "messages": [{"role": "user", "content": "测试"}],
        "max_tokens": 5
    }
    return make_request("OpenRouter", url, headers, data)

def make_request(provider_name, url, headers, data):
    """发送请求并返回结果"""
    print(f"\n🧪 测试 {provider_name}...")
    print(f"URL: {url}")

    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"✅ {provider_name} 连接成功!")
            return True
        else:
            print(f"❌ {provider_name} 连接失败!")
            print(f"错误信息: {response.text[:200]}")
            return False

    except requests.exceptions.Timeout:
        print(f"⏰ {provider_name} 请求超时!")
        return False
    except requests.exceptions.ConnectionError:
        print(f"🌐 {provider_name} 连接错误!")
        return False
    except Exception as e:
        print(f"❌ {provider_name} 未知错误: {e}")
        return False

def main():
    print("🔧 LLM API 连接调试工具")
    print("=" * 50)

    # 收集API密钥
    api_keys = {}

    print("\n请输入API密钥 (留空跳过测试):")

    siliconflow_key = input("硅基流动 API密钥: ").strip()
    if siliconflow_key:
        api_keys['siliconflow'] = siliconflow_key

    deepseek_key = input("DeepSeek API密钥: ").strip()
    if deepseek_key:
        api_keys['deepseek'] = deepseek_key

    modelscope_key = input("魔搭社区 API密钥: ").strip()
    if modelscope_key:
        api_keys['modelscope'] = modelscope_key

    openrouter_key = input("OpenRouter API密钥: ").strip()
    if openrouter_key:
        api_keys['openrouter'] = openrouter_key

    if not api_keys:
        print("❌ 没有输入任何API密钥")
        return

    print("\n" + "=" * 50)
    print("🚀 开始连接测试...")
    print("=" * 50)

    results = {}

    # 测试各个提供商
    if 'siliconflow' in api_keys:
        results['siliconflow'] = test_siliconflow(api_keys['siliconflow'])

    if 'deepseek' in api_keys:
        results['deepseek'] = test_deepseek(api_keys['deepseek'])

    if 'modelscope' in api_keys:
        results['modelscope'] = test_modelscope(api_keys['modelscope'])

    if 'openrouter' in api_keys:
        results['openrouter'] = test_openrouter(api_keys['openrouter'])

    # 输出总结
    print("\n" + "=" * 50)
    print("📊 测试结果总结:")
    print("=" * 50)

    for provider, success in results.items():
        status = "✅ 成功" if success else "❌ 失败"
        print(f"{provider}: {status}")

    # 提供建议
    print("\n💡 建议:")
    successful_providers = [k for k, v in results.items() if v]

    if successful_providers:
        print(f"✅ 以下服务商可用: {', '.join(successful_providers)}")
        print("🎯 建议在应用中使用这些可用的服务商")

    failed_providers = [k for k, v in results.items() if not v]

    if failed_providers:
        print(f"❌ 以下服务商不可用: {', '.join(failed_providers)}")
        print("🔧 请检查这些服务商的:")
        print("   - API密钥是否正确")
        print("   - 账户是否有效")
        print("   - 网络连接是否正常")
        print("   - 账户余额是否充足")

if __name__ == "__main__":
    main()
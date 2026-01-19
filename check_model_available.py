#!/usr/bin/env python3
"""
验证指定的模型是否在 API 中可用
Usage: python check_model_available.py <IP_ADDRESS> <PORT> <MODEL_NAME>
"""
import sys
import json
import urllib.request
import urllib.error
from urllib.parse import urljoin

def check_model_available(ip_address, port, model_name):
    """
    检查指定的模型是否在 API 的模型列表中
    
    Args:
        ip_address: API 服务器 IP 地址
        port: API 服务器端口
        model_name: 要检查的模型名称
    
    Returns:
        bool: 如果模型可用返回 True，否则返回 False
    """
    base_url = f"http://{ip_address}:{port}"
    models_url = urljoin(base_url, "/v1/models")
    
    try:
        print(f"正在检查模型 API: {models_url}")
        print(f"查找模型: {model_name}")
        
        # 发送请求，设置超时
        req = urllib.request.Request(models_url)
        with urllib.request.urlopen(req, timeout=10) as response:
            # 检查 HTTP 状态码
            if response.status != 200:
                print(f"错误: API 返回 HTTP 状态码 {response.status}")
                return False
            
            # 读取并解析响应
            response_data = response.read().decode('utf-8')
            data = json.loads(response_data)
        
        # 检查响应格式
        if "data" not in data:
            print(f"错误: API 响应格式不正确，缺少 'data' 字段")
            print(f"响应内容: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return False
        
        models = data["data"]
        if not isinstance(models, list):
            print(f"错误: API 响应格式不正确，'data' 字段不是列表")
            print(f"响应内容: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return False
        
        # 获取所有可用的模型 ID
        available_models = []
        for model in models:
            if isinstance(model, dict) and "id" in model:
                available_models.append(model["id"])
            elif isinstance(model, str):
                available_models.append(model)
        
        print(f"\n可用的模型列表 ({len(available_models)} 个):")
        for i, model_id in enumerate(available_models, 1):
            marker = " ✓" if model_id == model_name else ""
            print(f"  {i}. {model_id}{marker}")
        
        # 检查模型是否存在
        if model_name in available_models:
            print(f"\n✓ 模型 '{model_name}' 在 API 中可用")
            return True
        else:
            print(f"\n✗ 错误: 模型 '{model_name}' 不在 API 的可用模型列表中")
            print(f"请检查模型名称是否正确，或者确认该模型已加载到 API 服务中")
            return False
            
    except urllib.error.URLError as e:
        if isinstance(e.reason, TimeoutError) or "timed out" in str(e).lower():
            print(f"错误: 连接 API 超时 ({models_url})")
        else:
            print(f"错误: 无法连接到 API ({models_url})")
            print(f"详细信息: {e}")
        return False
    except urllib.error.HTTPError as e:
        print(f"错误: API 返回 HTTP 错误")
        print(f"状态码: {e.code}")
        try:
            error_body = e.read().decode('utf-8')
            print(f"响应内容: {error_body}")
        except:
            pass
        return False
    except json.JSONDecodeError as e:
        print(f"错误: API 响应不是有效的 JSON 格式")
        print(f"详细信息: {e}")
        return False
    except Exception as e:
        print(f"错误: 检查模型时发生未知错误")
        print(f"错误类型: {type(e).__name__}")
        print(f"详细信息: {e}")
        return False

def main():
    if len(sys.argv) != 4:
        print("Usage: python check_model_available.py <IP_ADDRESS> <PORT> <MODEL_NAME>")
        sys.exit(1)
    
    ip_address = sys.argv[1]
    port = sys.argv[2]
    model_name = sys.argv[3]
    
    if check_model_available(ip_address, port, model_name):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()

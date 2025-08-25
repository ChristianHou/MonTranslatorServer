#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断文件上传阻塞问题
"""

import os
import time
import requests
import json

def check_server_status():
    """检查服务器状态"""
    print("🔍 检查服务器状态...")
    
    try:
        response = requests.get('http://127.0.0.1:8000/', timeout=5)
        if response.status_code == 200:
            print("✅ 服务器正常运行")
            return True
        else:
            print(f"❌ 服务器响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到服务器: {e}")
        return False

def test_simple_upload():
    """测试简单文件上传"""
    print("\n🧪 测试简单文件上传...")
    
    # 创建测试文件
    test_content = "这是一个测试文件。" * 100
    test_file = "test_upload.txt"
    
    try:
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        print(f"📄 创建测试文件: {test_file}")
        print(f"📊 文件大小: {len(test_content)} 字符")
        
        # 测试上传
        with open(test_file, 'rb') as f:
            files = {'files': (test_file, f, 'text/plain')}
            
            print("📤 开始上传...")
            start_time = time.time()
            
            response = requests.post('http://127.0.0.1:8000/uploadfiles', 
                                   files=files, timeout=30)
            
            upload_time = time.time() - start_time
            print(f"⏱️ 上传耗时: {upload_time:.2f}秒")
        
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 文件上传成功！")
            print(f"📊 响应数据: {data}")
            return data.get('client_id')
        else:
            print(f"❌ 文件上传失败: {response.status_code}")
            print(f"📄 响应内容: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print("❌ 文件上传超时（30秒）")
        return None
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return None

def test_translation_task(client_id):
    """测试翻译任务提交"""
    if not client_id:
        print("❌ 无法测试翻译任务，缺少client_id")
        return False
    
    print(f"\n🧪 测试翻译任务提交...")
    
    try:
        task_data = {
            "client_ip": client_id,
            "source_lang": "zh_Hans",
            "target_lang": "khk_Cyrl",
            "via_eng": False
        }
        
        print(f"📤 提交任务数据: {json.dumps(task_data, ensure_ascii=False)}")
        
        start_time = time.time()
        response = requests.post('http://127.0.0.1:8000/translate/files',
                               json=task_data, timeout=30)
        task_time = time.time() - start_time
        
        print(f"⏱️ 任务提交耗时: {task_time:.2f}秒")
        print(f"📊 响应状态: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 翻译任务提交成功")
            print(f"📊 任务ID: {data.get('task_id', 'N/A')}")
            return True
        else:
            print(f"❌ 翻译任务提交失败: {response.status_code}")
            print(f"📄 响应内容: {response.text}")
            return False
        
    except requests.exceptions.Timeout:
        print("❌ 翻译任务提交超时（30秒）")
        return False
    except Exception as e:
        print(f"❌ 测试翻译任务失败: {e}")
        return False

def check_browser_console():
    """检查浏览器控制台问题"""
    print("\n🔍 检查浏览器控制台问题...")
    
    print("💡 请按以下步骤检查:")
    print("1. 在浏览器中按 F12 打开开发者工具")
    print("2. 切换到 Console 标签页")
    print("3. 刷新页面，查看是否有错误信息")
    print("4. 尝试上传文件，观察控制台输出")
    print("5. 检查 Network 标签页中的网络请求")
    
    print("\n🔧 常见问题及解决方案:")
    print("- JavaScript语法错误: 检查translator.js文件")
    print("- 网络请求失败: 检查服务器状态和端点")
    print("- CORS错误: 检查服务器CORS配置")
    print("- 文件大小限制: 检查配置文件中的MAX_FILE_SIZE")

def check_file_permissions():
    """检查文件权限"""
    print("\n🔍 检查文件权限...")
    
    directories = [
        "files/upload",
        "files/download",
        "logs"
    ]
    
    for directory in directories:
        if os.path.exists(directory):
            if os.access(directory, os.W_OK):
                print(f"✅ {directory}: 可写")
            else:
                print(f"❌ {directory}: 不可写")
        else:
            print(f"📁 {directory}: 不存在，将自动创建")

def main():
    """主函数"""
    print("🚀 开始诊断文件上传阻塞问题...")
    
    # 检查服务器状态
    if not check_server_status():
        print("\n❌ 服务器未运行，请先启动服务器:")
        print("python server.py")
        return
    
    # 检查文件权限
    check_file_permissions()
    
    # 测试文件上传
    client_id = test_simple_upload()
    
    if client_id:
        # 测试翻译任务
        test_translation_task(client_id)
        print("\n✅ 后端功能测试通过！")
        print("💡 问题可能在前端JavaScript代码中")
    else:
        print("\n❌ 后端功能测试失败！")
        print("💡 问题在服务器端，请检查日志")
    
    # 检查浏览器控制台
    check_browser_console()
    
    print(f"\n{'='*60}")
    print("诊断完成！")
    print(f"{'='*60}")
    print("💡 下一步操作:")
    print("1. 如果后端测试通过，访问测试页面: http://127.0.0.1:8000/test")
    print("2. 如果测试页面工作正常，问题在主页面")
    print("3. 如果测试页面也有问题，问题在服务器端")
    print("4. 检查浏览器控制台错误信息")
    print("5. 检查服务器日志: tail -f logs/app.log")

if __name__ == "__main__":
    main()

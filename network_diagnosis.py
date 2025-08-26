#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络诊断脚本
帮助排查Hugging Face访问问题
"""

import os
import sys
import subprocess
import urllib.request
import socket
import time
from pathlib import Path

def test_dns_resolution():
    """测试DNS解析"""
    print("🔍 测试DNS解析...")
    
    domains = [
        "huggingface.co",
        "www.huggingface.co",
        "huggingface-hub.org",
        "www.google.com"
    ]
    
    for domain in domains:
        try:
            ip = socket.gethostbyname(domain)
            print(f"✅ {domain} -> {ip}")
        except socket.gaierror as e:
            print(f"❌ {domain} DNS解析失败: {e}")

def test_http_connection():
    """测试HTTP连接"""
    print("\n🌐 测试HTTP连接...")
    
    test_urls = [
        ("https://huggingface.co", "Hugging Face主页"),
        ("https://www.google.com", "Google"),
        ("https://www.baidu.com", "百度"),
        ("https://httpbin.org/get", "HTTP测试服务")
    ]
    
    for url, description in test_urls:
        try:
            start_time = time.time()
            response = urllib.request.urlopen(url, timeout=10)
            end_time = time.time()
            
            status = response.getcode()
            response_time = (end_time - start_time) * 1000
            
            print(f"✅ {description}: {status} ({response_time:.1f}ms)")
            response.close()
            
        except Exception as e:
            print(f"❌ {description}: {e}")

def test_huggingface_specific():
    """测试Hugging Face特定功能"""
    print("\n🤗 测试Hugging Face特定功能...")
    
    # 测试模型页面访问
    model_name = "Billyyy/mn_nllb_1.3B_continue"
    model_url = f"https://huggingface.co/{model_name}"
    
    try:
        response = urllib.request.urlopen(model_url, timeout=15)
        if response.getcode() == 200:
            print(f"✅ 模型页面访问成功: {model_url}")
        else:
            print(f"⚠️  模型页面返回状态码: {response.getcode()}")
        response.close()
    except Exception as e:
        print(f"❌ 模型页面访问失败: {e}")
    
    # 测试模型文件访问
    model_files = [
        "config.json",
        "pytorch_model.bin",
        "tokenizer.json"
    ]
    
    for file_name in model_files:
        file_url = f"{model_url}/resolve/main/{file_name}"
        try:
            response = urllib.request.urlopen(file_url, timeout=15)
            file_size = len(response.read())
            response.close()
            print(f"✅ 文件访问成功: {file_name} ({file_size} bytes)")
        except Exception as e:
            print(f"❌ 文件访问失败: {file_name}: {e}")

def test_proxy_settings():
    """测试代理设置"""
    print("\n🔧 检查代理设置...")
    
    proxy_vars = [
        "HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
        "HTTP_PROXY_USER", "HTTPS_PROXY_USER",
        "HTTP_PROXY_PASS", "HTTPS_PROXY_PASS"
    ]
    
    proxy_found = False
    for var in proxy_vars:
        value = os.environ.get(var)
        if value:
            print(f"📡 发现代理设置: {var} = {value}")
            proxy_found = True
    
    if not proxy_found:
        print("ℹ️  未发现代理设置")
    
    # 检查系统代理
    try:
        import winreg
        print("\n🔍 检查Windows系统代理...")
        
        # 检查Internet设置中的代理
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                               r"Software\Microsoft\Windows\CurrentVersion\Internet Settings")
            proxy_enable, _ = winreg.QueryValueEx(key, "ProxyEnable")
            if proxy_enable:
                proxy_server, _ = winreg.QueryValueEx(key, "ProxyServer")
                print(f"⚠️  系统代理已启用: {proxy_server}")
            else:
                print("✅ 系统代理未启用")
            winreg.CloseKey(key)
        except Exception as e:
            print(f"ℹ️  无法检查系统代理设置: {e}")
            
    except ImportError:
        print("ℹ️  非Windows系统，跳过系统代理检查")

def test_firewall_ports():
    """测试防火墙端口"""
    print("\n🔥 测试防火墙端口...")
    
    # 测试常用端口
    ports = [80, 443, 8080, 3128]
    
    for port in ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(('8.8.8.8', port))
            sock.close()
            
            if result == 0:
                print(f"✅ 端口 {port} 开放")
            else:
                print(f"❌ 端口 {port} 被阻止")
        except Exception as e:
            print(f"⚠️  端口 {port} 测试失败: {e}")

def test_curl_availability():
    """测试curl可用性"""
    print("\n📡 测试curl工具...")
    
    try:
        result = subprocess.run(["curl", "--version"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✅ curl可用: {version_line}")
            
            # 测试curl访问Hugging Face
            print("🔄 测试curl访问Hugging Face...")
            test_result = subprocess.run([
                "curl", "-I", "--connect-timeout", "10", 
                "https://huggingface.co"
            ], capture_output=True, text=True, timeout=15)
            
            if test_result.returncode == 0:
                print("✅ curl访问Hugging Face成功")
            else:
                print(f"❌ curl访问Hugging Face失败: {test_result.stderr}")
        else:
            print("❌ curl不可用")
    except FileNotFoundError:
        print("❌ curl未安装")
    except Exception as e:
        print(f"⚠️  curl测试异常: {e}")

def test_git_availability():
    """测试git可用性"""
    print("\n📚 测试git工具...")
    
    try:
        result = subprocess.run(["git", "--version"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version_line = result.stdout.strip()
            print(f"✅ git可用: {version_line}")
            
            # 测试git访问Hugging Face
            print("🔄 测试git访问Hugging Face...")
            test_result = subprocess.run([
                "git", "ls-remote", "--exit-code", 
                "https://huggingface.co/Billyyy/mn_nllb_1.3B_continue"
            ], capture_output=True, text=True, timeout=15)
            
            if test_result.returncode == 0:
                print("✅ git访问Hugging Face成功")
            else:
                print(f"❌ git访问Hugging Face失败: {test_result.stderr}")
        else:
            print("❌ git不可用")
    except FileNotFoundError:
        print("❌ git未安装")
    except Exception as e:
        print(f"⚠️  git测试异常: {e}")

def generate_report():
    """生成诊断报告"""
    print("\n📋 生成诊断报告...")
    
    report_file = "network_diagnosis_report.txt"
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"网络诊断报告\n")
            f.write(f"生成时间: {timestamp}\n")
            f.write(f"=" * 50 + "\n\n")
            
            # 系统信息
            f.write("系统信息:\n")
            f.write(f"操作系统: {os.name}\n")
            f.write(f"Python版本: {sys.version}\n")
            f.write(f"当前目录: {os.getcwd()}\n\n")
            
            # 网络配置
            f.write("网络配置:\n")
            for var in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]:
                value = os.environ.get(var)
                if value:
                    f.write(f"{var}: {value}\n")
            f.write("\n")
            
            # 环境变量
            f.write("相关环境变量:\n")
            for var in ["PATH", "PYTHONPATH", "CUDA_PATH"]:
                value = os.environ.get(var)
                if value:
                    f.write(f"{var}: {value}\n")
            f.write("\n")
        
        print(f"✅ 诊断报告已生成: {report_file}")
        
    except Exception as e:
        print(f"❌ 生成诊断报告失败: {e}")

def main():
    """主函数"""
    print("🔍 网络诊断工具")
    print("=" * 50)
    print("此工具将帮助您诊断Hugging Face访问问题")
    print()
    
    # 执行各项测试
    test_dns_resolution()
    test_http_connection()
    test_huggingface_specific()
    test_proxy_settings()
    test_firewall_ports()
    test_curl_availability()
    test_git_availability()
    
    # 生成报告
    generate_report()
    
    print("\n🎯 诊断完成！")
    print("\n💡 常见解决方案:")
    print("1. 检查网络连接和防火墙设置")
    print("2. 配置代理服务器（如果需要）")
    print("3. 尝试使用VPN或更换网络")
    print("4. 检查DNS设置")
    print("5. 查看详细报告: network_diagnosis_report.txt")

if __name__ == "__main__":
    main()

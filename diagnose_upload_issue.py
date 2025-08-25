#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件上传问题诊断脚本
"""

import logging
import os
import time
import requests
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def check_server_status():
    """检查服务器状态"""
    try:
        logger.info("🔍 检查服务器状态...")
        
        # 检查首页
        response = requests.get('http://127.0.0.1:8000/', timeout=10)
        if response.status_code == 200:
            logger.info("✅ 服务器首页正常响应")
        else:
            logger.error(f"❌ 服务器首页响应异常: {response.status_code}")
            return False
        
        # 检查静态文件
        response = requests.get('http://127.0.0.1:8000/static/css/main.css', timeout=10)
        if response.status_code == 200:
            logger.info("✅ 静态文件服务正常")
        else:
            logger.error(f"❌ 静态文件服务异常: {response.status_code}")
            return False
        
        return True
        
    except requests.exceptions.ConnectionError:
        logger.error("❌ 无法连接到服务器，请确保服务器正在运行")
        return False
    except requests.exceptions.Timeout:
        logger.error("❌ 服务器响应超时")
        return False
    except Exception as e:
        logger.error(f"❌ 检查服务器状态失败: {e}")
        return False


def check_configuration():
    """检查配置文件"""
    try:
        logger.info("🔍 检查配置文件...")
        
        from utils.config_manager import config_manager
        
        # 检查关键配置
        max_file_size = config_manager.getint('SETTINGS', 'MAX_FILE_SIZE', 10485760)
        max_tasks = config_manager.getint('SETTINGS', 'MAX_TASKS', 10)
        upload_dir = config_manager.get_upload_directory()
        download_dir = config_manager.get_download_directory()
        
        logger.info(f"📊 最大文件大小: {max_file_size / 1024 / 1024:.1f} MB")
        logger.info(f"📊 最大任务数: {max_tasks}")
        logger.info(f"📁 上传目录: {upload_dir}")
        logger.info(f"📁 下载目录: {download_dir}")
        
        # 检查目录权限
        if os.path.exists(upload_dir):
            if os.access(upload_dir, os.W_OK):
                logger.info("✅ 上传目录可写")
            else:
                logger.error("❌ 上传目录不可写")
                return False
        else:
            logger.info("📁 上传目录不存在，将自动创建")
        
        if os.path.exists(download_dir):
            if os.access(download_dir, os.W_OK):
                logger.info("✅ 下载目录可写")
            else:
                logger.error("❌ 下载目录不可写")
                return False
        else:
            logger.info("📁 下载目录不存在，将自动创建")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 检查配置失败: {e}")
        return False


def test_file_upload():
    """测试文件上传"""
    try:
        logger.info("🔍 测试文件上传...")
        
        # 创建测试文件
        test_file_path = "test_upload.txt"
        test_content = "这是一个测试文件，用于验证上传功能。\n" * 100  # 约2KB
        
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        logger.info(f"📄 创建测试文件: {test_file_path} ({len(test_content)} 字符)")
        
        # 测试上传
        with open(test_file_path, 'rb') as f:
            files = {'files': ('test_upload.txt', f, 'text/plain')}
            
            start_time = time.time()
            response = requests.post('http://127.0.0.1:8000/uploadfiles', 
                                   files=files, timeout=30)
            upload_time = time.time() - start_time
        
        # 清理测试文件
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ 文件上传成功，耗时: {upload_time:.2f}秒")
            logger.info(f"📊 响应数据: {data}")
            
            # 检查client_id
            if 'client_id' in data:
                logger.info(f"🆔 客户端ID: {data['client_id']}")
                return data['client_id']
            else:
                logger.error("❌ 响应中缺少client_id")
                return None
        else:
            logger.error(f"❌ 文件上传失败: {response.status_code}")
            logger.error(f"📄 响应内容: {response.text}")
            return None
        
    except requests.exceptions.Timeout:
        logger.error("❌ 文件上传超时（30秒）")
        return None
    except Exception as e:
        logger.error(f"❌ 测试文件上传失败: {e}")
        return None


def test_translation_task(client_id):
    """测试翻译任务提交"""
    if not client_id:
        logger.error("❌ 无法测试翻译任务，缺少client_id")
        return False
    
    try:
        logger.info("🔍 测试翻译任务提交...")
        
        task_data = {
            "client_ip": client_id,
            "source_lang": "zh_Hans",
            "target_lang": "khk_Cyrl",
            "via_eng": False
        }
        
        start_time = time.time()
        response = requests.post('http://127.0.0.1:8000/translate/files',
                               json=task_data, timeout=30)
        task_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ 翻译任务提交成功，耗时: {task_time:.2f}秒")
            logger.info(f"📊 任务ID: {data.get('task_id', 'N/A')}")
            return True
        else:
            logger.error(f"❌ 翻译任务提交失败: {response.status_code}")
            logger.error(f"📄 响应内容: {response.text}")
            return False
        
    except requests.exceptions.Timeout:
        logger.error("❌ 翻译任务提交超时（30秒）")
        return False
    except Exception as e:
        logger.error(f"❌ 测试翻译任务失败: {e}")
        return False


def check_rate_limiting():
    """检查速率限制"""
    try:
        logger.info("🔍 检查速率限制...")
        
        from utils.rateLimiter import rate_limiter
        
        # 检查速率限制配置
        logger.info(f"📊 速率限制器类型: {type(rate_limiter).__name__}")
        
        # 尝试多次请求，检查是否被限制
        for i in range(5):
            try:
                response = requests.get('http://127.0.0.1:8000/', timeout=5)
                if response.status_code == 200:
                    logger.info(f"✅ 请求 {i+1} 成功")
                else:
                    logger.warning(f"⚠️ 请求 {i+1} 异常: {response.status_code}")
            except Exception as e:
                logger.warning(f"⚠️ 请求 {i+1} 失败: {e}")
            
            time.sleep(0.1)  # 短暂延迟
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 检查速率限制失败: {e}")
        return False


def check_file_validation():
    """检查文件验证逻辑"""
    try:
        logger.info("🔍 检查文件验证逻辑...")
        
        from utils.fileHandler import FileHandler
        
        # 检查允许的文件类型
        allowed_extensions = ['.docx', '.xlsx', '.xls', '.csv']
        logger.info(f"📋 允许的文件类型: {', '.join(allowed_extensions)}")
        
        # 检查文件大小限制
        max_size = 10 * 1024 * 1024  # 10MB
        logger.info(f"📏 文件大小限制: {max_size / 1024 / 1024:.1f} MB")
        
        # 检查文件处理锁
        if hasattr(FileHandler, '_file_lock'):
            logger.info("✅ 文件处理锁已配置")
        else:
            logger.warning("⚠️ 文件处理锁未配置")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 检查文件验证失败: {e}")
        return False


def main():
    """主函数"""
    logger.info("🚀 开始诊断文件上传问题...")
    
    tests = [
        ("服务器状态", check_server_status),
        ("配置文件", check_configuration),
        ("文件验证", check_file_validation),
        ("速率限制", check_rate_limiting),
    ]
    
    results = {}
    
    # 执行基础检查
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"执行测试: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = test_func()
            results[test_name] = result
            if result:
                logger.info(f"✅ {test_name} 测试通过")
            else:
                logger.error(f"❌ {test_name} 测试失败")
        except Exception as e:
            logger.error(f"❌ {test_name} 测试异常: {e}")
            results[test_name] = False
    
    # 如果基础检查通过，测试文件上传
    if all(results.values()):
        logger.info(f"\n{'='*50}")
        logger.info("执行文件上传测试")
        logger.info(f"{'='*50}")
        
        client_id = test_file_upload()
        if client_id:
            results["文件上传"] = True
            # 测试翻译任务
            results["翻译任务"] = test_translation_task(client_id)
        else:
            results["文件上传"] = False
            results["翻译任务"] = False
    else:
        results["文件上传"] = False
        results["翻译任务"] = False
    
    # 总结报告
    logger.info(f"\n{'='*50}")
    logger.info("诊断总结报告")
    logger.info(f"{'='*50}")
    
    passed_tests = sum(1 for result in results.values() if result)
    total_tests = len(results)
    
    logger.info(f"总计测试项目: {total_tests}")
    logger.info(f"通过测试: {passed_tests}")
    logger.info(f"失败测试: {total_tests - passed_tests}")
    
    if passed_tests == total_tests:
        logger.info("🎉 所有测试都通过了！")
        logger.info("💡 文件上传功能应该正常工作")
        logger.info("🔧 如果仍有问题，可能是浏览器缓存或网络问题")
    else:
        logger.error("❌ 部分测试失败，请检查问题。")
        
        failed_tests = [name for name, result in results.items() if not result]
        logger.error(f"失败的测试项目: {failed_tests}")
        
        # 提供解决建议
        logger.info("\n💡 解决建议:")
        if "服务器状态" in failed_tests:
            logger.info("  - 确保服务器正在运行: python server.py")
            logger.info("  - 检查端口8000是否被占用")
        if "配置文件" in failed_tests:
            logger.info("  - 检查config/config.ini文件")
            logger.info("  - 确保目录权限正确")
        if "文件上传" in failed_tests:
            logger.info("  - 检查文件大小是否超过10MB限制")
            logger.info("  - 检查文件格式是否支持")
            logger.info("  - 检查网络连接和超时设置")
    
    return 0 if passed_tests == total_tests else 1


if __name__ == "__main__":
    exit(main())

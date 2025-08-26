#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
健壮的蒙古语翻译模型下载脚本
包含多种下载方式和错误处理
"""

import os
import sys
import logging
import time
import subprocess
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('model_download.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

def check_network_connection():
    """检查网络连接"""
    import urllib.request
    
    test_urls = [
        "https://huggingface.co",
        "https://www.google.com",
        "https://www.baidu.com"
    ]
    
    for url in test_urls:
        try:
            urllib.request.urlopen(url, timeout=10)
            logger.info(f"✅ 网络连接正常: {url}")
            return True
        except Exception as e:
            logger.warning(f"⚠️  网络连接失败: {url} - {e}")
    
    return False

def install_dependencies():
    """安装必要的依赖"""
    try:
        import transformers
        import torch
        import huggingface_hub
        logger.info("✅ 所有必要的库已安装")
        return True
    except ImportError as e:
        logger.info("📦 安装必要的库...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                "transformers", "torch", "huggingface_hub", "--upgrade"
            ])
            logger.info("✅ 依赖安装完成")
            return True
        except Exception as e:
            logger.error(f"❌ 依赖安装失败: {e}")
            return False

def download_with_huggingface_cli(model_name, cache_dir):
    """使用huggingface-cli命令行工具下载"""
    try:
        logger.info("🔄 尝试使用huggingface-cli下载...")
        
        # 检查是否安装了huggingface-cli
        try:
            subprocess.run(["huggingface-cli", "--version"], 
                         capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.info("📦 安装huggingface-cli...")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "huggingface_hub[cli]"
            ])
        
        # 创建本地目录
        local_dir = os.path.join(cache_dir, model_name.replace("/", "_"))
        os.makedirs(local_dir, exist_ok=True)
        
        # 执行下载命令
        cmd = [
            "huggingface-cli", "download", model_name,
            "--local-dir", local_dir,
            "--cache-dir", cache_dir
        ]
        
        logger.info(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ huggingface-cli下载成功")
            return local_dir
        else:
            logger.error(f"❌ huggingface-cli下载失败: {result.stderr}")
            return None
            
    except Exception as e:
        logger.error(f"❌ huggingface-cli下载异常: {e}")
        return None

def download_with_git_lfs(model_name, cache_dir):
    """使用git-lfs下载模型"""
    try:
        logger.info("🔄 尝试使用git-lfs下载...")
        
        # 检查git是否安装
        try:
            subprocess.run(["git", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("❌ git未安装，请先安装git")
            return None
        
        # 创建本地目录
        local_dir = os.path.join(cache_dir, model_name.replace("/", "_"))
        if os.path.exists(local_dir):
            import shutil
            shutil.rmtree(local_dir)
        
        # 克隆仓库
        repo_url = f"https://huggingface.co/{model_name}"
        logger.info(f"克隆仓库: {repo_url}")
        
        result = subprocess.run([
            "git", "clone", repo_url, local_dir
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ git克隆成功")
            
            # 进入目录并拉取LFS文件
            os.chdir(local_dir)
            subprocess.run(["git", "lfs", "pull"], check=True)
            os.chdir("..")
            
            return local_dir
        else:
            logger.error(f"❌ git克隆失败: {result.stderr}")
            return None
            
    except Exception as e:
        logger.error(f"❌ git-lfs下载异常: {e}")
        return None

def download_with_manual_curl(model_name, cache_dir):
    """使用curl手动下载模型文件"""
    try:
        logger.info("🔄 尝试使用curl手动下载...")
        
        # 检查curl是否可用
        try:
            subprocess.run(["curl", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("❌ curl未安装，请先安装curl")
            return None
        
        # 创建本地目录
        local_dir = os.path.join(cache_dir, model_name.replace("/", "_"))
        os.makedirs(local_dir, exist_ok=True)
        
        # 模型文件列表（常见的必要文件）
        model_files = [
            "config.json",
            "pytorch_model.bin",
            "tokenizer.json",
            "tokenizer_config.json",
            "special_tokens_map.json",
            "vocab.txt"
        ]
        
        base_url = f"https://huggingface.co/{model_name}/resolve/main"
        
        downloaded_files = []
        for file_name in model_files:
            file_url = f"{base_url}/{file_name}"
            local_file = os.path.join(local_dir, file_name)
            
            logger.info(f"下载文件: {file_name}")
            try:
                result = subprocess.run([
                    "curl", "-L", "-o", local_file, file_url
                ], capture_output=True, text=True)
                
                if result.returncode == 0 and os.path.exists(local_file):
                    downloaded_files.append(file_name)
                    logger.info(f"✅ {file_name} 下载成功")
                else:
                    logger.warning(f"⚠️  {file_name} 下载失败")
            except Exception as e:
                logger.warning(f"⚠️  {file_name} 下载异常: {e}")
        
        if len(downloaded_files) >= 3:  # 至少需要config.json, pytorch_model.bin, tokenizer
            logger.info(f"✅ 手动下载完成，成功下载 {len(downloaded_files)} 个文件")
            return local_dir
        else:
            logger.error("❌ 手动下载失败，文件不完整")
            return None
            
    except Exception as e:
        logger.error(f"❌ curl手动下载异常: {e}")
        return None

def download_with_transformers(model_name, cache_dir):
    """使用transformers库下载"""
    try:
        logger.info("🔄 尝试使用transformers库下载...")
        
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        from huggingface_hub import snapshot_download
        
        # 创建本地目录
        local_dir = os.path.join(cache_dir, model_name.replace("/", "_"))
        os.makedirs(local_dir, exist_ok=True)
        
        # 使用snapshot_download
        local_path = snapshot_download(
            repo_id=model_name,
            cache_dir=cache_dir,
            local_dir=local_dir,
            resume_download=True,
            local_files_only=False,
            max_workers=1  # 减少并发，提高稳定性
        )
        
        if os.path.exists(local_path):
            logger.info("✅ transformers下载成功")
            return local_path
        else:
            logger.error("❌ transformers下载失败")
            return None
            
    except Exception as e:
        logger.error(f"❌ transformers下载异常: {e}")
        return None

def verify_model_files(model_path):
    """验证模型文件完整性"""
    if not os.path.exists(model_path):
        return False
    
    required_files = ["config.json", "pytorch_model.bin"]
    optional_files = ["tokenizer.json", "tokenizer_config.json", "vocab.txt"]
    
    # 检查必需文件
    for file_name in required_files:
        file_path = os.path.join(model_path, file_name)
        if not os.path.exists(file_path):
            logger.error(f"❌ 缺少必需文件: {file_name}")
            return False
    
    # 检查可选文件
    found_optional = 0
    for file_name in optional_files:
        file_path = os.path.join(model_path, file_name)
        if os.path.exists(file_path):
            found_optional += 1
    
    logger.info(f"✅ 模型文件验证通过")
    logger.info(f"  必需文件: {len(required_files)}/{len(required_files)}")
    logger.info(f"  可选文件: {found_optional}/{len(optional_files)}")
    
    return True

def main():
    """主函数"""
    model_name = "Billyyy/mn_nllb_1.3B_continue"
    cache_dir = "./cache"
    
    print("🤖 健壮的蒙古语翻译模型下载工具")
    print("=" * 60)
    print(f"模型: {model_name}")
    print(f"缓存目录: {cache_dir}")
    print()
    
    # 检查网络连接
    if not check_network_connection():
        print("❌ 网络连接检查失败，请检查网络设置")
        return
    
    # 安装依赖
    if not install_dependencies():
        print("❌ 依赖安装失败")
        return
    
    # 创建缓存目录
    os.makedirs(cache_dir, exist_ok=True)
    
    # 尝试多种下载方式
    download_methods = [
        ("Transformers库", download_with_transformers),
        ("HuggingFace CLI", download_with_huggingface_cli),
        ("Git LFS", download_with_git_lfs),
        ("手动CURL", download_with_manual_curl)
    ]
    
    model_path = None
    for method_name, download_func in download_methods:
        print(f"\n🔄 尝试方法: {method_name}")
        try:
            model_path = download_func(model_name, cache_dir)
            if model_path and verify_model_files(model_path):
                print(f"🎉 使用 {method_name} 下载成功！")
                break
            else:
                print(f"⚠️  {method_name} 下载失败或文件不完整")
        except Exception as e:
            print(f"❌ {method_name} 执行异常: {e}")
    
    if model_path:
        print(f"\n✅ 模型下载完成！")
        print(f"📁 本地路径: {model_path}")
        
        # 更新配置文件
        config_file = "config/config.ini"
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if model_name not in content:
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if line.strip() == "[MODEL_LIST]":
                        for j in range(i + 1, len(lines)):
                            if lines[j].strip().startswith('[') and lines[j].strip().endswith(']'):
                                lines.insert(j, f"{model_name} = {model_path}")
                                break
                        break
                
                with open(config_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines))
                
                print("✅ 配置文件已更新")
        
        print("\n📋 下一步操作:")
        print("1. 重启翻译服务器")
        print("2. 测试蒙古语翻译功能")
        
    else:
        print("\n💥 所有下载方法都失败了！")
        print("请检查:")
        print("1. 网络连接是否正常")
        print("2. 是否有防火墙或代理限制")
        print("3. 磁盘空间是否充足")
        print("4. 查看详细日志: model_download.log")

if __name__ == "__main__":
    main()

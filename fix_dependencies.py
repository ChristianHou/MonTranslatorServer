#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依赖检查和修复脚本
解决protobuf等依赖问题
"""

import subprocess
import sys
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_package(package_name):
    """检查包是否已安装"""
    try:
        __import__(package_name)
        logger.info(f"✅ {package_name} 已安装")
        return True
    except ImportError:
        logger.warning(f"⚠️  {package_name} 未安装")
        return False


def install_package(package_name):
    """安装包"""
    try:
        logger.info(f"🔧 正在安装 {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        logger.info(f"✅ {package_name} 安装成功")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ {package_name} 安装失败: {e}")
        return False


def check_and_fix_dependencies():
    """检查并修复依赖"""
    logger.info("🔍 检查依赖包...")
    
    # 需要检查的包
    required_packages = [
        "protobuf",
        "sentencepiece", 
        "sacremoses"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        if not check_package(package):
            missing_packages.append(package)
    
    if missing_packages:
        logger.info(f"📦 需要安装的包: {missing_packages}")
        
        # 安装缺失的包
        for package in missing_packages:
            if not install_package(package):
                logger.error(f"❌ 无法安装 {package}")
                return False
        
        logger.info("✅ 所有依赖包安装完成")
    else:
        logger.info("✅ 所有依赖包都已安装")
    
    return True


def test_tokenizer_loading():
    """测试tokenizer加载"""
    try:
        logger.info("🧪 测试tokenizer加载...")
        
        # 测试transformers导入
        import transformers
        logger.info(f"✅ transformers 版本: {transformers.__version__}")
        
        # 测试AutoTokenizer
        from transformers import AutoTokenizer
        logger.info("✅ AutoTokenizer 导入成功")
        
        # 测试protobuf
        import google.protobuf
        logger.info(f"✅ protobuf 版本: {google.protobuf.__version__}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ tokenizer测试失败: {e}")
        return False


def main():
    """主函数"""
    logger.info("🚀 开始依赖检查和修复...")
    
    # 检查并修复依赖
    if not check_and_fix_dependencies():
        logger.error("❌ 依赖修复失败")
        return 1
    
    # 测试tokenizer加载
    if not test_tokenizer_loading():
        logger.error("❌ tokenizer测试失败")
        return 1
    
    logger.info("🎉 所有依赖问题都已解决！")
    logger.info("🚀 现在可以尝试启动服务器了！")
    
    return 0


if __name__ == "__main__":
    exit(main())

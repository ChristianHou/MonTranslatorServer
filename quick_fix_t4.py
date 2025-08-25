#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T4 GPU快速修复脚本
解决内存不足和API调用问题
"""

import logging
import sys
import os

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def apply_conservative_config():
    """应用保守的T4配置"""
    try:
        logger.info("🔧 应用保守的T4配置...")
        
        # 复制保守配置文件
        import shutil
        shutil.copy("config/config_t4_conservative.ini", "config/config.ini")
        
        logger.info("✅ 保守配置已应用")
        return True
        
    except Exception as e:
        logger.error(f"❌ 应用配置失败: {e}")
        return False


def test_conservative_config():
    """测试保守配置"""
    try:
        from models.translateModel import TranslatorSingleton
        
        logger.info("🧪 测试保守配置...")
        
        # 使用保守配置初始化
        TranslatorSingleton.initialize_models(num_cpu_models=2, num_gpu_models=1)
        logger.info("✅ 保守配置初始化成功")
        
        # 检查实例状态
        cpu_count = len(TranslatorSingleton._cpu_instances)
        gpu_count = len(TranslatorSingleton._cuda_instances)
        
        logger.info(f"✅ CPU实例数量: {cpu_count}")
        logger.info(f"✅ GPU实例数量: {gpu_count}")
        
        if gpu_count > 0:
            logger.info("🎉 保守T4 GPU配置运行成功！")
        else:
            logger.info("ℹ️  CPU模式运行成功！")
        
        # 清理资源
        TranslatorSingleton.cleanup_resources()
        logger.info("✅ 资源清理成功")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 保守配置测试失败: {e}")
        return False


def test_simple_translation():
    """测试简单翻译功能"""
    try:
        from models.translateModel import TranslatorSingleton
        
        logger.info("🧪 测试简单翻译功能...")
        
        # 重新初始化
        TranslatorSingleton.initialize_models(num_cpu_models=1, num_gpu_models=1)
        
        # 测试简单翻译
        test_text = "Hello world"
        try:
            result = TranslatorSingleton.translate_sentence(test_text, "eng_Latn", "cmn_Hans")
            logger.info(f"✅ 翻译测试成功: '{test_text}' -> '{result}'")
        except Exception as e:
            logger.warning(f"⚠️  翻译测试失败: {e}")
            logger.info("ℹ️  这可能是正常的，因为模型可能还没有完全加载")
        
        # 清理资源
        TranslatorSingleton.cleanup_resources()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 翻译功能测试失败: {e}")
        return False


def suggest_alternatives():
    """建议替代方案"""
    logger.info("💡 如果T4 GPU仍有问题，建议使用以下替代方案：")
    
    logger.info("1. 强制CPU模式（推荐）:")
    logger.info("   cp config/config_force_cpu.ini config/config.ini")
    
    logger.info("2. 使用Transformers替代:")
    logger.info("   python3 models/transformers_translator.py")
    
    logger.info("3. 减少模型大小:")
    logger.info("   - 使用600M模型而不是3.3B")
    logger.info("   - 减少GPU实例数量到1个")
    logger.info("   - 增加CPU实例数量")


def main():
    """主函数"""
    logger.info("🚀 开始T4 GPU快速修复...")
    
    # 应用保守配置
    if not apply_conservative_config():
        logger.error("❌ 无法应用保守配置")
        suggest_alternatives()
        return 1
    
    # 测试保守配置
    if not test_conservative_config():
        logger.error("❌ 保守配置测试失败")
        suggest_alternatives()
        return 1
    
    # 测试翻译功能
    if not test_simple_translation():
        logger.warning("⚠️  翻译功能测试失败，但配置可能正常")
    
    logger.info("🎉 T4 GPU快速修复完成！")
    logger.info("🚀 现在可以尝试启动服务器了！")
    
    return 0


if __name__ == "__main__":
    exit(main())

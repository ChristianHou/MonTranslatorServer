#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型检查脚本
验证配置文件中的模型是否能被正确加载
"""

import os
import sys
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def check_config_files():
    """检查配置文件"""
    logger.info("🔍 检查配置文件...")
    
    config_files = [
        "config/config.ini",
        "config/config_t4_optimized.ini"
    ]
    
    for config_file in config_files:
        if os.path.exists(config_file):
            logger.info(f"✅ 配置文件存在: {config_file}")
        else:
            logger.warning(f"⚠️  配置文件不存在: {config_file}")
    
    return config_files


def check_model_paths():
    """检查模型路径"""
    logger.info("🔍 检查模型路径...")
    
    # 检查缓存目录
    cache_dir = Path("cache")
    if cache_dir.exists():
        logger.info(f"✅ 缓存目录存在: {cache_dir}")
        
        # 检查模型子目录
        model_subdirs = [
            "ct2/facebook-nllb-200-distilled-600M",
            "ct2/facebook-nllb-200-3.3B",
            "models--facebook--nllb-200-1.3B/snapshots/b0de46b488af0cf31749cd8da5ed3171e11b2309",
            "models--facebook--nllb-200-distilled-600M/snapshots/f8d333a098d19b4fd9a8b18f94170487ad3f821d"
        ]
        
        for subdir in model_subdirs:
            full_path = cache_dir / subdir
            if full_path.exists():
                logger.info(f"✅ 模型目录存在: {full_path}")
                
                # 检查是否有模型文件
                model_files = list(full_path.glob("*.bin")) + list(full_path.glob("*.safetensors"))
                if model_files:
                    logger.info(f"✅ 模型文件存在: {len(model_files)} 个文件")
                else:
                    logger.warning(f"⚠️  模型目录为空: {full_path}")
            else:
                logger.warning(f"⚠️  模型目录不存在: {full_path}")
    else:
        logger.error(f"❌ 缓存目录不存在: {cache_dir}")
        return False
    
    return True


def check_config_manager():
    """检查配置管理器"""
    logger.info("🔍 检查配置管理器...")
    
    try:
        from utils.config_manager import config_manager
        
        # 检查关键配置项
        configs_to_check = [
            ("SETTINGS", "SEQ_TRANSLATE_MODEL"),
            ("PATHS", "MODEL_PATH"),
            ("SETTINGS", "ENABLE_CUDA"),
            ("GPU", "GPU_INSTANCES")
        ]
        
        for section, key in configs_to_check:
            try:
                value = config_manager.get(section, key)
                logger.info(f"✅ 配置项 {section}.{key} = {value}")
            except Exception as e:
                logger.error(f"❌ 配置项 {section}.{key} 读取失败: {e}")
        
        # 检查模型路径
        try:
            model_name = config_manager.get("SETTINGS", "SEQ_TRANSLATE_MODEL")
            model_path = config_manager.get_model_path(model_name)
            logger.info(f"✅ 模型路径解析成功: {model_path}")
            
            # 检查模型路径是否存在
            if os.path.exists(model_path):
                logger.info(f"✅ 模型路径存在: {model_path}")
            else:
                logger.error(f"❌ 模型路径不存在: {model_path}")
                
        except Exception as e:
            logger.error(f"❌ 模型路径解析失败: {e}")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ 无法导入配置管理器: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ 配置管理器检查失败: {e}")
        return False


def check_translator_singleton():
    """检查翻译器单例"""
    logger.info("🔍 检查翻译器单例...")
    
    try:
        from models.translateModel import TranslatorSingleton
        
        # 尝试初始化模型
        logger.info("🧪 尝试初始化模型...")
        
        # 使用较小的配置进行测试
        TranslatorSingleton.initialize_models(num_cpu_models=1, num_gpu_models=1)
        
        # 获取GPU状态
        gpu_status = TranslatorSingleton.get_gpu_status()
        logger.info(f"✅ GPU状态获取成功: {gpu_status}")
        
        # 清理资源
        TranslatorSingleton.cleanup_resources()
        logger.info("✅ 资源清理成功")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ 无法导入翻译器: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ 翻译器检查失败: {e}")
        return False


def check_dependencies():
    """检查依赖包"""
    logger.info("🔍 检查依赖包...")
    
    required_packages = [
        "torch",
        "ctranslate2",
        "transformers",
        "fastapi",
        "uvicorn"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"✅ 依赖包 {package} 已安装")
        except ImportError:
            logger.error(f"❌ 依赖包 {package} 未安装")
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"❌ 缺少依赖包: {missing_packages}")
        return False
    
    return True


def check_cuda_availability():
    """检查CUDA可用性"""
    logger.info("🔍 检查CUDA可用性...")
    
    try:
        import torch
        
        if torch.cuda.is_available():
            logger.info(f"✅ CUDA可用，版本: {torch.version.cuda}")
            logger.info(f"✅ GPU数量: {torch.cuda.device_count()}")
            
            for i in range(torch.cuda.device_count()):
                gpu_name = torch.cuda.get_device_name(i)
                gpu_memory = torch.cuda.get_device_properties(i).total_memory / 1024**3
                logger.info(f"✅ GPU {i}: {gpu_name}, 内存: {gpu_memory:.1f}GB")
        else:
            logger.warning("⚠️  CUDA不可用")
            return False
            
    except ImportError:
        logger.error("❌ PyTorch未安装")
        return False
    except Exception as e:
        logger.error(f"❌ CUDA检查失败: {e}")
        return False
    
    try:
        import ctranslate2
        
        # 检查CTranslate2 CUDA支持
        if hasattr(ctranslate2, 'cuda') and hasattr(ctranslate2.cuda, 'get_device_count'):
            gpu_count = ctranslate2.cuda.get_device_count()
            logger.info(f"✅ CTranslate2 CUDA可用，GPU数量: {gpu_count}")
        else:
            logger.warning("⚠️  CTranslate2 CUDA不可用或功能不完整")
            return False
            
    except ImportError:
        logger.error("❌ CTranslate2未安装")
        return False
    except Exception as e:
        logger.error(f"❌ CTranslate2 CUDA检查失败: {e}")
        return False
    
    return True


def main():
    """主函数"""
    logger.info("🚀 开始模型检查...")
    
    checks = [
        ("配置文件", check_config_files),
        ("模型路径", check_model_paths),
        ("依赖包", check_dependencies),
        ("CUDA可用性", check_cuda_availability),
        ("配置管理器", check_config_manager),
        ("翻译器", check_translator_singleton)
    ]
    
    results = {}
    
    for check_name, check_func in checks:
        logger.info(f"\n{'='*50}")
        logger.info(f"检查项目: {check_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = check_func()
            results[check_name] = result
            if result:
                logger.info(f"✅ {check_name} 检查通过")
            else:
                logger.error(f"❌ {check_name} 检查失败")
        except Exception as e:
            logger.error(f"❌ {check_name} 检查异常: {e}")
            results[check_name] = False
    
    # 总结报告
    logger.info(f"\n{'='*50}")
    logger.info("检查总结报告")
    logger.info(f"{'='*50}")
    
    passed_checks = sum(1 for result in results.values() if result)
    total_checks = len(results)
    
    logger.info(f"总计检查项目: {total_checks}")
    logger.info(f"通过检查: {passed_checks}")
    logger.info(f"失败检查: {total_checks - passed_checks}")
    
    if passed_checks == total_checks:
        logger.info("🎉 所有检查项目都通过了！模型应该能够正常加载。")
        return 0
    else:
        logger.error("❌ 部分检查项目失败，请根据上述信息修复问题。")
        
        # 显示失败的检查项目
        failed_checks = [name for name, result in results.items() if not result]
        logger.error(f"失败的检查项目: {failed_checks}")
        
        return 1


if __name__ == "__main__":
    exit(main())

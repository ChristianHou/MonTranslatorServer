#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断CUDA问题脚本
分析为什么ctranslate2无法使用CUDA设备
"""

import logging
import sys
import os

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_pytorch_cuda():
    """检查PyTorch CUDA支持"""
    try:
        import torch
        
        logger.info(f"✅ PyTorch版本: {torch.__version__}")
        logger.info(f"✅ CUDA可用: {torch.cuda.is_available()}")
        
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            logger.info(f"✅ GPU数量: {gpu_count}")
            
            for i in range(gpu_count):
                gpu_name = torch.cuda.get_device_name(i)
                gpu_memory = torch.cuda.get_device_properties(i).total_memory / 1024**3
                logger.info(f"✅ GPU {i}: {gpu_name}, 内存: {gpu_memory:.1f}GB")
            
            return True
        else:
            logger.warning("⚠️  PyTorch CUDA不可用")
            return False
            
    except ImportError:
        logger.error("❌ PyTorch未安装")
        return False
    except Exception as e:
        logger.error(f"❌ 测试PyTorch CUDA时出错: {e}")
        return False


def check_ctranslate2_cuda():
    """检查ctranslate2 CUDA支持"""
    try:
        import ctranslate2
        
        logger.info(f"✅ ctranslate2版本: {ctranslate2.__version__}")
        
        # 检查是否有cuda属性
        if hasattr(ctranslate2, 'cuda'):
            logger.info("✅ ctranslate2有cuda属性")
            
            # 检查cuda模块的属性
            cuda_attrs = dir(ctranslate2.cuda)
            logger.info(f"ctranslate2.cuda属性: {cuda_attrs}")
            
            # 检查关键方法
            key_methods = ['get_device_count', 'is_available', 'get_device_memory_info']
            for method in key_methods:
                if hasattr(ctranslate2.cuda, method):
                    logger.info(f"✅ ctranslate2.cuda.{method} 方法存在")
                else:
                    logger.warning(f"⚠️  ctranslate2.cuda.{method} 方法不存在")
            
            return True
        else:
            logger.error("❌ ctranslate2没有cuda属性")
            return False
            
    except ImportError as e:
        logger.error(f"❌ ctranslate2导入失败: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ 检查ctranslate2时出错: {e}")
        return False


def test_ctranslate2_cuda_device():
    """测试ctranslate2是否能真正使用CUDA设备"""
    try:
        from utils.config_manager import config_manager
        
        # 获取模型路径
        model_name = config_manager.get("SETTINGS", "SEQ_TRANSLATE_MODEL")
        model_path = config_manager.get_model_path(model_name)
        
        logger.info(f"🧪 测试模型路径: {model_path}")
        
        if not os.path.exists(model_path):
            logger.error(f"❌ 模型路径不存在: {model_path}")
            return False
        
        # 尝试创建CUDA设备上的translator
        logger.info("🧪 尝试创建CUDA设备上的translator...")
        
        try:
            import ctranslate2
            
            # 测试不同的CUDA设备参数
            test_configs = [
                {"device": "cuda", "name": "cuda"},
                {"device": "cpu", "name": "cpu"},
                {"device": "auto", "name": "auto"}
            ]
            
            for config in test_configs:
                try:
                    logger.info(f"🧪 测试配置: {config['name']}")
                    
                    translator = ctranslate2.Translator(
                        model_path,
                        device=config['device'],
                        inter_threads=1,
                        intra_threads=1
                    )
                    
                    logger.info(f"✅ 配置 {config['name']} 成功！")
                    del translator
                    return True
                    
                except Exception as e:
                    logger.warning(f"⚠️  配置 {config['name']} 失败: {e}")
                    continue
            
            logger.error("❌ 所有CUDA配置都失败了")
            return False
            
        except Exception as e:
            logger.error(f"❌ 创建translator时出错: {e}")
            return False
            
    except Exception as e:
        logger.error(f"❌ 测试ctranslate2 CUDA设备时出错: {e}")
        return False


def check_cuda_environment():
    """检查CUDA环境"""
    logger.info("🔍 检查CUDA环境...")
    
    # 检查环境变量
    cuda_env_vars = ['CUDA_HOME', 'CUDA_PATH', 'LD_LIBRARY_PATH', 'PATH']
    for var in cuda_env_vars:
        value = os.environ.get(var, '未设置')
        logger.info(f"{var}: {value}")
    
    # 检查CUDA库文件
    cuda_lib_paths = [
        '/usr/local/cuda/lib64',
        '/usr/local/cuda/lib',
        '/opt/cuda/lib64',
        '/opt/cuda/lib'
    ]
    
    for lib_path in cuda_lib_paths:
        if os.path.exists(lib_path):
            logger.info(f"✅ CUDA库路径存在: {lib_path}")
            # 检查是否有CUDA库文件
            cuda_libs = [f for f in os.listdir(lib_path) if 'cuda' in f.lower() and f.endswith('.so')]
            if cuda_libs:
                logger.info(f"  - 找到CUDA库文件: {len(cuda_libs)} 个")
                for lib in cuda_libs[:3]:  # 只显示前3个
                    logger.info(f"    - {lib}")
        else:
            logger.warning(f"⚠️  CUDA库路径不存在: {lib_path}")
    
    return True


def suggest_solutions():
    """建议解决方案"""
    logger.info("💡 建议解决方案...")
    
    logger.info("1. 使用强制CPU模式配置:")
    logger.info("   cp config/config_force_cpu.ini config/config.ini")
    
    logger.info("2. 重新安装支持CUDA的ctranslate2:")
    logger.info("   pip uninstall ctranslate2")
    logger.info("   pip install ctranslate2[cuda]")
    
    logger.info("3. 或者从源码编译:")
    logger.info("   git clone https://github.com/OpenNMT/CTranslate2.git")
    logger.info("   cd CTranslate2")
    logger.info("   mkdir build && cd build")
    logger.info("   cmake -DCMAKE_BUILD_TYPE=Release -DWITH_CUDA=ON ..")
    logger.info("   make -j$(nproc)")
    
    logger.info("4. 检查CUDA环境变量:")
    logger.info("   export CUDA_HOME=/usr/local/cuda")
    logger.info("   export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH")
    
    logger.info("5. 验证CUDA安装:")
    logger.info("   nvidia-smi")
    logger.info("   nvcc --version")


def main():
    """主函数"""
    logger.info("🚀 开始CUDA问题诊断...")
    
    checks = [
        ("PyTorch CUDA", check_pytorch_cuda),
        ("ctranslate2 CUDA", check_ctranslate2_cuda),
        ("ctranslate2 CUDA设备测试", test_ctranslate2_cuda_device),
        ("CUDA环境", check_cuda_environment)
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
    logger.info("诊断总结报告")
    logger.info(f"{'='*50}")
    
    passed_checks = sum(1 for result in results.values() if result)
    total_checks = len(results)
    
    logger.info(f"总计检查项目: {total_checks}")
    logger.info(f"通过检查: {passed_checks}")
    logger.info(f"失败检查: {total_checks - passed_checks}")
    
    if passed_checks == total_checks:
        logger.info("🎉 所有检查都通过了！CUDA支持正常。")
    else:
        logger.error("❌ 部分检查失败，CUDA支持有问题。")
        
        # 显示失败的检查项目
        failed_checks = [name for name, result in results.items() if not result]
        logger.error(f"失败的检查项目: {failed_checks}")
        
        # 提供解决方案
        suggest_solutions()
    
    return 0 if passed_checks == total_checks else 1


if __name__ == "__main__":
    exit(main())

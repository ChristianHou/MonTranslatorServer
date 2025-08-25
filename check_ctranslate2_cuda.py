#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查ctranslate2 CUDA支持状态
诊断CUDA功能不可用的问题
"""

import logging
import sys
import os

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_python_environment():
    """检查Python环境"""
    logger.info("🔍 检查Python环境...")
    
    logger.info(f"Python版本: {sys.version}")
    logger.info(f"Python路径: {sys.executable}")
    logger.info(f"当前工作目录: {os.getcwd()}")
    
    return True


def check_ctranslate2_installation():
    """检查ctranslate2安装状态"""
    logger.info("🔍 检查ctranslate2安装状态...")
    
    try:
        import ctranslate2
        logger.info(f"✅ ctranslate2导入成功，版本: {ctranslate2.__version__}")
        
        # 检查ctranslate2的属性
        ctranslate2_attrs = dir(ctranslate2)
        logger.info(f"ctranslate2属性: {ctranslate2_attrs}")
        
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


def check_pytorch_cuda():
    """检查PyTorch CUDA支持"""
    logger.info("🔍 检查PyTorch CUDA支持...")
    
    try:
        import torch
        
        logger.info(f"PyTorch版本: {torch.__version__}")
        logger.info(f"CUDA可用: {torch.cuda.is_available()}")
        
        if torch.cuda.is_available():
            logger.info(f"CUDA版本: {torch.version.cuda}")
            logger.info(f"GPU数量: {torch.cuda.device_count()}")
            
            for i in range(torch.cuda.device_count()):
                gpu_name = torch.cuda.get_device_name(i)
                gpu_memory = torch.cuda.get_device_properties(i).total_memory / 1024**3
                logger.info(f"GPU {i}: {gpu_name}, 内存: {gpu_memory:.1f}GB")
        else:
            logger.warning("⚠️  PyTorch CUDA不可用")
            
        return True
        
    except ImportError:
        logger.error("❌ PyTorch未安装")
        return False
    except Exception as e:
        logger.error(f"❌ 检查PyTorch CUDA时出错: {e}")
        return False


def test_ctranslate2_cuda_calls():
    """测试ctranslate2 CUDA调用"""
    logger.info("🧪 测试ctranslate2 CUDA调用...")
    
    try:
        import ctranslate2
        
        if hasattr(ctranslate2, 'cuda'):
            # 测试get_device_count
            try:
                device_count = ctranslate2.cuda.get_device_count()
                logger.info(f"✅ ctranslate2.cuda.get_device_count() 成功: {device_count}")
            except Exception as e:
                logger.error(f"❌ ctranslate2.cuda.get_device_count() 失败: {e}")
            
            # 测试is_available
            try:
                if hasattr(ctranslate2.cuda, 'is_available'):
                    is_available = ctranslate2.cuda.is_available()
                    logger.info(f"✅ ctranslate2.cuda.is_available() 成功: {is_available}")
                else:
                    logger.warning("⚠️  ctranslate2.cuda.is_available 方法不存在")
            except Exception as e:
                logger.error(f"❌ ctranslate2.cuda.is_available() 失败: {e}")
            
            # 测试get_device_memory_info
            try:
                if hasattr(ctranslate2.cuda, 'get_device_memory_info'):
                    memory_info = ctranslate2.cuda.get_device_memory_info(0)
                    logger.info(f"✅ ctranslate2.cuda.get_device_memory_info(0) 成功: {memory_info}")
                else:
                    logger.warning("⚠️  ctranslate2.cuda.get_device_memory_info 方法不存在")
            except Exception as e:
                logger.error(f"❌ ctranslate2.cuda.get_device_memory_info(0) 失败: {e}")
        else:
            logger.error("❌ ctranslate2没有cuda属性，无法测试")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试ctranslate2 CUDA调用时出错: {e}")
        return False


def suggest_solutions():
    """建议解决方案"""
    logger.info("💡 建议解决方案...")
    
    logger.info("1. 重新安装支持CUDA的ctranslate2:")
    logger.info("   pip uninstall ctranslate2")
    logger.info("   pip install ctranslate2[cuda]")
    
    logger.info("2. 或者从源码编译:")
    logger.info("   git clone https://github.com/OpenNMT/CTranslate2.git")
    logger.info("   cd CTranslate2")
    logger.info("   mkdir build && cd build")
    logger.info("   cmake -DCMAKE_BUILD_TYPE=Release -DWITH_CUDA=ON ..")
    logger.info("   make -j$(nproc)")
    
    logger.info("3. 检查CUDA环境变量:")
    logger.info("   export CUDA_HOME=/usr/local/cuda")
    logger.info("   export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH")
    
    logger.info("4. 验证CUDA安装:")
    logger.info("   nvidia-smi")
    logger.info("   nvcc --version")


def main():
    """主函数"""
    logger.info("🚀 开始ctranslate2 CUDA支持检查...")
    
    checks = [
        ("Python环境", check_python_environment),
        ("ctranslate2安装", check_ctranslate2_installation),
        ("CUDA环境", check_cuda_environment),
        ("PyTorch CUDA", check_pytorch_cuda),
        ("ctranslate2 CUDA调用", test_ctranslate2_cuda_calls)
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

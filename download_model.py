#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从Hugging Face下载蒙古语翻译模型
模型: Billyyy/mn_nllb_1.3B_continue
"""

import os
import sys
import logging
from pathlib import Path
import time
from tqdm import tqdm

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

def download_model_from_huggingface(model_name: str, cache_dir: str = "./cache"):
    """
    从Hugging Face下载模型
    
    Args:
        model_name: Hugging Face模型名称
        cache_dir: 本地缓存目录
    """
    try:
        logger.info(f"🚀 开始下载模型: {model_name}")
        logger.info(f"📁 缓存目录: {cache_dir}")
        
        # 创建缓存目录
        os.makedirs(cache_dir, exist_ok=True)
        
        # 检查是否已经下载
        model_cache_path = os.path.join(cache_dir, "models--" + model_name.replace("/", "--"))
        if os.path.exists(model_cache_path):
            logger.info(f"✅ 模型已存在于缓存: {model_cache_path}")
            return model_cache_path
        
        # 导入必要的库
        try:
            from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
            from huggingface_hub import snapshot_download
        except ImportError as e:
            logger.error(f"❌ 缺少必要的库: {e}")
            logger.info("请运行: pip install transformers huggingface_hub torch")
            return None
        
        # 下载模型
        logger.info("📥 正在下载模型文件...")
        start_time = time.time()
        
        # 使用snapshot_download下载完整模型
        local_model_path = snapshot_download(
            repo_id=model_name,
            cache_dir=cache_dir,
            local_dir=os.path.join(cache_dir, model_name.replace("/", "_")),
            resume_download=True,
            local_files_only=False
        )
        
        download_time = time.time() - start_time
        logger.info(f"✅ 模型下载完成！耗时: {download_time:.2f}秒")
        logger.info(f"📁 本地路径: {local_model_path}")
        
        # 验证模型文件
        if os.path.exists(local_model_path):
            # 计算模型大小
            total_size = 0
            file_count = 0
            for root, dirs, files in os.walk(local_model_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    total_size += os.path.getsize(file_path)
                    file_count += 1
            
            logger.info(f"📊 模型统计:")
            logger.info(f"  文件数量: {file_count}")
            logger.info(f"  总大小: {total_size / (1024*1024*1024):.2f} GB")
            
            # 测试加载模型
            logger.info("🧪 测试模型加载...")
            try:
                tokenizer = AutoTokenizer.from_pretrained(local_model_path)
                model = AutoModelForSeq2SeqLM.from_pretrained(
                    local_model_path,
                    low_cpu_mem_usage=True
                )
                logger.info("✅ 模型加载测试成功！")
                
                # 清理内存
                del tokenizer, model
                
            except Exception as e:
                logger.warning(f"⚠️  模型加载测试失败: {e}")
                logger.info("模型文件已下载，但加载测试失败，可能需要手动检查")
        
        return local_model_path
        
    except Exception as e:
        logger.error(f"❌ 模型下载失败: {e}")
        return None

def update_config_file(model_name: str, model_path: str):
    """更新配置文件，添加新模型"""
    config_file = "config/config.ini"
    
    if not os.path.exists(config_file):
        logger.warning(f"⚠️  配置文件不存在: {config_file}")
        return False
    
    try:
        # 读取配置文件
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已经存在该模型
        if model_name in content:
            logger.info(f"✅ 模型 {model_name} 已存在于配置文件中")
            return True
        
        # 在MODEL_LIST部分添加新模型
        if "[MODEL_LIST]" in content:
            # 找到MODEL_LIST部分的结束位置
            lines = content.split('\n')
            model_list_end = 0
            
            for i, line in enumerate(lines):
                if line.strip() == "[MODEL_LIST]":
                    # 找到下一个section的开始
                    for j in range(i + 1, len(lines)):
                        if lines[j].strip().startswith('[') and lines[j].strip().endswith(']'):
                            model_list_end = j
                            break
                    break
            
            if model_list_end > 0:
                # 在MODEL_LIST部分末尾添加新模型
                new_line = f"{model_name} = {model_path}"
                lines.insert(model_list_end, new_line)
                
                # 写回文件
                with open(config_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines))
                
                logger.info(f"✅ 已更新配置文件，添加模型: {model_name}")
                return True
        
        logger.warning("⚠️  无法找到MODEL_LIST部分，请手动添加模型配置")
        return False
        
    except Exception as e:
        logger.error(f"❌ 更新配置文件失败: {e}")
        return False

def create_model_info_file(model_name: str, model_path: str):
    """创建模型信息文件"""
    info_file = os.path.join(model_path, "model_info.txt")
    
    try:
        info_content = f"""模型信息
========

模型名称: {model_name}
下载时间: {time.strftime('%Y-%m-%d %H:%M:%S')}
本地路径: {model_path}

模型描述:
这是一个基于NLLB-200的蒙古语翻译模型，专门针对蒙古语进行了继续训练。

使用方法:
1. 在config.ini中添加模型配置
2. 在代码中使用transformers库加载模型
3. 支持蒙古语与其他语言之间的翻译

注意事项:
- 模型大小约为1.3B参数
- 需要足够的内存来加载模型
- 建议使用GPU加速翻译性能

技术支持:
如有问题，请查看模型页面: https://huggingface.co/{model_name}
"""
        
        with open(info_file, 'w', encoding='utf-8') as f:
            f.write(info_content)
        
        logger.info(f"✅ 已创建模型信息文件: {info_file}")
        
    except Exception as e:
        logger.error(f"❌ 创建模型信息文件失败: {e}")

def main():
    """主函数"""
    model_name = "Billyyy/mn_nllb_1.3B_continue"
    cache_dir = "./cache"
    
    print("🤖 蒙古语翻译模型下载工具")
    print("=" * 50)
    print(f"模型: {model_name}")
    print(f"缓存目录: {cache_dir}")
    print()
    
    # 检查Python环境
    try:
        import transformers
        import torch
        print(f"✅ Transformers版本: {transformers.__version__}")
        print(f"✅ PyTorch版本: {torch.__version__}")
        print(f"✅ CUDA可用: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"✅ GPU数量: {torch.cuda.device_count()}")
        print()
    except ImportError as e:
        print(f"❌ 缺少必要的库: {e}")
        print("请运行: pip install transformers torch huggingface_hub")
        return
    
    # 下载模型
    model_path = download_model_from_huggingface(model_name, cache_dir)
    
    if model_path:
        print(f"\n🎉 模型下载成功！")
        print(f"📁 本地路径: {model_path}")
        
        # 创建模型信息文件
        create_model_info_file(model_name, model_path)
        
        # 更新配置文件
        if update_config_file(model_name, model_path):
            print("✅ 配置文件已更新")
        else:
            print("⚠️  请手动更新配置文件")
        
        print("\n📋 下一步操作:")
        print("1. 重启翻译服务器")
        print("2. 在配置文件中设置新模型为默认模型")
        print("3. 测试蒙古语翻译功能")
        
    else:
        print("\n💥 模型下载失败！")
        print("请检查网络连接和错误日志")

if __name__ == "__main__":
    main()

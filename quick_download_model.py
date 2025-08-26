#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速下载蒙古语翻译模型
"""

import os
import subprocess
import sys

def quick_download():
    """快速下载模型"""
    model_name = "Billyyy/mn_nllb_1.3B_continue"
    
    print(f"🚀 开始下载模型: {model_name}")
    
    # 检查必要的库
    try:
        import transformers
        import huggingface_hub
        print("✅ 必要的库已安装")
    except ImportError:
        print("📦 安装必要的库...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "transformers", "huggingface_hub", "torch"])
        print("✅ 库安装完成")
    
    # 创建缓存目录
    cache_dir = "./cache"
    os.makedirs(cache_dir, exist_ok=True)
    
    # 下载模型
    try:
        from huggingface_hub import snapshot_download
        
        print("📥 正在下载模型...")
        local_path = snapshot_download(
            repo_id=model_name,
            cache_dir=cache_dir,
            local_dir=os.path.join(cache_dir, model_name.replace("/", "_"))
        )
        
        print(f"✅ 模型下载完成！")
        print(f"📁 本地路径: {local_path}")
        
        # 更新配置文件
        config_file = "config/config.ini"
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if model_name not in content:
                # 在MODEL_LIST部分添加新模型
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if line.strip() == "[MODEL_LIST]":
                        # 找到下一个section
                        for j in range(i + 1, len(lines)):
                            if lines[j].strip().startswith('[') and lines[j].strip().endswith(']'):
                                lines.insert(j, f"{model_name} = {local_path}")
                                break
                        break
                
                with open(config_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines))
                
                print("✅ 配置文件已更新")
        
        print("\n🎉 完成！模型已下载并配置")
        
    except Exception as e:
        print(f"❌ 下载失败: {e}")

if __name__ == "__main__":
    quick_download()

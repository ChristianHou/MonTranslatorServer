#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NLLB-MoE 54B 模型下载脚本
从Hugging Face下载facebook/nllb-moe-54b模型到本地缓存目录

使用方法：
python download_nllb_moe.py

需要安装依赖：
pip install huggingface_hub tqdm requests
"""

import os
import sys
from pathlib import Path
from huggingface_hub import snapshot_download, HfApi
from tqdm import tqdm
import requests
import time
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('download_nllb_moe.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class NLLBMoEDownloader:
    def __init__(self, cache_dir="./cache"):
        self.model_id = "facebook/nllb-moe-54b"
        self.cache_dir = Path(cache_dir).absolute()
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 设置环境变量，让huggingface使用指定的缓存目录
        os.environ['HF_HOME'] = str(self.cache_dir)
        os.environ['HUGGINGFACE_HUB_CACHE'] = str(self.cache_dir / "huggingface")

        logger.info(f"缓存目录: {self.cache_dir}")
        logger.info(f"模型ID: {self.model_id}")

    def check_model_info(self):
        """检查模型信息"""
        logger.info("=== 检查模型信息 ===")

        try:
            api = HfApi()
            model_info = api.model_info(self.model_id)

            logger.info(f"模型名称: {model_info.modelId}")
            logger.info(f"标签: {model_info.tags}")
            logger.info(f"下载次数: {model_info.downloads}")

            # 获取文件列表
            files = api.list_repo_files(self.model_id)
            logger.info(f"文件数量: {len(files)}")

            # 计算总大小
            total_size = 0
            for file in files[:10]:  # 只显示前10个文件
                logger.info(f"  - {file}")

            return True

        except Exception as e:
            logger.error(f"获取模型信息失败: {e}")
            return False

    def download_model(self, resume=True):
        """下载模型"""
        logger.info("=== 开始下载模型 ===")
        logger.info(f"目标目录: {self.cache_dir}")

        try:
            # 配置下载参数
            download_kwargs = {
                "repo_id": self.model_id,
                "local_dir": self.cache_dir / "models--facebook--nllb-moe-54b",
                "local_dir_use_symlinks": False,  # 使用硬链接而不是软链接
                "resume_download": resume,
                "max_workers": 4,  # 同时下载的线程数
                "tqdm_class": tqdm,
            }

            logger.info("开始下载...")
            start_time = time.time()

            # 执行下载
            snapshot_path = snapshot_download(**download_kwargs)

            end_time = time.time()
            duration = end_time - start_time

            logger.info("✅ 下载完成!"            logger.info(".2f"            logger.info(f"模型保存位置: {snapshot_path}")

            return snapshot_path

        except KeyboardInterrupt:
            logger.info("下载被用户中断")
            return None
        except Exception as e:
            logger.error(f"下载失败: {e}")
            logger.info("建议检查网络连接或重试")
            return None

    def verify_download(self, model_path):
        """验证下载的完整性"""
        logger.info("=== 验证下载 ===")

        if not model_path or not Path(model_path).exists():
            logger.error("模型路径不存在")
            return False

        try:
            # 检查关键文件是否存在
            required_files = [
                "config.json",
                "tokenizer.json",
                "tokenizer_config.json",
                "pytorch_model.bin.index.json"
            ]

            missing_files = []
            for file in required_files:
                if not (Path(model_path) / file).exists():
                    missing_files.append(file)

            if missing_files:
                logger.warning(f"缺少文件: {missing_files}")
                return False

            # 计算目录大小
            total_size = 0
            file_count = 0
            for file_path in Path(model_path).rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    file_count += 1

            logger.info(","            logger.info(".2f"
            return True

        except Exception as e:
            logger.error(f"验证失败: {e}")
            return False

    def cleanup_cache(self):
        """清理不完整的下载"""
        logger.info("=== 清理缓存 ===")

        try:
            import shutil

            # 查找不完整的下载
            incomplete_dirs = []
            for item in self.cache_dir.iterdir():
                if item.is_dir() and item.name.startswith("models--facebook--nllb-moe-54b"):
                    # 检查是否有.lock文件
                    lock_file = item / ".huggingface" / "download" / ".lock"
                    if lock_file.exists():
                        incomplete_dirs.append(item)

            if incomplete_dirs:
                logger.info(f"发现 {len(incomplete_dirs)} 个不完整的下载")
                for incomplete_dir in incomplete_dirs:
                    logger.info(f"删除: {incomplete_dir}")
                    shutil.rmtree(incomplete_dir, ignore_errors=True)
                logger.info("✅ 清理完成")
            else:
                logger.info("没有发现不完整的下载")

        except Exception as e:
            logger.error(f"清理失败: {e}")

def main():
    """主函数"""
    print("=" * 60)
    print("NLLB-MoE 54B 模型下载器")
    print("=" * 60)
    print(f"模型: facebook/nllb-moe-54b")
    print(f"大小: ~200GB (这是一个非常大的模型)")
    print("=" * 60)

    # 检查参数
    if len(sys.argv) > 1:
        cache_dir = sys.argv[1]
    else:
        cache_dir = "./cache"

    # 创建下载器
    downloader = NLLBMoEDownloader(cache_dir)

    # 检查磁盘空间
    try:
        stat = os.statvfs(cache_dir)
        free_space = stat.f_bavail * stat.f_frsize / (1024**3)  # GB
        logger.info(".2f"
        if free_space < 250:
            logger.warning("磁盘空间可能不足，建议至少保留250GB空间")
            response = input("是否继续? (y/N): ").lower().strip()
            if response not in ['y', 'yes']:
                logger.info("下载已取消")
                return
    except Exception as e:
        logger.warning(f"无法检查磁盘空间: {e}")

    # 检查模型信息
    if not downloader.check_model_info():
        logger.error("无法获取模型信息，请检查网络连接")
        return

    # 清理不完整的下载
    downloader.cleanup_cache()

    # 开始下载
    print("\n⚠️  警告:")
    print("- 这个模型非常大（约200GB）")
    print("- 下载可能需要很长时间")
    print("- 请确保网络连接稳定")
    print("- 可以随时按Ctrl+C中断并在下次继续")

    response = input("\n是否开始下载? (y/N): ").lower().strip()
    if response not in ['y', 'yes']:
        logger.info("下载已取消")
        return

    # 执行下载
    model_path = downloader.download_model()

    if model_path:
        # 验证下载
        if downloader.verify_download(model_path):
            logger.info("🎉 下载和验证都成功完成!")
            logger.info(f"模型位置: {model_path}")
            logger.info("现在可以使用这个模型进行翻译了")
        else:
            logger.warning("下载完成但验证失败，建议重新下载")
    else:
        logger.error("下载失败")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n下载被用户中断")
    except Exception as e:
        logger.error(f"程序异常: {e}")
        sys.exit(1)


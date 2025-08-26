#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
蒙语翻译服务器启动脚本
包含任务管理功能
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/server.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

def main():
    """主函数"""
    try:
        logger.info("🚀 启动蒙语翻译服务器...")
        
        # 检查必要的目录
        required_dirs = ['logs', 'files/upload', 'files/download', 'cache']
        for dir_path in required_dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ 目录检查: {dir_path}")
        
        # 检查配置文件
        config_file = Path('config/config.ini')
        if not config_file.exists():
            logger.error("❌ 配置文件不存在: config/config.ini")
            return 1
        
        logger.info("✅ 配置文件检查通过")
        
        # 导入并启动服务器
        from server import app
        import uvicorn
        
        logger.info("✅ 服务器模块加载成功")
        logger.info("🌐 服务器将在 http://0.0.0.0:8000 启动")
        logger.info("📊 任务管理页面: http://localhost:8000/tasks")
        logger.info("📁 文件上传页面: http://localhost:8000/")
        
        # 启动服务器
        uvicorn.run(
            app="server:app",
            host="0.0.0.0",
            port=8000,
            log_level="info",
            workers=1,
            timeout_keep_alive=300,
            timeout_graceful_shutdown=30
        )
        
    except KeyboardInterrupt:
        logger.info("🛑 服务器被用户中断")
        return 0
    except Exception as e:
        logger.error(f"❌ 服务器启动失败: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

#!/bin/bash

# 快速部署脚本 - 4张T4显卡服务器
# 自动配置和优化多GPU环境

set -e

echo "🚀 快速部署蒙语翻译服务器到4张T4显卡环境..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查是否为root用户
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}❌ 请不要使用root用户运行此脚本${NC}"
    exit 1
fi

# 检查CUDA环境
echo -e "${BLUE}📋 检查CUDA环境...${NC}"
if ! command -v nvidia-smi &> /dev/null; then
    echo -e "${RED}❌ NVIDIA驱动未安装或nvidia-smi不可用${NC}"
    echo -e "${YELLOW}请先安装NVIDIA驱动和CUDA${NC}"
    exit 1
fi

# 检查GPU数量
GPU_COUNT=$(nvidia-smi --list-gpus | wc -l)
echo -e "${GREEN}✅ 检测到 ${GPU_COUNT} 个GPU设备${NC}"

if [ $GPU_COUNT -lt 4 ]; then
    echo -e "${YELLOW}⚠️  警告: 检测到 ${GPU_COUNT} 个GPU，建议至少4个GPU以获得最佳性能${NC}"
    read -p "是否继续部署？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}部署已取消${NC}"
        exit 1
    fi
fi

# 显示GPU信息
echo -e "${BLUE}📊 GPU详细信息:${NC}"
nvidia-smi --query-gpu=index,name,memory.total,memory.free --format=csv,noheader,nounits

# 检查Python环境
echo -e "${BLUE}🐍 检查Python环境...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3未安装${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✅ ${PYTHON_VERSION}${NC}"

# 检查pip
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}❌ pip3未安装${NC}"
    exit 1
fi

# 创建虚拟环境
echo -e "${BLUE}🔧 创建Python虚拟环境...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✅ 虚拟环境创建成功${NC}"
else
    echo -e "${YELLOW}⚠️  虚拟环境已存在${NC}"
fi

# 激活虚拟环境
echo -e "${BLUE}🔌 激活虚拟环境...${NC}"
source venv/bin/activate

# 升级pip
echo -e "${BLUE}⬆️  升级pip...${NC}"
pip install --upgrade pip

# 安装依赖
echo -e "${BLUE}📦 安装项目依赖...${NC}"
pip install -r requirements.txt

# 检查CUDA相关包安装
echo -e "${BLUE}🔍 检查CUDA包安装...${NC}"
python3 -c "
import torch
import ctranslate2
print(f'PyTorch版本: {torch.__version__}')
print(f'CUDA可用: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA版本: {torch.version.cuda}')
    print(f'GPU数量: {torch.cuda.device_count()}')
    for i in range(torch.cuda.device_count()):
        print(f'GPU {i}: {torch.cuda.get_device_name(i)}')
print(f'CTranslate2版本: {ctranslate2.__version__}')
if hasattr(ctranslate2, 'cuda') and hasattr(ctranslate2.cuda, 'get_device_count'):
    print(f'CTranslate2 CUDA可用: GPU数量 {ctranslate2.cuda.get_device_count()}')
else:
    print('CTranslate2 CUDA不可用')
"

# 创建必要的目录
echo -e "${BLUE}📁 创建必要的目录...${NC}"
mkdir -p files/upload files/download logs cache models

# 设置权限
echo -e "${BLUE}🔐 设置目录权限...${NC}"
chmod 755 files/upload files/download logs cache models

# 备份原配置文件
echo -e "${BLUE}💾 备份原配置文件...${NC}"
if [ -f "config/config.ini" ]; then
    cp config/config.ini config/config.ini.backup.$(date +%Y%m%d_%H%M%S)
    echo -e "${GREEN}✅ 原配置文件已备份${NC}"
fi

# 使用T4优化配置
echo -e "${BLUE}⚙️  应用T4优化配置...${NC}"
if [ -f "config/config_t4_optimized.ini" ]; then
    cp config/config_t4_optimized.ini config/config.ini
    echo -e "${GREEN}✅ T4优化配置已应用${NC}"
else
    echo -e "${YELLOW}⚠️  T4优化配置文件不存在，使用默认配置${NC}"
fi

# 验证GPU配置
echo -e "${BLUE}🔧 验证GPU配置...${NC}"
python3 -c "
import configparser
config = configparser.ConfigParser()
config.read('config/config.ini')
gpu_instances = config.getint('GPU', 'GPU_INSTANCES', fallback=4)
cpu_instances = config.getint('GPU', 'CPU_INSTANCES', fallback=2)
print(f'配置的GPU实例数: {gpu_instances}')
print(f'配置的CPU实例数: {cpu_instances}')
print(f'检测到的GPU数: {GPU_COUNT}')
if gpu_instances > GPU_COUNT * 2:
    print('⚠️  警告: 配置的GPU实例数可能过多')
"

# 测试GPU功能
echo -e "${BLUE}🧪 测试GPU功能...${NC}"
python3 -c "
from models.translateModel import TranslatorSingleton
try:
    print('初始化模型...')
    TranslatorSingleton.initialize_models(num_cpu_models=2, num_gpu_models=4)
    print('✅ 模型初始化成功')
    
    gpu_status = TranslatorSingleton.get_gpu_status()
    print(f'GPU状态: {gpu_status}')
    
    print('清理资源...')
    TranslatorSingleton.cleanup_resources()
    print('✅ 资源清理成功')
    
except Exception as e:
    print(f'❌ GPU功能测试失败: {e}')
    exit(1)
"

# 运行多GPU测试
echo -e "${BLUE}🧪 运行多GPU性能测试...${NC}"
if [ -f "test_multi_gpu.py" ]; then
    echo -e "${YELLOW}⚠️  运行多GPU测试可能需要几分钟...${NC}"
    python3 test_multi_gpu.py
    echo -e "${GREEN}✅ 多GPU测试完成${NC}"
else
    echo -e "${YELLOW}⚠️  多GPU测试脚本不存在，跳过测试${NC}"
fi

# 创建systemd服务文件
echo -e "${BLUE}🔧 创建systemd服务文件...${NC}"
sudo tee /etc/systemd/system/mongolian-translator.service > /dev/null <<EOF
[Unit]
Description=Mongolian Translation Server (4x T4 GPU)
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/python server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✅ systemd服务文件创建成功${NC}"

# 创建GPU监控服务
echo -e "${BLUE}🔧 创建GPU监控服务...${NC}"
sudo tee /etc/systemd/system/gpu-monitor.service > /dev/null <<EOF
[Unit]
Description=GPU Monitor Service (4x T4 GPU)
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/python gpu_monitor.py
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✅ GPU监控服务文件创建成功${NC}"

# 重新加载systemd
echo -e "${BLUE}🔄 重新加载systemd...${NC}"
sudo systemctl daemon-reload

# 启用服务
echo -e "${BLUE}🔌 启用服务...${NC}"
sudo systemctl enable mongolian-translator.service
sudo systemctl enable gpu-monitor.service

# 启动服务
echo -e "${BLUE}🚀 启动服务...${NC}"
sudo systemctl start mongolian-translator.service
sudo systemctl start gpu-monitor.service

# 等待服务启动
echo -e "${BLUE}⏳ 等待服务启动...${NC}"
sleep 5

# 检查服务状态
echo -e "${BLUE}📊 检查服务状态...${NC}"
echo -e "${BLUE}翻译服务状态:${NC}"
sudo systemctl status mongolian-translator.service --no-pager -l

echo -e "${BLUE}GPU监控服务状态:${NC}"
sudo systemctl status gpu-monitor.service --no-pager -l

# 测试API接口
echo -e "${BLUE}🧪 测试API接口...${NC}"
sleep 3

# 测试GPU状态接口
if curl -s http://localhost:8000/gpu_status > /dev/null; then
    echo -e "${GREEN}✅ GPU状态接口测试成功${NC}"
else
    echo -e "${YELLOW}⚠️  GPU状态接口测试失败，服务可能还在启动中${NC}"
fi

# 显示部署完成信息
echo -e "${GREEN}🎉 部署完成！${NC}"
echo -e "${BLUE}📋 部署信息:${NC}"
echo -e "  - 项目路径: $(pwd)"
echo -e "  - 虚拟环境: $(pwd)/venv"
echo -e "  - 翻译服务: mongolian-translator"
echo -e "  - GPU监控: gpu-monitor"
echo -e "  - 配置文件: config/config.ini"
echo -e "  - GPU数量: ${GPU_COUNT}"

echo -e "${BLUE}🚀 服务管理命令:${NC}"
echo -e "  # 启动服务"
echo -e "  sudo systemctl start mongolian-translator"
echo -e "  sudo systemctl start gpu-monitor"
echo -e ""
echo -e "  # 停止服务"
echo -e "  sudo systemctl stop mongolian-translator"
echo -e "  sudo systemctl stop gpu-monitor"
echo -e ""
echo -e "  # 重启服务"
echo -e "  sudo systemctl restart mongolian-translator"
echo -e "  sudo systemctl restart gpu-monitor"

echo -e "${BLUE}📊 监控命令:${NC}"
echo -e "  # 查看服务状态"
echo -e "  sudo systemctl status mongolian-translator"
echo -e "  sudo systemctl status gpu-monitor"
echo -e ""
echo -e "  # 查看日志"
echo -e "  sudo journalctl -u mongolian-translator -f"
echo -e "  sudo journalctl -u gpu-monitor -f"
echo -e ""
echo -e "  # 查看GPU状态"
echo -e "  curl http://localhost:8000/gpu_status"
echo -e "  curl http://localhost:8000/system_info"

echo -e "${BLUE}🌐 访问地址:${NC}"
echo -e "  - 翻译服务: http://localhost:8000"
echo -e "  - GPU状态: http://localhost:8000/gpu_status"
echo -e "  - 系统信息: http://localhost:8000/system_info"

echo -e "${BLUE}🔧 性能优化建议:${NC}"
echo -e "  - 监控GPU内存使用率，保持在85%以下"
echo -e "  - 定期检查日志文件大小"
echo -e "  - 根据实际负载调整GPU_INSTANCES参数"
echo -e "  - 使用test_multi_gpu.py进行性能测试"

echo -e "${GREEN}✅ 4张T4显卡蒙语翻译服务器部署完成！${NC}"
echo -e "${BLUE}💡 提示: 首次启动可能需要几分钟来加载模型${NC}"

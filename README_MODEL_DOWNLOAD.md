# 蒙古语翻译模型下载指南

本指南介绍如何从Hugging Face下载蒙古语翻译模型 `Billyyy/mn_nllb_1.3B_continue` 并集成到翻译服务器中。

## 🎯 模型信息

- **模型名称**: `Billyyy/mn_nllb_1.3B_continue`
- **模型类型**: 基于NLLB-200的蒙古语翻译模型
- **模型大小**: 约1.3B参数
- **支持语言**: 蒙古语与其他语言之间的翻译
- **模型页面**: [https://huggingface.co/Billyyy/mn_nllb_1.3B_continue](https://huggingface.co/Billyyy/mn_nllb_1.3B_continue)

## 📥 下载方式

### 方式1: 使用快速下载脚本（推荐）

```bash
# 运行快速下载脚本
python quick_download_model.py
```

### 方式2: 使用完整下载脚本

```bash
# 运行完整下载脚本（包含更多功能）
python download_model.py
```

### 方式3: 使用Windows批处理文件

```cmd
# 双击运行或在命令行中执行
download_model.bat
```

### 方式4: 手动下载

```bash
# 使用huggingface_hub命令行工具
pip install huggingface_hub
huggingface-cli download Billyyy/mn_nllb_1.3B_continue --local-dir ./cache/Billyyy_mn_nllb_1.3B_continue
```

## 🔧 环境要求

### Python库依赖

```bash
pip install transformers torch huggingface_hub
```

### 系统要求

- Python 3.7+
- 至少8GB可用内存（推荐16GB+）
- 稳定的网络连接
- 足够的磁盘空间（约3-5GB）

## 📁 下载目录结构

下载完成后，模型将保存在以下目录结构中：

```
cache/
├── models--Billyyy--mn_nllb_1.3B_continue/
│   ├── snapshots/
│   │   └── [commit_hash]/
│   │       ├── config.json
│   │       ├── pytorch_model.bin
│   │       ├── tokenizer.json
│   │       └── ...
│   └── refs/
└── Billyyy_mn_nllb_1.3B_continue/
    ├── config.json
    ├── pytorch_model.bin
    ├── tokenizer.json
    ├── model_info.txt
    └── ...
```

## ⚙️ 配置文件更新

下载脚本会自动更新 `config/config.ini` 文件，在 `[MODEL_LIST]` 部分添加新模型：

```ini
[MODEL_LIST]
facebook/nllb-200-distilled-600M = ./cache/ct2/facebook-nllb-200-distilled-600M
facebook/nllb-200-1.3B = ./cache/models--facebook--nllb-200-1.3B/snapshots/b0de46b488af0cf31749cd8da5ed3171e11b2309
facebook/nllb-200-3.3B = ./cache/ct2/facebook-nllb-200-3.3B
Billyyy/mn_nllb_1.3B_continue = ./cache/Billyyy_mn_nllb_1.3B_continue
```

## 🚀 使用方法

### 1. 下载模型

```bash
python quick_download_model.py
```

### 2. 重启翻译服务器

```bash
python start_server.py
```

### 3. 测试蒙古语翻译

在翻译界面中选择：
- 源语言：蒙古语（mon_Cyrl）
- 目标语言：中文（cmn_Hans）或其他语言

## 🔍 故障排除

### 常见问题

#### 1. 网络连接问题

```bash
# 检查网络连接
ping huggingface.co

# 使用代理（如果需要）
export HTTPS_PROXY=http://proxy:port
export HTTP_PROXY=http://proxy:port
```

#### 2. 内存不足

```bash
# 检查可用内存
free -h  # Linux
# 或
wmic OS get TotalVisibleMemorySize,FreePhysicalMemory  # Windows
```

#### 3. 磁盘空间不足

```bash
# 检查磁盘空间
df -h  # Linux
# 或
dir  # Windows
```

#### 4. Python库版本冲突

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 日志文件

下载过程中的详细日志保存在 `model_download.log` 文件中，可以查看具体的错误信息。

## 📊 性能优化建议

### 1. GPU加速

如果系统有NVIDIA GPU，建议启用CUDA加速：

```bash
# 安装CUDA版本的PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 2. 内存优化

- 使用 `low_cpu_mem_usage=True` 参数
- 考虑使用模型量化（8位或16位精度）
- 分批处理长文本

### 3. 缓存优化

- 将模型缓存目录放在SSD上
- 定期清理不需要的模型缓存

## 🔄 更新模型

当模型有新版本时，可以重新运行下载脚本：

```bash
# 删除旧版本
rm -rf ./cache/Billyyy_mn_nllb_1.3B_continue

# 重新下载
python quick_download_model.py
```

## 📞 技术支持

如果遇到问题，请：

1. 查看日志文件 `model_download.log`
2. 检查网络连接和系统资源
3. 参考Hugging Face官方文档
4. 在项目Issues中报告问题

## 📚 相关链接

- [Hugging Face模型页面](https://huggingface.co/Billyyy/mn_nllb_1.3B_continue)
- [Transformers文档](https://huggingface.co/docs/transformers/)
- [NLLB-200论文](https://arxiv.org/abs/2207.04672)
- [蒙古语资源](https://github.com/topics/mongolian-language)

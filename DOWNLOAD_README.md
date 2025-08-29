# NLLB-MoE 54B 模型下载指南

本指南介绍如何下载facebook/nllb-moe-54b模型到本地缓存目录。

## 📋 模型信息

- **模型名称**: facebook/nllb-moe-54b
- **模型大小**: ~200GB
- **模型类型**: Mixture of Experts (MoE)
- **支持语言**: 200+种语言
- **下载地址**: https://huggingface.co/facebook/nllb-moe-54b

## ⚠️ 重要提醒

1. **巨大文件**: 这个模型非常大（约200GB），下载需要很长时间
2. **磁盘空间**: 确保至少有250GB可用磁盘空间
3. **网络要求**: 需要稳定的网络连接，下载过程可能持续几天
4. **中断恢复**: 支持断点续传，可以随时中断并继续

## 🚀 下载方法

### 方法1：Windows批处理脚本（推荐）

```cmd
# 双击运行或在命令行中执行
download_nllb_moe.bat
```

**脚本会自动**：
- 检查Python环境
- 安装必要的依赖
- 检查磁盘空间
- 下载模型到`./cache`目录

### 方法2：Python脚本

```bash
# 安装依赖
pip install huggingface_hub

# 运行下载脚本
python download_nllb_moe_simple.py
```

### 方法3：手动下载

```python
from huggingface_hub import snapshot_download

# 下载到指定目录
model_path = snapshot_download(
    repo_id="facebook/nllb-moe-54b",
    local_dir="./cache/models--facebook--nllb-moe-54b",
    local_dir_use_symlinks=False,
    resume_download=True
)
```

## 📁 文件结构

下载完成后，文件结构如下：

```
MonTranslatorServer/
├── cache/
│   └── models--facebook--nllb-moe-54b/
│       ├── config.json
│       ├── tokenizer.json
│       ├── tokenizer_config.json
│       ├── pytorch_model.bin.index.json
│       ├── pytorch_model-00001-of-00008.bin
│       ├── pytorch_model-00002-of-00008.bin
│       ├── ...
│       └── pytorch_model-00008-of-00008.bin
├── download_nllb_moe_simple.py
├── download_nllb_moe.bat
└── ...
```

## 🔧 故障排除

### 问题1：网络连接问题

```bash
# 设置代理（如果需要）
export HTTP_PROXY=http://your-proxy:8080
export HTTPS_PROXY=http://your-proxy:8080

# 或者使用国内镜像
export HF_ENDPOINT=https://hf-mirror.com
```

### 问题2：磁盘空间不足

```bash
# 检查磁盘空间
df -h

# 清理空间
rm -rf ~/.cache/huggingface/*
```

### 问题3：下载中断

脚本支持断点续传，重新运行即可继续：

```bash
python download_nllb_moe_simple.py
```

### 问题4：依赖安装失败

```bash
# 手动安装依赖
pip install --upgrade pip
pip install huggingface_hub

# 使用国内源
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple huggingface_hub
```

## 📊 下载进度监控

### 查看下载进度

```bash
# 查看下载进程
ps aux | grep huggingface

# 查看网络速度
nload

# 查看磁盘使用
du -sh ./cache
```

### 监控日志

```bash
# 查看下载日志
tail -f download_nllb_moe.log
```

## 🎯 使用模型

下载完成后，可以在MonTranslator中使用：

1. **更新配置**：
   ```ini
   # config/config.ini
   [SETTINGS]
   seq_translate_model = facebook/nllb-moe-54b
   ```

2. **运行容器**：
   ```bash
   docker run --gpus all -p 8000:8000 \
     -v $(pwd)/cache:/app/cache \
     -v $(pwd)/files:/app/files \
     -v $(pwd)/config:/app/config \
     mon-translator:gpu
   ```

## 🔄 其他下载选项

### 如果只需要较小的模型

考虑使用以下替代模型：
- `facebook/nllb-200-distilled-600M` (~2.5GB)
- `facebook/nllb-200-1.3B` (~5GB)
- `facebook/nllb-200-3.3B` (~12GB)

### 分批下载

如果网络不稳定，可以分批下载：

```python
from huggingface_hub import HfApi, snapshot_download

# 只下载配置文件
snapshot_download(
    repo_id="facebook/nllb-moe-54b",
    allow_patterns=["*.json", "*.txt"],
    local_dir="./cache/models--facebook--nllb-moe-54b"
)

# 然后下载模型文件
snapshot_download(
    repo_id="facebook/nllb-moe-54b",
    allow_patterns=["*.bin"],
    local_dir="./cache/models--facebook--nllb-moe-54b"
)
```

## 📈 性能对比

| 模型 | 大小 | 内存需求 | 翻译速度 | 质量 |
|------|------|----------|----------|------|
| NLLB-600M | 2.5GB | 4GB | 快 | 良好 |
| NLLB-1.3B | 5GB | 8GB | 中等 | 优秀 |
| NLLB-3.3B | 12GB | 16GB | 中等 | 优秀 |
| **NLLB-MoE-54B** | **200GB** | **32GB+** | **慢** | **最佳** |

## 🎉 完成下载后

1. **验证下载**：
   ```bash
   ls -la ./cache/models--facebook--nllb-moe-54b/
   ```

2. **测试模型**：
   ```python
   from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

   model_path = "./cache/models--facebook--nllb-moe-54b"
   tokenizer = AutoTokenizer.from_pretrained(model_path)
   model = AutoModelForSeq2SeqLM.from_pretrained(model_path)

   print("✅ 模型加载成功！")
   ```

3. **开始使用**：
   - 启动MonTranslator容器
   - 享受高质量的翻译服务

## 🆘 获取帮助

如果下载过程中遇到问题：

1. 检查网络连接
2. 确保有足够的磁盘空间
3. 查看日志文件：`download_nllb_moe.log`
4. 重试下载（支持断点续传）

---

**注意**: 这个模型非常大，请确保您确实需要这么高质量的翻译服务。如果只是测试用途，建议先使用较小的模型。



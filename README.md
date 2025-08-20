# MonTranslatorServer

MonTranslatorServer 是一个基于 FastAPI 的翻译服务器，支持文本翻译和文件翻译功能。

## 功能特点
- 文本翻译：支持实时翻译文本内容
- 文件翻译：支持上传文件进行翻译并下载结果
- WebSocket 实时翻译：支持通过 WebSocket 进行实时序列翻译
- 任务状态查询：支持查询翻译任务的状态

## 安装指南

### 前提条件
- Python 3.10 版本（推荐使用3.10.11）
- 确保您有互联网连接（用于下载依赖包和模型）

### 自动安装
1. 双击运行 `setup_venv.bat` 脚本
2. 按照脚本提示操作

### 手动安装（可选）
如果自动安装脚本失败，您可以尝试手动安装：

1. 创建虚拟环境：
   ```
   python -m venv venv
   ```

2. 激活虚拟环境：
   - Windows：
     ```
     venv\Scripts\activate.bat
     ```
   - Linux/Mac：
     ```
     source venv/bin/activate
     ```

3. 升级 pip：
   ```
   python -m pip install --upgrade pip
   ```

4. 安装依赖：
   ```
   pip install -r requirements.txt
   ```

## 运行服务器
1. 确保已激活虚拟环境
2. 双击运行 `start_server.bat` 脚本，或在命令行中执行：
   ```
   python server.py
   ```

## 访问前端页面
服务器启动后，打开浏览器，访问 `http://localhost:8000` 即可使用翻译功能。

## 常见问题

### 权限问题
如果您在安装过程中遇到权限问题，脚本会尝试在您的用户目录创建虚拟环境。如果仍然失败，请尝试以管理员身份运行脚本。

### PyTorch 安装问题
如果您遇到 PyTorch 相关的安装问题，可以尝试安装特定版本的 PyTorch：
```
# CPU 版本
pip install torch==2.0.1+cpu torchvision==0.15.2+cpu torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cpu

# CUDA 11.7 版本
pip install torch==2.0.1+cu117 torchvision==0.15.2+cu117 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cu117
```

### 端口占用问题
如果端口 8000 已被占用，您可以修改 `server.py` 文件中的端口号：
```python
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)  # 将 8001 改为其他可用端口
```

## 技术栈
- 后端：FastAPI, Python
- 前端：HTML, CSS, JavaScript, Bootstrap 5
- 翻译模型：NLLB (No Language Left Behind)
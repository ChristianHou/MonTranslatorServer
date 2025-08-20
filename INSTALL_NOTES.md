# 安装说明

## 虚拟环境配置
已修改`<mcfile name="setup_venv.bat" path="e:\MonTranslatorServer\setup_venv.bat"></mcfile>`添加`--user`选项，解决了权限问题。

## PyTorch CUDA版本说明
requirements.txt中包含了`<mcfile name="requirements.txt" path="e:\MonTranslatorServer\requirements.txt"></mcfile>`，这是一个带有CUDA 12.1的PyTorch版本。

### 潜在问题
1. 如果你没有NVIDIA显卡，或者没有安装CUDA 12.1，PyTorch可能无法正常安装或运行。
2. 安装过程中可能会遇到与CUDA相关的错误。

### 解决方案
如果遇到CUDA相关问题，可以尝试以下方法：

1. **使用CPU版本的PyTorch**：
   修改requirements.txt中的PyTorch依赖为CPU版本：
   ```
   torch==2.1.2+cpu
   ```

2. **安装适合你CUDA版本的PyTorch**：
   访问[PyTorch官网](https://pytorch.org/)获取适合你CUDA版本的安装命令。

3. **使用conda安装**：
   如果你使用conda，可以尝试：
   ```
   conda install pytorch torchvision torchaudio cpuonly -c pytorch
   ```

## 运行服务器
配置好虚拟环境后，运行以下命令启动服务器：
```
venv\Scripts\activate.bat
python server.py
```

## 访问前端页面
服务器启动后，在浏览器中打开`<mcfile name="index.html" path="e:\MonTranslatorServer\index.html"></mcfile>`开始使用翻译服务。
#!/bin/bash
# 安装缺失的依赖

echo "🔧 安装缺失的依赖..."

# 安装 protobuf
pip install protobuf

# 安装其他可能缺失的依赖
pip install sentencepiece
pip install sacremoses

# 验证安装
echo "✅ 验证安装..."
python -c "import protobuf; print('protobuf 安装成功')" 2>/dev/null || echo "❌ protobuf 安装失败"
python -c "import sentencepiece; print('sentencepiece 安装成功')" 2>/dev/null || echo "❌ sentencepiece 安装失败"
python -c "import sacremoses; print('sacremoses 安装成功')" 2>/dev/null || echo "❌ sacremoses 安装失败"

echo "🎉 依赖安装完成！"

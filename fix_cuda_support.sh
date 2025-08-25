#!/bin/bash
# CUDA支持修复脚本

echo "🔧 修复ctranslate2 CUDA支持..."

# 检查是否在conda环境中
if [[ "$CONDA_DEFAULT_ENV" != "" ]]; then
    echo "✅ 检测到conda环境: $CONDA_DEFAULT_ENV"
    PIP_CMD="pip"
else
    echo "⚠️  未检测到conda环境，使用系统pip"
    PIP_CMD="pip3"
fi

# 卸载当前的ctranslate2
echo "📦 卸载当前ctranslate2..."
$PIP_CMD uninstall -y ctranslate2

# 安装支持CUDA的ctranslate2
echo "📦 安装支持CUDA的ctranslate2..."
$PIP_CMD install ctranslate2[cuda]

# 如果上面的安装失败，尝试其他方法
if [ $? -ne 0 ]; then
    echo "⚠️  标准安装失败，尝试其他方法..."
    
    # 方法1：从预编译wheel安装
    echo "🔧 尝试从预编译wheel安装..."
    $PIP_CMD install --no-cache-dir ctranslate2
    
    # 方法2：如果还是失败，尝试从源码编译
    if [ $? -ne 0 ]; then
        echo "🔧 尝试从源码编译..."
        
        # 安装编译依赖
        $PIP_CMD install cmake ninja
        
        # 克隆源码
        if [ ! -d "CTranslate2" ]; then
            git clone https://github.com/OpenNMT/CTranslate2.git
        fi
        
        cd CTranslate2
        
        # 创建构建目录
        mkdir -p build && cd build
        
        # 配置构建
        cmake -DCMAKE_BUILD_TYPE=Release -DWITH_CUDA=ON ..
        
        # 编译
        make -j$(nproc)
        
        # 安装
        make install
        
        cd ../..
    fi
fi

# 验证安装
echo "✅ 验证CUDA支持..."
python3 -c "
import ctranslate2
print(f'ctranslate2版本: {ctranslate2.__version__}')
if hasattr(ctranslate2, 'cuda'):
    print('✅ CUDA支持可用')
    if hasattr(ctranslate2.cuda, 'get_device_count'):
        try:
            count = ctranslate2.cuda.get_device_count()
            print(f'✅ GPU设备数量: {count}')
        except Exception as e:
            print(f'⚠️  GPU设备检测失败: {e}')
    else:
        print('⚠️  get_device_count方法不可用')
else:
    print('❌ CUDA支持不可用')
"

echo "🎉 CUDA支持修复完成！"

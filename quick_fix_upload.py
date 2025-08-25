#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速修复文件上传问题
"""

import os
import shutil
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def backup_original_files():
    """备份原始文件"""
    try:
        logger.info("💾 备份原始文件...")
        
        files_to_backup = [
            "static/js/translator.js",
            "templates/index.html"
        ]
        
        for file_path in files_to_backup:
            if os.path.exists(file_path):
                backup_path = file_path + ".backup"
                shutil.copy2(file_path, backup_path)
                logger.info(f"  ✅ 已备份: {file_path} -> {backup_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 备份失败: {e}")
        return False

def create_simple_test_page():
    """创建简单的测试页面"""
    try:
        logger.info("🔧 创建简单测试页面...")
        
        test_page = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>文件上传测试</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .test-section { border: 1px solid #ddd; padding: 20px; margin: 20px 0; border-radius: 8px; }
        .btn { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; margin: 5px; }
        .log { background: #f8f9fa; border: 1px solid #dee2e6; padding: 10px; margin: 10px 0; border-radius: 4px; font-family: monospace; max-height: 300px; overflow-y: auto; }
    </style>
</head>
<body>
    <h1>🚀 文件上传功能测试</h1>
    
    <div class="test-section">
        <h2>📁 选择文件</h2>
        <input type="file" id="fileInput" multiple accept=".txt,.docx,.xlsx">
        <div id="fileInfo"></div>
    </div>
    
    <div class="test-section">
        <h2>🌐 语言设置</h2>
        <label>源语言: <select id="sourceLang"><option value="zh_Hans">中文</option><option value="khk_Cyrl">蒙文</option><option value="eng_Latn">英语</option></select></label><br><br>
        <label>目标语言: <select id="targetLang"><option value="khk_Cyrl">蒙文</option><option value="zh_Hans">中文</option><option value="eng_Latn">英语</option></select></label>
    </div>
    
    <div class="test-section">
        <h2>🧪 测试操作</h2>
        <button class="btn" onclick="testUpload()">📤 测试上传</button>
        <button class="btn" onclick="testTranslate()">🔄 测试翻译</button>
        <button class="btn" onclick="clearLog()">🗑️ 清空日志</button>
    </div>
    
    <div class="test-section">
        <h2>📊 测试结果</h2>
        <div id="log" class="log"></div>
    </div>

    <script>
        let clientId = null;
        
        function log(message) {
            const logDiv = document.getElementById('log');
            const timestamp = new Date().toLocaleTimeString();
            logDiv.innerHTML += `<div>[${timestamp}] ${message}</div>`;
            logDiv.scrollTop = logDiv.scrollHeight;
        }
        
        function clearLog() {
            document.getElementById('log').innerHTML = '';
        }
        
        async function testUpload() {
            const fileInput = document.getElementById('fileInput');
            const files = fileInput.files;
            
            if (files.length === 0) {
                log('❌ 请先选择文件');
                return;
            }
            
            log(`🚀 开始上传 ${files.length} 个文件...`);
            
            try {
                const formData = new FormData();
                for (let file of files) {
                    formData.append('files', file);
                    log(`📄 添加文件: ${file.name} (${file.size} 字节)`);
                }
                
                const startTime = Date.now();
                const response = await fetch('/uploadfiles', {
                    method: 'POST',
                    body: formData
                });
                const uploadTime = Date.now() - startTime;
                
                log(`⏱️ 上传耗时: ${uploadTime}ms`);
                log(`📊 响应状态: ${response.status}`);
                
                if (response.ok) {
                    const data = await response.json();
                    log('✅ 上传成功');
                    log(`🆔 客户端ID: ${data.client_id}`);
                    clientId = data.client_id;
                } else {
                    const errorText = await response.text();
                    log(`❌ 上传失败: ${errorText}`);
                }
                
            } catch (error) {
                log(`❌ 上传异常: ${error.message}`);
            }
        }
        
        async function testTranslate() {
            if (!clientId) {
                log('❌ 请先上传文件');
                return;
            }
            
            const sourceLang = document.getElementById('sourceLang').value;
            const targetLang = document.getElementById('targetLang').value;
            
            log('🔄 开始提交翻译任务...');
            log(`🌐 语言: ${sourceLang} → ${targetLang}`);
            
            try {
                const taskData = {
                    client_ip: clientId,
                    source_lang: sourceLang,
                    target_lang: targetLang,
                    via_eng: false
                };
                
                const startTime = Date.now();
                const response = await fetch('/translate/files', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(taskData)
                });
                const taskTime = Date.now() - startTime;
                
                log(`⏱️ 任务提交耗时: ${taskTime}ms`);
                log(`📊 响应状态: ${response.status}`);
                
                if (response.ok) {
                    const data = await response.json();
                    log('✅ 翻译任务提交成功');
                    log(`🆔 任务ID: ${data.task_id}`);
                } else {
                    const errorText = await response.text();
                    log(`❌ 翻译任务失败: ${errorText}`);
                }
                
            } catch (error) {
                log(`❌ 翻译任务异常: ${error.message}`);
            }
        }
        
        // 文件选择事件
        document.getElementById('fileInput').addEventListener('change', function(e) {
            const files = e.target.files;
            const fileInfo = document.getElementById('fileInfo');
            
            if (files.length === 0) {
                fileInfo.innerHTML = '';
                return;
            }
            
            let info = '<h4>已选择的文件:</h4>';
            for (let i = 0; i < files.length; i++) {
                const file = files[i];
                const size = (file.size / 1024).toFixed(2);
                info += `<div>📄 ${file.name} (${size} KB)</div>`;
            }
            fileInfo.innerHTML = info;
        });
        
        log('🚀 测试页面加载完成');
    </script>
</body>
</html>"""
        
        with open('test_upload_simple.html', 'w', encoding='utf-8') as f:
            f.write(test_page)
        
        logger.info("✅ 简单测试页面创建成功: test_upload_simple.html")
        return True
        
    except Exception as e:
        logger.error(f"❌ 创建测试页面失败: {e}")
        return False

def check_server_endpoints():
    """检查服务器端点"""
    try:
        logger.info("🔍 检查服务器端点...")
        
        # 检查server.py中的端点
        server_file = "server.py"
        if not os.path.exists(server_file):
            logger.error(f"❌ 服务器文件不存在: {server_file}")
            return False
        
        with open(server_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查关键端点
        endpoints = [
            ('/uploadfiles', 'POST'),
            ('/translate/files', 'POST'),
            ('/task_status', 'GET')
        ]
        
        for endpoint, method in endpoints:
            if f'@app.{method.lower()}("{endpoint}")' in content or f'@app.{method.lower()}("{endpoint}")' in content:
                logger.info(f"✅ 端点 {method} {endpoint} 存在")
            else:
                logger.warning(f"⚠️ 端点 {method} {endpoint} 可能缺失")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 检查服务器端点失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("🚀 开始快速修复文件上传问题...")
    
    steps = [
        ("备份原始文件", backup_original_files),
        ("检查服务器端点", check_server_endpoints),
        ("创建简单测试页面", create_simple_test_page),
    ]
    
    for step_name, step_func in steps:
        logger.info(f"\n{'='*50}")
        logger.info(f"执行步骤: {step_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = step_func()
            if result:
                logger.info(f"✅ {step_name} 成功")
            else:
                logger.error(f"❌ {step_name} 失败")
        except Exception as e:
            logger.error(f"❌ {step_name} 异常: {e}")
    
    logger.info(f"\n{'='*50}")
    logger.info("快速修复完成！")
    logger.info(f"{'='*50}")
    logger.info("💡 现在请:")
    logger.info("1. 重启服务器: python server.py")
    logger.info("2. 访问测试页面: http://127.0.0.1:8000/test_upload_simple.html")
    logger.info("3. 测试文件上传功能")
    logger.info("4. 检查浏览器控制台是否有错误信息")
    logger.info("5. 如果测试页面工作正常，说明问题在主页面")
    logger.info("6. 如果测试页面也有问题，说明问题在服务器端")

if __name__ == "__main__":
    main()

// 调试版本 - 诊断上传问题
console.log('🚀 开始调试文件上传功能...');

// 检查必要的DOM元素
function checkDOMElements() {
    console.log('🔍 检查DOM元素...');
    
    const requiredElements = [
        'fileInput',
        'fileUploadArea', 
        'fileList',
        'selectedFiles',
        'fileSourceLang',
        'fileTargetLang',
        'fileViaEnglish',
        'uploadTranslateBtn',
        'taskStatus',
        'taskId',
        'statusBadge',
        'progressFill',
        'progressText',
        'checkStatusBtn',
        'downloadBtn'
    ];
    
    const missingElements = [];
    
    for (const id of requiredElements) {
        const element = document.getElementById(id);
        if (element) {
            console.log(`✅ ${id}: 存在`);
        } else {
            console.log(`❌ ${id}: 缺失`);
            missingElements.push(id);
        }
    }
    
    if (missingElements.length > 0) {
        console.error('❌ 缺失的元素:', missingElements);
        return false;
    }
    
    console.log('✅ 所有必要的DOM元素都存在');
    return true;
}

// 简化的上传测试
async function testSimpleUpload() {
    console.log('🧪 开始简单上传测试...');
    
    try {
        // 创建测试文件
        const testContent = '这是一个测试文件。' * 100;
        const testFile = new File([testContent], 'test.txt', { type: 'text/plain' });
        
        console.log('📄 创建测试文件:', testFile.name, testFile.size, '字节');
        
        // 创建FormData
        const formData = new FormData();
        formData.append('files', testFile);
        
        console.log('📤 开始上传...');
        const startTime = Date.now();
        
        const response = await fetch('/uploadfiles', {
            method: 'POST',
            body: formData
        });
        
        const uploadTime = Date.now() - startTime;
        console.log(`⏱️ 上传耗时: ${uploadTime}ms`);
        console.log('📊 响应状态:', response.status, response.statusText);
        
        if (response.ok) {
            const data = await response.json();
            console.log('✅ 上传成功:', data);
            return data.client_id;
        } else {
            const errorText = await response.text();
            console.error('❌ 上传失败:', errorText);
            return null;
        }
        
    } catch (error) {
        console.error('❌ 上传测试异常:', error);
        return null;
    }
}

// 测试翻译任务提交
async function testTranslationTask(clientId) {
    if (!clientId) {
        console.error('❌ 无法测试翻译任务，缺少clientId');
        return false;
    }
    
    console.log('🧪 测试翻译任务提交...');
    
    try {
        const taskData = {
            client_ip: clientId,
            source_lang: 'zh_Hans',
            target_lang: 'khk_Cyrl',
            via_eng: false
        };
        
        console.log('📤 提交翻译任务:', taskData);
        const startTime = Date.now();
        
        const response = await fetch('/translate/files', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(taskData)
        });
        
        const taskTime = Date.now() - startTime;
        console.log(`⏱️ 任务提交耗时: ${taskTime}ms`);
        console.log('📊 响应状态:', response.status, response.statusText);
        
        if (response.ok) {
            const data = await response.json();
            console.log('✅ 翻译任务提交成功:', data);
            return true;
        } else {
            const errorText = await response.text();
            console.error('❌ 翻译任务提交失败:', errorText);
            return false;
        }
        
    } catch (error) {
        console.error('❌ 翻译任务测试异常:', error);
        return false;
    }
}

// 主测试函数
async function runDebugTests() {
    console.log('🚀 开始运行调试测试...');
    
    // 检查DOM元素
    if (!checkDOMElements()) {
        console.error('❌ DOM元素检查失败，停止测试');
        return;
    }
    
    // 测试上传
    const clientId = await testSimpleUpload();
    
    if (clientId) {
        // 测试翻译任务
        await testTranslationTask(clientId);
    }
    
    console.log('🏁 调试测试完成');
}

// 页面加载完成后运行测试
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', runDebugTests);
} else {
    runDebugTests();
}

// 暴露测试函数到全局作用域
window.debugUpload = {
    checkDOMElements,
    testSimpleUpload,
    testTranslationTask,
    runDebugTests
};

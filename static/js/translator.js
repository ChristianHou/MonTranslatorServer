/**
 * 蒙古语翻译助手 - 主要JavaScript逻辑
 * 负责处理前端交互和API调用
 */

class TranslatorApp {
    constructor() {
        this.initializeElements();
        this.bindEvents();
        this.currentTaskId = null;
        this.statusCheckInterval = null;
    }

    initializeElements() {
        // 文本翻译元素
        this.sourceText = document.getElementById('sourceText');
        this.targetText = document.getElementById('targetText');
        this.sourceLang = document.getElementById('sourceLang');
        this.targetLang = document.getElementById('targetLang');
        this.viaEnglish = document.getElementById('viaEnglish');
        this.translateBtn = document.getElementById('translateBtn');
        this.clearBtn = document.getElementById('clearBtn');
        this.swapBtn = document.getElementById('swapLanguages');

        // 文件翻译元素
        this.fileInput = document.getElementById('fileInput');
        this.fileUploadArea = document.getElementById('fileUploadArea');
        this.fileList = document.getElementById('fileList');
        this.selectedFiles = document.getElementById('selectedFiles');
        this.fileSourceLang = document.getElementById('fileSourceLang');
        this.fileTargetLang = document.getElementById('fileTargetLang');
        this.fileViaEnglish = document.getElementById('fileViaEnglish');
        this.uploadTranslateBtn = document.getElementById('uploadTranslateBtn');

        // 任务状态元素
        this.taskStatus = document.getElementById('taskStatus');
        this.taskId = document.getElementById('taskId');
        this.statusBadge = document.getElementById('statusBadge');
        this.progressFill = document.getElementById('progressFill');
        this.progressText = document.getElementById('progressText');
        this.checkStatusBtn = document.getElementById('checkStatusBtn');
        this.downloadBtn = document.getElementById('downloadBtn');

        this.toastContainer = document.getElementById('toastContainer');
    }

    bindEvents() {
        // 文本翻译事件
        this.translateBtn.addEventListener('click', () => this.translateText());
        this.clearBtn.addEventListener('click', () => this.clearText());
        this.swapBtn.addEventListener('click', () => this.swapLanguages());

        // 文件上传事件
        this.fileUploadArea.addEventListener('click', () => this.fileInput.click());
        this.fileUploadArea.addEventListener('dragover', (e) => this.handleDragOver(e));
        this.fileUploadArea.addEventListener('dragleave', (e) => this.handleDragLeave(e));
        this.fileUploadArea.addEventListener('drop', (e) => this.handleDrop(e));
        this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        this.uploadTranslateBtn.addEventListener('click', () => this.uploadAndTranslate());

        // 任务状态事件
        this.checkStatusBtn.addEventListener('click', () => this.checkTaskStatus());

        // 实时输入检测（可选，目前禁用）
        // this.sourceText.addEventListener('input', () => this.debounceTranslate());
    }

    /**
     * 显示Toast通知
     * @param {string} message - 消息内容
     * @param {string} type - 消息类型 (info, success, warning, danger)
     */
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        this.toastContainer.appendChild(toast);
        const toastInstance = new bootstrap.Toast(toast);
        toastInstance.show();
        
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }

    /**
     * 文本翻译功能
     */
    async translateText() {
        const text = this.sourceText.value.trim();
        if (!text) {
            this.showToast('请输入要翻译的文本', 'warning');
            return;
        }

        if (this.sourceLang.value === this.targetLang.value) {
            this.showToast('源语言和目标语言不能相同', 'warning');
            return;
        }

        this.setTranslateLoading(true);

        try {
            const response = await fetch('/translate/text', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    sentences: text,
                    source_lang: this.sourceLang.value,
                    target_lang: this.targetLang.value,
                    via_eng: this.viaEnglish.checked
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || errorData.error || '翻译请求失败');
            }

            const data = await response.json();
            
            if (data.status === 'error' || data.error) {
                this.showToast('翻译出错: ' + (data.error || '未知错误'), 'danger');
            } else {
                this.targetText.value = data.result;
                this.showToast('翻译完成', 'success');
            }

        } catch (error) {
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                this.showToast('网络连接错误，请检查服务器状态', 'danger');
            } else {
                this.showToast('翻译失败: ' + error.message, 'danger');
            }
        } finally {
            this.setTranslateLoading(false);
        }
    }

    /**
     * 设置翻译按钮状态
     * @param {boolean} loading - 是否处于加载状态
     */
    setTranslateLoading(loading) {
        if (loading) {
            this.translateBtn.disabled = true;
            this.translateBtn.innerHTML = '<span class="loading-spinner"></span> 翻译中...';
        } else {
            this.translateBtn.disabled = false;
            this.translateBtn.innerHTML = '<i class="fas fa-language"></i> 开始翻译';
        }
    }

    /**
     * 清空文本内容
     */
    clearText() {
        this.sourceText.value = '';
        this.targetText.value = '';
    }

    /**
     * 交换源语言和目标语言
     */
    swapLanguages() {
        const sourceValue = this.sourceLang.value;
        const targetValue = this.targetLang.value;
        const sourceTextValue = this.sourceText.value;
        const targetTextValue = this.targetText.value;

        this.sourceLang.value = targetValue;
        this.targetLang.value = sourceValue;
        this.sourceText.value = targetTextValue;
        this.targetText.value = sourceTextValue;

        this.swapBtn.style.transform = 'rotate(180deg)';
        setTimeout(() => {
            this.swapBtn.style.transform = '';
        }, 200);
    }

    /**
     * 防抖翻译（预留功能）
     */
    debounceTranslate() {
        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(() => {
            // 可以在这里添加自动翻译逻辑
        }, 1000);
    }

    /**
     * 文件拖拽处理
     */
    handleDragOver(e) {
        e.preventDefault();
        this.fileUploadArea.classList.add('dragover');
    }

    handleDragLeave(e) {
        e.preventDefault();
        this.fileUploadArea.classList.remove('dragover');
    }

    handleDrop(e) {
        e.preventDefault();
        this.fileUploadArea.classList.remove('dragover');
        const files = e.dataTransfer.files;
        this.updateFileList(files);
    }

    handleFileSelect(e) {
        const files = e.target.files;
        this.updateFileList(files);
    }

    /**
     * 更新文件列表显示
     * @param {FileList} files - 选择的文件列表
     */
    updateFileList(files) {
        if (files.length === 0) {
            this.fileList.style.display = 'none';
            this.uploadTranslateBtn.disabled = true;
            return;
        }

        this.fileList.style.display = 'block';
        this.uploadTranslateBtn.disabled = false;
        
        this.selectedFiles.innerHTML = '';
        for (let file of files) {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            fileItem.innerHTML = `
                <div class="d-flex align-items-center flex-grow-1">
                    <i class="fas fa-file-alt me-2"></i>
                    <span>${file.name}</span>
                    <small class="text-muted ms-2">(${this.formatFileSize(file.size)})</small>
                </div>
            `;
            this.selectedFiles.appendChild(fileItem);
        }
    }

    /**
     * 格式化文件大小显示
     * @param {number} bytes - 文件大小（字节）
     * @returns {string} 格式化后的文件大小
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /**
     * 上传文件并提交翻译任务
     */
    async uploadAndTranslate() {
        console.log('🚀 开始上传文件并翻译...');
        
        const files = this.fileInput.files;
        if (files.length === 0) {
            this.showToast('请选择要上传的文件', 'warning');
            return;
        }
    
        console.log('📄 选择的文件数量:', files.length);
        for (let i = 0; i < files.length; i++) {
            console.log(`📄 文件 ${i+1}:`, files[i].name, files[i].size, '字节');
        }
    
        // 检查语言选择
        if (!this.fileSourceLang || !this.fileTargetLang) {
            console.error('❌ 语言选择元素缺失:', {
                sourceLang: this.fileSourceLang,
                targetLang: this.fileTargetLang
            });
            this.showToast('语言选择元素缺失', 'danger');
            return;
        }
    
        if (this.fileSourceLang.value === this.fileTargetLang.value) {
            this.showToast('源语言和目标语言不能相同', 'warning');
            return;
        }
    
        console.log('🌐 语言选择:', {
            source: this.fileSourceLang.value,
            target: this.fileTargetLang.value,
            viaEng: this.fileViaEnglish.checked
        });
    
        // 验证文件大小
        const maxFileSize = 10 * 1024 * 1024; // 10MB
        for (let file of files) {
            if (file.size > maxFileSize) {
                this.showToast(`文件 ${file.name} 过大: ${(file.size / 1024 / 1024).toFixed(2)}MB，最大允许10MB`, 'danger');
                return;
            }
        }
    
        this.setUploadLoading(true);
    
        try {
            // === 第一步：上传文件 ===
            this.showUploadProgress('正在上传文件...');
            
            const uploadFormData = new FormData();
            for (let file of files) {
                const safeFileName = encodeURIComponent(file.name);
                uploadFormData.append('files', file, safeFileName);
            }
    
            // 上传文件请求
            const uploadResponse = await fetch('/uploadfiles', {
                method: 'POST',
                body: uploadFormData,
                headers: { 'Accept': 'application/json' }
            });
    
            if (!uploadResponse.ok) {
                const errorData = await uploadResponse.json().catch(() => ({}));
                const errorMessage = errorData.message || `文件上传失败 (${uploadResponse.status})`;
                throw new Error(errorMessage);
            }
    
            const uploadData = await uploadResponse.json();
            console.log('✅ 文件上传成功:', uploadData);
            
            if (!uploadData.client_id) {
                throw new Error('未获取到客户端ID');
            }
            const clientId = uploadData.client_id;
    
            // === 第二步：提交翻译任务 ===
            this.showUploadProgress('文件上传成功，正在提交翻译任务...');
            
            const taskFormData = new FormData();
            taskFormData.append('client_id', clientId);
            taskFormData.append('source_lang', this.fileSourceLang.value);
            taskFormData.append('target_lang', this.fileTargetLang.value);
            taskFormData.append('via_eng', this.fileViaEnglish.checked);
    
            // 提交翻译任务请求
            const taskResponse = await fetch('/submit_translation_task', {
                method: 'POST',
                body: taskFormData,
                headers: { 'Accept': 'application/json' }
            });
    
            console.log('📊 翻译任务响应状态:', taskResponse.status, taskResponse.statusText);
    
            if (!taskResponse.ok) {
                const errorData = await taskResponse.json().catch(() => ({}));
                const errorMessage = errorData.message || `翻译任务提交失败 (${taskResponse.status})`;
                
                // 处理特定错误
                if (taskResponse.status === 555) {
                    this.showToast('服务器繁忙，请稍后重试', 'warning');
                } else {
                    this.showToast(`翻译任务提交失败: ${errorMessage}`, 'danger');
                }
                return;
            }
    
            const taskData = await taskResponse.json();
            console.log('✅ 翻译任务提交成功:', taskData);
            
            if (!taskData.task_id) {
                throw new Error('翻译任务创建失败');
            }
    
            // 显示任务状态
            this.currentTaskId = taskData.task_id;
            this.showTaskStatus();
            this.showToast('翻译任务已开始', 'success');
            
        } catch (error) {
            console.error('❌ 上传或翻译失败:', error);
            this.showToast('操作失败: ' + error.message, 'danger');
        } finally {
            this.setUploadLoading(false);
            this.hideUploadProgress();
        }
    }

    /**
     * 设置上传按钮状态
     * @param {boolean} loading - 是否处于加载状态
     */
    setUploadLoading(loading) {
        if (loading) {
            this.uploadTranslateBtn.disabled = true;
            this.uploadTranslateBtn.innerHTML = '<span class="loading-spinner"></span> 处理中...';
        } else {
            this.uploadTranslateBtn.disabled = false;
            this.uploadTranslateBtn.innerHTML = '<i class="fas fa-upload"></i> 上传并翻译';
        }
    }

    /**
     * 显示任务状态面板
     */
    showTaskStatus() {
        this.taskStatus.style.display = 'block';
        this.taskId.textContent = this.currentTaskId;
        this.updateTaskStatus('处理中', 'processing', 25);
        
        // 开始定期检查状态
        this.startStatusCheck();
    }

    /**
     * 开始定期检查任务状态
     */
    startStatusCheck() {
        this.checkTaskStatus();
        this.statusCheckInterval = setInterval(() => {
            this.checkTaskStatus();
        }, 3000);
    }

    /**
     * 检查任务状态
     */
    async checkTaskStatus() {
        if (!this.currentTaskId) return;

        try {
            const response = await fetch(`/task_status?task_id=${encodeURIComponent(this.currentTaskId)}`);
            const data = await response.json();
            
            if (data.result) {
                this.handleStatusUpdate(data.result);
            }
        } catch (error) {
            console.error('状态检查失败:', error);
        }
    }

    /**
     * 处理状态更新
     * @param {string} status - 任务状态
     */
    handleStatusUpdate(status) {
        switch (status.toLowerCase()) {
            case '处理中':
            case 'processing':
                this.updateTaskStatus('处理中', 'processing', 50);
                break;
            case '完成':
            case 'completed':
                this.updateTaskStatus('已完成', 'completed', 100);
                this.showDownloadButton();
                this.stopStatusCheck();
                this.showToast('翻译任务完成，可以下载结果', 'success');
                break;
            case 'downloaded':
                this.updateTaskStatus('已下载', 'completed', 100);
                this.showDownloadButton();
                this.stopStatusCheck();
                break;
            case '错误':
            case 'error':
                this.updateTaskStatus('翻译失败', 'error', 0);
                this.stopStatusCheck();
                this.showToast('翻译任务失败，请重试', 'danger');
                break;
            default:
                this.updateTaskStatus('等待中', 'pending', 10);
                break;
        }
    }

    /**
     * 更新任务状态显示
     * @param {string} text - 状态文本
     * @param {string} type - 状态类型
     * @param {number} progress - 进度百分比
     */
    updateTaskStatus(text, type, progress) {
        this.statusBadge.className = `status-badge status-${type}`;
        this.statusBadge.innerHTML = `
            <i class="fas ${this.getStatusIcon(type)}"></i>
            ${text}
        `;
        this.progressFill.style.width = `${progress}%`;
        this.progressText.textContent = `${progress}%`;
        
        // 当进度达到100%时，添加completed类，停止动画
        if (progress >= 100) {
            this.progressFill.classList.add('completed');
        } else {
            this.progressFill.classList.remove('completed');
        }
    }

    /**
     * 获取状态对应的图标
     * @param {string} type - 状态类型
     * @returns {string} 图标类名
     */
    getStatusIcon(type) {
        const icons = {
            pending: 'fa-clock',
            processing: 'fa-spinner fa-spin',
            completed: 'fa-check-circle',
            error: 'fa-exclamation-circle'
        };
        return icons[type] || 'fa-clock';
    }

    /**
     * 显示下载按钮
     */
    showDownloadButton() {
        this.downloadBtn.style.display = 'inline-block';
        this.downloadBtn.href = `/download-all?task_id=${encodeURIComponent(this.currentTaskId)}`;
    }

    /**
     * 停止状态检查
     */
    stopStatusCheck() {
        if (this.statusCheckInterval) {
            clearInterval(this.statusCheckInterval);
            this.statusCheckInterval = null;
        }
    }

    /**
     * 显示上传进度
     * @param {string} message - 进度消息
     */
    showUploadProgress(message) {
        // 创建或更新进度显示
        let progressDiv = document.getElementById('uploadProgress');
        if (!progressDiv) {
            progressDiv = document.createElement('div');
            progressDiv.id = 'uploadProgress';
            progressDiv.className = 'upload-progress';
            progressDiv.innerHTML = `
                <div class="progress-container">
                    <div class="progress-bar">
                        <div class="progress-fill"></div>
                    </div>
                    <div class="progress-text">${message}</div>
                </div>
            `;
            
            // 插入到文件上传区域下方
            this.fileUploadArea.parentNode.insertBefore(progressDiv, this.fileUploadArea.nextSibling);
        } else {
            progressDiv.querySelector('.progress-text').textContent = message;
        }
        
        progressDiv.style.display = 'block';
    }

    /**
     * 隐藏上传进度
     */
    hideUploadProgress() {
        const progressDiv = document.getElementById('uploadProgress');
        if (progressDiv) {
            progressDiv.style.display = 'none';
        }
    }
}

// 页面加载完成后初始化应用
document.addEventListener('DOMContentLoaded', () => {
    new TranslatorApp();
});

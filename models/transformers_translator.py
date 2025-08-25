#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Transformers翻译器实现
作为ctranslate2的替代方案，提供更简单的API和更好的兼容性
"""

import logging
import threading
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

# 配置日志
logger = logging.getLogger(__name__)


class TaskType(Enum):
    """任务类型枚举"""
    TEXT = "text"
    FILE = "file"


@dataclass
class TranslationResult:
    """翻译结果数据类"""
    source_text: str
    translated_text: str
    source_lang: str
    target_lang: str
    processing_time: float
    task_type: TaskType
    success: bool
    error_message: Optional[str] = None


class TransformersTranslator:
    """使用Transformers的翻译器"""
    
    def __init__(self, model_name: str, device: str = "cpu"):
        """
        初始化翻译器
        
        Args:
            model_name: 模型名称或路径
            device: 设备类型 ("cpu", "cuda", "cuda:0" 等)
        """
        self.model_name = model_name
        self.device = device
        self.model = None
        self.tokenizer = None
        self._lock = threading.Lock()
        self._initialized = False
        
        # 性能统计
        self.total_requests = 0
        self.successful_requests = 0
        self.total_processing_time = 0.0
        
        logger.info(f"🚀 初始化Transformers翻译器: {model_name} on {device}")
    
    def _ensure_initialized(self):
        """确保模型已初始化"""
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    self._load_model()
    
    def _load_model(self):
        """加载模型和tokenizer"""
        try:
            logger.info(f"📥 加载模型: {self.model_name}")
            
            from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
            import torch
            
            # 加载tokenizer
            start_time = time.time()
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            tokenizer_time = time.time() - start_time
            logger.info(f"✅ Tokenizer加载完成，耗时: {tokenizer_time:.2f}秒")
            
            # 加载模型
            start_time = time.time()
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if self.device != "cpu" else torch.float32,
                low_cpu_mem_usage=True
            )
            
            # 移动到指定设备
            if self.device != "cpu":
                self.model = self.model.to(self.device)
            
            model_time = time.time() - start_time
            logger.info(f"✅ 模型加载完成，耗时: {model_time:.2f}秒")
            
            self._initialized = True
            logger.info(f"🎉 Transformers翻译器初始化完成！")
            
        except Exception as e:
            logger.error(f"❌ 模型加载失败: {e}")
            raise RuntimeError(f"无法加载模型 {self.model_name}: {e}")
    
    def translate_text(self, text: str, source_lang: str, target_lang: str, 
                      task_type: TaskType = TaskType.TEXT) -> TranslationResult:
        """
        翻译单个文本
        
        Args:
            text: 源文本
            source_lang: 源语言代码
            target_lang: 目标语言代码
            task_type: 任务类型
            
        Returns:
            TranslationResult: 翻译结果
        """
        start_time = time.time()
        self.total_requests += 1
        
        try:
            self._ensure_initialized()
            
            # 构建目标语言前缀
            target_prefix = self._get_target_prefix(target_lang)
            
            # 编码输入
            inputs = self.tokenizer(
                text, 
                return_tensors="pt", 
                padding=True, 
                truncation=True, 
                max_length=512
            )
            
            # 移动到设备
            if self.device != "cpu":
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # 生成翻译
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=512,
                    num_beams=5,
                    early_stopping=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    do_sample=False
                )
            
            # 解码输出
            translated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # 移除目标语言前缀（如果存在）
            if target_prefix and translated_text.startswith(target_prefix):
                translated_text = translated_text[len(target_prefix):].strip()
            
            processing_time = time.time() - start_time
            self.successful_requests += 1
            self.total_processing_time += processing_time
            
            logger.debug(f"✅ 翻译完成: '{text[:50]}...' -> '{translated_text[:50]}...' ({processing_time:.3f}s)")
            
            return TranslationResult(
                source_text=text,
                translated_text=translated_text,
                source_lang=source_lang,
                target_lang=target_lang,
                processing_time=processing_time,
                task_type=task_type,
                success=True
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"翻译失败: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            return TranslationResult(
                source_text=text,
                translated_text="",
                source_lang=source_lang,
                target_lang=target_lang,
                processing_time=processing_time,
                task_type=task_type,
                success=False,
                error_message=error_msg
            )
    
    def translate_batch(self, texts: List[str], source_lang: str, target_lang: str,
                       task_type: TaskType = TaskType.TEXT, batch_size: int = 8) -> List[TranslationResult]:
        """
        批量翻译文本
        
        Args:
            texts: 源文本列表
            source_lang: 源语言代码
            target_lang: 目标语言代码
            task_type: 任务类型
            batch_size: 批处理大小
            
        Returns:
            List[TranslationResult]: 翻译结果列表
        """
        start_time = time.time()
        self.total_requests += len(texts)
        
        try:
            self._ensure_initialized()
            
            results = []
            target_prefix = self._get_target_prefix(target_lang)
            
            # 分批处理
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                logger.debug(f"🧪 处理批次 {i//batch_size + 1}: {len(batch_texts)} 个文本")
                
                # 编码批次
                inputs = self.tokenizer(
                    batch_texts,
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                    max_length=512
                )
                
                # 移动到设备
                if self.device != "cpu":
                    inputs = {k: v.to(self.device) for k, v in inputs.items()}
                
                # 生成翻译
                with torch.no_grad():
                    outputs = self.model.generate(
                        **inputs,
                        max_length=512,
                        num_beams=5,
                        early_stopping=True,
                        pad_token_id=self.tokenizer.eos_token_id,
                        do_sample=False
                    )
                
                # 解码输出
                for j, output in enumerate(outputs):
                    translated_text = self.tokenizer.decode(output, skip_special_tokens=True)
                    
                    # 移除目标语言前缀
                    if target_prefix and translated_text.startswith(target_prefix):
                        translated_text = translated_text[len(target_prefix):].strip()
                    
                    # 创建结果
                    result = TranslationResult(
                        source_text=batch_texts[j],
                        translated_text=translated_text,
                        source_lang=source_lang,
                        target_lang=target_lang,
                        processing_time=0.0,  # 单个文本的处理时间无法准确计算
                        task_type=task_type,
                        success=True
                    )
                    results.append(result)
            
            batch_time = time.time() - start_time
            self.successful_requests += len(texts)
            self.total_processing_time += batch_time
            
            logger.info(f"✅ 批量翻译完成: {len(texts)} 个文本，耗时: {batch_time:.3f}秒")
            return results
            
        except Exception as e:
            batch_time = time.time() - start_time
            error_msg = f"批量翻译失败: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            # 返回错误结果
            error_results = []
            for text in texts:
                result = TranslationResult(
                    source_text=text,
                    translated_text="",
                    source_lang=source_lang,
                    target_lang=target_lang,
                    processing_time=batch_time / len(texts),
                    task_type=task_type,
                    success=False,
                    error_message=error_msg
                )
                error_results.append(result)
            
            return error_results
    
    def _get_target_prefix(self, target_lang: str) -> str:
        """获取目标语言前缀"""
        # NLLB模型的语言前缀映射
        lang_prefixes = {
            "cmn_Hans": "cmn_Hans",
            "cmn_Hant": "cmn_Hant", 
            "eng_Latn": "eng_Latn",
            "mon_Cyrl": "mon_Cyrl",
            "mon_Mong": "mon_Mong"
        }
        return lang_prefixes.get(target_lang, "")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        avg_time = (self.total_processing_time / self.successful_requests 
                   if self.successful_requests > 0 else 0.0)
        
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.total_requests - self.successful_requests,
            "success_rate": (self.successful_requests / self.total_requests 
                           if self.total_requests > 0 else 0.0),
            "total_processing_time": self.total_processing_time,
            "average_processing_time": avg_time,
            "model_name": self.model_name,
            "device": self.device,
            "initialized": self._initialized
        }
    
    def cleanup(self):
        """清理资源"""
        try:
            if self.model is not None:
                del self.model
                self.model = None
            
            if self.tokenizer is not None:
                del self.tokenizer
                self.tokenizer = None
            
            self._initialized = False
            logger.info("🧹 Transformers翻译器资源清理完成")
            
        except Exception as e:
            logger.warning(f"⚠️  清理资源时出错: {e}")


class TransformersTranslatorPool:
    """Transformers翻译器池"""
    
    def __init__(self, model_name: str, pool_size: int = 4, device: str = "cpu"):
        """
        初始化翻译器池
        
        Args:
            model_name: 模型名称
            pool_size: 池大小
            device: 设备类型
        """
        self.model_name = model_name
        self.pool_size = pool_size
        self.device = device
        self.translators = []
        self._lock = threading.Lock()
        self._initialized = False
        
        logger.info(f"🏊 初始化Transformers翻译器池: {pool_size} 个实例")
    
    def initialize(self):
        """初始化翻译器池"""
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    logger.info(f"🚀 创建 {self.pool_size} 个翻译器实例...")
                    
                    for i in range(self.pool_size):
                        translator = TransformersTranslator(
                            model_name=self.model_name,
                            device=self.device
                        )
                        self.translators.append(translator)
                    
                    self._initialized = True
                    logger.info(f"✅ 翻译器池初始化完成")
    
    def get_translator(self) -> TransformersTranslator:
        """获取一个可用的翻译器"""
        self.initialize()
        
        with self._lock:
            if not self.translators:
                raise RuntimeError("翻译器池为空")
            
            # 简单的轮询分配
            translator = self.translators.pop(0)
            self.translators.append(translator)
            return translator
    
    def translate_text(self, text: str, source_lang: str, target_lang: str,
                      task_type: TaskType = TaskType.TEXT) -> TranslationResult:
        """翻译单个文本"""
        translator = self.get_translator()
        return translator.translate_text(text, source_lang, target_lang, task_type)
    
    def translate_batch(self, texts: List[str], source_lang: str, target_lang: str,
                       task_type: TaskType = TaskType.TEXT, batch_size: int = 8) -> List[TranslationResult]:
        """批量翻译文本"""
        translator = self.get_translator()
        return translator.translate_batch(texts, source_lang, target_lang, task_type, batch_size)
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """获取池统计信息"""
        if not self.translators:
            return {"status": "未初始化", "pool_size": self.pool_size}
        
        # 汇总所有翻译器的统计信息
        total_stats = {
            "pool_size": self.pool_size,
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_processing_time": 0.0,
            "average_processing_time": 0.0
        }
        
        for translator in self.translators:
            stats = translator.get_stats()
            total_stats["total_requests"] += stats["total_requests"]
            total_stats["successful_requests"] += stats["successful_requests"]
            total_stats["failed_requests"] += stats["failed_requests"]
            total_stats["total_processing_time"] += stats["total_processing_time"]
        
        if total_stats["successful_requests"] > 0:
            total_stats["average_processing_time"] = (
                total_stats["total_processing_time"] / total_stats["successful_requests"]
            )
        
        total_stats["success_rate"] = (
            total_stats["successful_requests"] / total_stats["total_requests"]
            if total_stats["total_requests"] > 0 else 0.0
        )
        
        return total_stats
    
    def cleanup(self):
        """清理所有翻译器"""
        with self._lock:
            for translator in self.translators:
                translator.cleanup()
            self.translators.clear()
            self._initialized = False
            logger.info("🧹 翻译器池清理完成")


# 全局翻译器池实例
_translator_pool: Optional[TransformersTranslatorPool] = None


def get_translator_pool(model_name: str, pool_size: int = 4, device: str = "cpu") -> TransformersTranslatorPool:
    """获取全局翻译器池实例"""
    global _translator_pool
    
    if _translator_pool is None:
        _translator_pool = TransformersTranslatorPool(model_name, pool_size, device)
    
    return _translator_pool


def cleanup_translator_pool():
    """清理全局翻译器池"""
    global _translator_pool
    
    if _translator_pool is not None:
        _translator_pool.cleanup()
        _translator_pool = None


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    # 创建翻译器池
    pool = get_translator_pool("facebook/nllb-200-distilled-600M", pool_size=2)
    
    # 测试翻译
    test_texts = [
        "Hello, how are you?",
        "The weather is beautiful today.",
        "Machine learning is fascinating."
    ]
    
    try:
        # 单个翻译测试
        result = pool.translate_text("Hello world!", "eng_Latn", "cmn_Hans")
        print(f"单个翻译: {result}")
        
        # 批量翻译测试
        results = pool.translate_batch(test_texts, "eng_Latn", "cmn_Hans")
        print(f"批量翻译: {len(results)} 个结果")
        
        # 显示统计信息
        stats = pool.get_pool_stats()
        print(f"池统计: {stats}")
        
    finally:
        cleanup_translator_pool()

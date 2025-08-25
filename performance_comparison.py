#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能对比测试脚本
对比ctranslate2和transformers在翻译任务上的性能差异
"""

import time
import logging
import sys
import os
from typing import List, Dict, Any

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_ctranslate2_performance(model_path: str, test_texts: List[str], batch_size: int = 8) -> Dict[str, Any]:
    """测试ctranslate2性能"""
    try:
        import ctranslate2
        
        logger.info("🧪 测试ctranslate2性能...")
        
        # 加载模型
        start_time = time.time()
        translator = ctranslate2.Translator(
            model_path,
            device="cpu",  # 使用CPU进行公平对比
            inter_threads=4,
            intra_threads=1
        )
        load_time = time.time() - start_time
        logger.info(f"✅ ctranslate2模型加载时间: {load_time:.2f}秒")
        
        # 测试推理性能
        start_time = time.time()
        
        # 批处理翻译
        if batch_size > 1:
            # 分批处理
            all_results = []
            for i in range(0, len(test_texts), batch_size):
                batch = test_texts[i:i + batch_size]
                results = translator.translate_batch(batch, target_prefix=["cmn_Hans"])
                all_results.extend(results)
        else:
            # 单句处理
            all_results = []
            for text in test_texts:
                result = translator.translate(text, target_prefix="cmn_Hans")
                all_results.append(result)
        
        inference_time = time.time() - start_time
        
        # 计算性能指标
        total_chars = sum(len(text) for text in test_texts)
        chars_per_second = total_chars / inference_time if inference_time > 0 else 0
        
        logger.info(f"✅ ctranslate2推理时间: {inference_time:.2f}秒")
        logger.info(f"✅ 处理字符数: {total_chars}")
        logger.info(f"✅ 字符/秒: {chars_per_second:.0f}")
        
        return {
            "success": True,
            "load_time": load_time,
            "inference_time": inference_time,
            "total_chars": total_chars,
            "chars_per_second": chars_per_second,
            "results": all_results
        }
        
    except Exception as e:
        logger.error(f"❌ ctranslate2性能测试失败: {e}")
        return {"success": False, "error": str(e)}


def test_transformers_performance(model_name: str, test_texts: List[str], batch_size: int = 8) -> Dict[str, Any]:
    """测试transformers性能"""
    try:
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        import torch
        
        logger.info("🧪 测试transformers性能...")
        
        # 加载模型和tokenizer
        start_time = time.time()
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        load_time = time.time() - start_time
        logger.info(f"✅ transformers模型加载时间: {load_time:.2f}秒")
        
        # 测试推理性能
        start_time = time.time()
        
        # 批处理翻译
        if batch_size > 1:
            # 分批处理
            all_results = []
            for i in range(0, len(test_texts), batch_size):
                batch = test_texts[i:i + batch_size]
                
                # 编码
                inputs = tokenizer(batch, return_tensors="pt", padding=True, truncation=True, max_length=512)
                
                # 推理
                with torch.no_grad():
                    outputs = model.generate(
                        **inputs,
                        max_length=512,
                        num_beams=5,
                        early_stopping=True,
                        pad_token_id=tokenizer.eos_token_id
                    )
                
                # 解码
                results = [tokenizer.decode(output, skip_special_tokens=True) for output in outputs]
                all_results.extend(results)
        else:
            # 单句处理
            all_results = []
            for text in test_texts:
                inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
                
                with torch.no_grad():
                    outputs = model.generate(
                        **inputs,
                        max_length=512,
                        num_beams=5,
                        early_stopping=True,
                        pad_token_id=tokenizer.eos_token_id
                    )
                
                result = tokenizer.decode(outputs[0], skip_special_tokens=True)
                all_results.append(result)
        
        inference_time = time.time() - start_time
        
        # 计算性能指标
        total_chars = sum(len(text) for text in test_texts)
        chars_per_second = total_chars / inference_time if inference_time > 0 else 0
        
        logger.info(f"✅ transformers推理时间: {inference_time:.2f}秒")
        logger.info(f"✅ 处理字符数: {total_chars}")
        logger.info(f"✅ 字符/秒: {chars_per_second:.0f}")
        
        return {
            "success": True,
            "load_time": load_time,
            "inference_time": inference_time,
            "total_chars": total_chars,
            "chars_per_second": chars_per_second,
            "results": all_results
        }
        
    except Exception as e:
        logger.error(f"❌ transformers性能测试失败: {e}")
        return {"success": False, "error": str(e)}


def generate_test_texts() -> List[str]:
    """生成测试文本"""
    test_texts = [
        "Hello, how are you today?",
        "The weather is beautiful today.",
        "Machine learning is an exciting field.",
        "Natural language processing helps computers understand human language.",
        "Translation is the process of converting text from one language to another.",
        "Artificial intelligence is transforming many industries.",
        "Deep learning models can achieve remarkable performance on various tasks.",
        "The development of neural networks has revolutionized computer science.",
        "Computational linguistics combines linguistics and computer science.",
        "Modern translation systems use sophisticated algorithms and large datasets."
    ]
    return test_texts


def compare_performance(ctranslate2_result: Dict[str, Any], transformers_result: Dict[str, Any]) -> None:
    """对比性能结果"""
    logger.info(f"\n{'='*60}")
    logger.info("性能对比结果")
    logger.info(f"{'='*60}")
    
    if not ctranslate2_result["success"] or not transformers_result["success"]:
        logger.error("❌ 无法完成性能对比，因为某个测试失败")
        return
    
    # 加载时间对比
    c2_load = ctranslate2_result["load_time"]
    tf_load = transformers_result["load_time"]
    load_ratio = tf_load / c2_load if c2_load > 0 else float('inf')
    
    logger.info(f"📊 模型加载时间对比:")
    logger.info(f"  - ctranslate2: {c2_load:.2f}秒")
    logger.info(f"  - transformers: {tf_load:.2f}秒")
    logger.info(f"  - 比例: transformers/ctranslate2 = {load_ratio:.2f}x")
    
    # 推理时间对比
    c2_inference = ctranslate2_result["inference_time"]
    tf_inference = transformers_result["inference_time"]
    inference_ratio = tf_inference / c2_inference if c2_inference > 0 else float('inf')
    
    logger.info(f"\n📊 推理性能对比:")
    logger.info(f"  - ctranslate2: {c2_inference:.2f}秒")
    logger.info(f"  - transformers: {tf_inference:.2f}秒")
    logger.info(f"  - 比例: transformers/ctranslate2 = {inference_ratio:.2f}x")
    
    # 字符处理速度对比
    c2_speed = ctranslate2_result["chars_per_second"]
    tf_speed = transformers_result["chars_per_second"]
    speed_ratio = c2_speed / tf_speed if tf_speed > 0 else float('inf')
    
    logger.info(f"\n📊 处理速度对比:")
    logger.info(f"  - ctranslate2: {c2_speed:.0f} 字符/秒")
    logger.info(f"  - transformers: {tf_speed:.0f} 字符/秒")
    logger.info(f"  - 比例: ctranslate2/transformers = {speed_ratio:.2f}x")
    
    # 总结
    logger.info(f"\n🎯 性能总结:")
    if inference_ratio > 2.0:
        logger.info(f"✅ ctranslate2 显著更快 ({inference_ratio:.1f}x)")
    elif inference_ratio > 1.5:
        logger.info(f"✅ ctranslate2 明显更快 ({inference_ratio:.1f}x)")
    elif inference_ratio > 1.2:
        logger.info(f"✅ ctranslate2 稍快 ({inference_ratio:.1f}x)")
    else:
        logger.info(f"ℹ️  性能差异不大 ({inference_ratio:.1f}x)")
    
    # 建议
    logger.info(f"\n💡 建议:")
    if inference_ratio > 2.0:
        logger.info("  - 强烈推荐使用 ctranslate2，性能提升显著")
    elif inference_ratio > 1.5:
        logger.info("  - 推荐使用 ctranslate2，性能提升明显")
    elif inference_ratio > 1.2:
        logger.info("  - 可以考虑使用 ctranslate2，性能略有提升")
    else:
        logger.info("  - 性能差异不大，可以根据易用性选择")
        logger.info("  - 如果 ctranslate2 配置复杂，使用 transformers 也是不错的选择")


def main():
    """主函数"""
    logger.info("🚀 开始性能对比测试...")
    
    # 生成测试文本
    test_texts = generate_test_texts()
    logger.info(f"📝 测试文本数量: {len(test_texts)}")
    
    # 获取模型路径
    try:
        from utils.config_manager import config_manager
        model_name = config_manager.get("SETTINGS", "SEQ_TRANSLATE_MODEL")
        model_path = config_manager.get_model_path(model_name)
        
        logger.info(f"🔍 使用模型: {model_name}")
        logger.info(f"🔍 模型路径: {model_path}")
        
    except Exception as e:
        logger.error(f"❌ 获取模型配置失败: {e}")
        logger.info("💡 请确保配置文件正确，或者手动指定模型路径")
        return 1
    
    # 测试ctranslate2性能
    logger.info(f"\n{'='*50}")
    c2_result = test_ctranslate2_performance(model_path, test_texts, batch_size=8)
    
    # 测试transformers性能
    logger.info(f"\n{'='*50}")
    tf_result = test_transformers_performance(model_name, test_texts, batch_size=8)
    
    # 对比性能
    if c2_result["success"] and tf_result["success"]:
        compare_performance(c2_result, tf_result)
        
        # 保存结果到文件
        with open("performance_comparison_results.txt", "w", encoding="utf-8") as f:
            f.write("性能对比测试结果\n")
            f.write("=" * 50 + "\n")
            f.write(f"ctranslate2 推理时间: {c2_result['inference_time']:.2f}秒\n")
            f.write(f"transformers 推理时间: {tf_result['inference_time']:.2f}秒\n")
            f.write(f"性能比例: transformers/ctranslate2 = {tf_result['inference_time']/c2_result['inference_time']:.2f}x\n")
        
        logger.info(f"\n💾 详细结果已保存到: performance_comparison_results.txt")
        
        return 0
    else:
        logger.error("❌ 性能测试失败，无法完成对比")
        return 1


if __name__ == "__main__":
    exit(main())

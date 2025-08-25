#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试NLLB官方语言代码修复
"""

import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def test_nllb_language_codes():
    """测试NLLB官方语言代码"""
    try:
        logger.info("🧪 测试NLLB官方语言代码映射...")
        
        from models.translateModel import TranslatorSingleton
        
        # NLLB官方语言代码
        nllb_codes = {
            "English": "eng_Latn",
            "Chinese (Simplified)": "zho_Hans", 
            "Halh Mongolian": "khk_Cyrl"
        }
        
        # 前端语言代码到NLLB的映射
        frontend_mapping = {
            "zh_Hans": "zho_Hans",      # 中文简体
            "eng_Latn": "eng_Latn",     # 英语
            "khk_Cyrl": "khk_Cyrl",     # 西里尔蒙文
        }
        
        logger.info("📋 NLLB官方语言代码:")
        for lang_name, code in nllb_codes.items():
            logger.info(f"  {lang_name}: {code}")
        
        logger.info("\n🔄 前端到NLLB的映射:")
        for frontend_code, expected_nllb in frontend_mapping.items():
            mapped_code = TranslatorSingleton._map_language_code(frontend_code)
            if mapped_code == expected_nllb:
                logger.info(f"  ✅ {frontend_code} -> {mapped_code}")
            else:
                logger.error(f"  ❌ {frontend_code} -> {mapped_code} (期望: {expected_nllb})")
                return False
        
        logger.info("\n🎯 测试翻译方向:")
        test_directions = [
            ("eng_Latn", "zho_Hans", "英语 -> 中文"),
            ("zho_Hans", "eng_Latn", "中文 -> 英语"),
            ("khk_Cyrl", "zho_Hans", "蒙文 -> 中文"),
        ]
        
        for src, tgt, desc in test_directions:
            mapped_src = TranslatorSingleton._map_language_code(src)
            mapped_tgt = TranslatorSingleton._map_language_code(tgt)
            logger.info(f"  {desc}: {mapped_src} -> {mapped_tgt}")
        
        logger.info("\n✅ NLLB语言代码映射测试通过！")
        logger.info("🚀 现在可以启动服务器进行翻译测试了！")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ NLLB语言代码测试失败: {e}")
        return False


def main():
    """主函数"""
    logger.info("🚀 开始测试NLLB官方语言代码修复...")
    
    if test_nllb_language_codes():
        logger.info("\n🎉 所有测试都通过了！")
        logger.info("💡 语言代码映射已修复为NLLB官方格式！")
        return 0
    else:
        logger.error("\n❌ 测试失败，请检查问题。")
        return 1


if __name__ == "__main__":
    exit(main())

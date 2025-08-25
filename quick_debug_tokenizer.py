#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速调试tokenizer问题
"""

import logging
import sys
import os

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def debug_tokenizer_directly():
    """直接调试tokenizer"""
    try:
        logger.info("🔍 直接调试tokenizer...")
        
        # 尝试导入必要的模块
        try:
            import transformers
            logger.info(f"✅ transformers版本: {transformers.__version__}")
        except ImportError as e:
            logger.error(f"❌ transformers导入失败: {e}")
            return False
        
        # 尝试加载tokenizer
        try:
            from models.translateModel import TranslatorSingleton
            
            # 加载tokenizer
            tokenizer = TranslatorSingleton._load_tokenizer("eng_Latn")
            logger.info(f"✅ Tokenizer类型: {type(tokenizer)}")
            logger.info(f"✅ Tokenizer类: {tokenizer.__class__.__name__}")
            
            # 检查tokenizer的方法
            methods = [method for method in dir(tokenizer) if not method.startswith('_')]
            logger.info(f"✅ Tokenizer方法: {methods[:15]}...")
            
            # 测试简单的encode
            test_text = "Hello world"
            logger.info(f"\n--- 测试文本: '{test_text}' ---")
            
            # 直接调用encode
            raw_result = tokenizer.encode(test_text)
            logger.info(f"原始encode结果: 类型={type(raw_result)}")
            logger.info(f"原始encode值: {raw_result}")
            
            # 检查结果的详细信息
            if hasattr(raw_result, '__iter__'):
                logger.info(f"结果是可迭代的，长度: {len(raw_result) if hasattr(raw_result, '__len__') else '未知'}")
                logger.info(f"前5个元素: {list(raw_result)[:5]}")
                logger.info(f"元素类型: {[type(x) for x in list(raw_result)[:5]]}")
            else:
                logger.info(f"结果不是可迭代的")
            
            # 尝试强制转换为列表
            try:
                token_list = list(raw_result)
                logger.info(f"强制转换为列表成功: {token_list[:5]}...")
                
                # 检查每个元素
                for i, item in enumerate(token_list[:5]):
                    logger.info(f"元素{i}: 值={item}, 类型={type(item)}")
                    if isinstance(item, str):
                        logger.warning(f"⚠️  元素{i}是字符串: {item}")
                        try:
                            # 尝试转换为整数
                            int_item = int(item)
                            logger.info(f"✅ 字符串'{item}'成功转换为整数: {int_item}")
                        except ValueError as e:
                            logger.error(f"❌ 字符串'{item}'无法转换为整数: {e}")
                
                # 尝试convert_ids_to_tokens
                try:
                    tokens = tokenizer.convert_ids_to_tokens(token_list)
                    logger.info(f"✅ convert_ids_to_tokens成功: {tokens[:5]}...")
                except Exception as e:
                    logger.error(f"❌ convert_ids_to_tokens失败: {e}")
                    
                    # 尝试逐个转换
                    logger.info("尝试逐个转换...")
                    for i, token_id in enumerate(token_list[:5]):
                        try:
                            single_token = tokenizer.convert_ids_to_tokens([token_id])
                            logger.info(f"✅ 单个ID {token_id} -> {single_token}")
                        except Exception as e2:
                            logger.error(f"❌ 单个ID {token_id} 转换失败: {e2}")
                            logger.error(f"   类型: {type(token_id)}")
                            
            except Exception as e:
                logger.error(f"❌ 强制转换失败: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Tokenizer加载失败: {e}")
            return False
        
    except Exception as e:
        logger.error(f"❌ 直接调试失败: {e}")
        return False


def check_config_files():
    """检查配置文件"""
    try:
        logger.info("🔍 检查配置文件...")
        
        # 检查config.ini
        if os.path.exists("config/config.ini"):
            logger.info("✅ config/config.ini 存在")
            
            # 读取关键配置
            import configparser
            config = configparser.ConfigParser()
            config.read("config/config.ini")
            
            if "SETTINGS" in config:
                model_name = config.get("SETTINGS", "SEQ_TRANSLATE_MODEL", fallback="未设置")
                logger.info(f"模型名称: {model_name}")
            
            if "MODEL_LIST" in config:
                logger.info("模型列表配置:")
                for key, value in config.items("MODEL_LIST"):
                    logger.info(f"  {key} = {value}")
            
            if "TOKENIZER_LIST" in config:
                logger.info("Tokenizer列表配置:")
                for key, value in config.items("TOKENIZER_LIST"):
                    logger.info(f"  {key} = {value}")
        else:
            logger.error("❌ config/config.ini 不存在")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 配置文件检查失败: {e}")
        return False


def main():
    """主函数"""
    logger.info("🚀 开始快速调试...")
    
    tests = [
        ("配置文件检查", check_config_files),
        ("直接调试", debug_tokenizer_directly)
    ]
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"测试项目: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = test_func()
            if result:
                logger.info(f"✅ {test_name} 完成")
            else:
                logger.error(f"❌ {test_name} 失败")
        except Exception as e:
            logger.error(f"❌ {test_name} 异常: {e}")
    
    logger.info("\n🔍 调试完成，请检查上面的输出信息")


if __name__ == "__main__":
    main()

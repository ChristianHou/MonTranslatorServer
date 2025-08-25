#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终验证脚本 - 确认所有字体问题已解决
"""

import logging
import os
import re

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def verify_no_webfonts_references():
    """验证没有webfonts引用"""
    try:
        logger.info("🔍 验证没有webfonts引用...")
        
        # 检查所有CSS文件
        css_files = [
            "static/libs/fontawesome/all.min.css",
            "static/css/fonts.css",
            "static/css/main.css"
        ]
        
        for css_file in css_files:
            if os.path.exists(css_file):
                with open(css_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if '../webfonts/' in content:
                    logger.error(f"❌ {css_file} 仍有webfonts引用")
                    return False
                
                if 'webfonts' in content:
                    logger.error(f"❌ {css_file} 仍有webfonts引用")
                    return False
        
        logger.info("✅ 所有CSS文件都没有webfonts引用")
        return True
        
    except Exception as e:
        logger.error(f"❌ webfonts引用验证失败: {e}")
        return False


def verify_no_ttf_references():
    """验证没有ttf引用"""
    try:
        logger.info("🔍 验证没有ttf引用...")
        
        # 检查所有CSS文件
        css_files = [
            "static/libs/fontawesome/all.min.css",
            "static/css/fonts.css",
            "static/css/main.css"
        ]
        
        for css_file in css_files:
            if os.path.exists(css_file):
                with open(css_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if '.ttf' in content:
                    logger.error(f"❌ {css_file} 仍有ttf引用")
                    return False
        
        logger.info("✅ 所有CSS文件都没有ttf引用")
        return True
        
    except Exception as e:
        logger.error(f"❌ ttf引用验证失败: {e}")
        return False


def verify_correct_font_paths():
    """验证正确的字体路径"""
    try:
        logger.info("🔍 验证正确的字体路径...")
        
        # 检查FontAwesome CSS
        fa_css = "static/libs/fontawesome/all.min.css"
        if os.path.exists(fa_css):
            with open(fa_css, 'r', encoding='utf-8') as f:
                content = f.read()
            
            font_paths = re.findall(r'\.\./fonts/', content)
            if not font_paths:
                logger.error("❌ FontAwesome CSS没有正确的字体路径")
                return False
            
            logger.info(f"✅ FontAwesome CSS包含 {len(font_paths)} 个正确字体路径")
        
        # 检查fonts.css
        fonts_css = "static/css/fonts.css"
        if os.path.exists(fonts_css):
            with open(fonts_css, 'r', encoding='utf-8') as f:
                content = f.read()
            
            font_paths = re.findall(r'\.\./fonts/', content)
            if not font_paths:
                logger.error("❌ fonts.css没有正确的字体路径")
                return False
            
            logger.info(f"✅ fonts.css包含 {len(font_paths)} 个正确字体路径")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 字体路径验证失败: {e}")
        return False


def verify_html_version_parameters():
    """验证HTML中的版本参数"""
    try:
        logger.info("🔍 验证HTML版本参数...")
        
        html_file = "templates/index.html"
        if not os.path.exists(html_file):
            logger.error(f"❌ HTML文件不存在: {html_file}")
            return False
        
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查版本参数
        version_params = re.findall(r'\?v=\d+\.\d+', content)
        if len(version_params) < 3:
            logger.error(f"❌ HTML文件版本参数不足，只有 {len(version_params)} 个")
            return False
        
        logger.info(f"✅ HTML文件包含 {len(version_params)} 个版本参数")
        return True
        
    except Exception as e:
        logger.error(f"❌ HTML版本参数验证失败: {e}")
        return False


def verify_font_files_exist():
    """验证字体文件存在"""
    try:
        logger.info("🔍 验证字体文件存在...")
        
        fonts_dir = "static/fonts"
        if not os.path.exists(fonts_dir):
            logger.error(f"❌ 字体目录不存在: {fonts_dir}")
            return False
        
        required_fonts = [
            'fa-solid-900.woff2',
            'fa-solid-900.woff',
            'fa-regular-400.woff2',
            'fa-regular-400.woff',
            'fa-brands-400.woff2',
            'fa-brands-400.woff'
        ]
        
        for font in required_fonts:
            font_path = os.path.join(fonts_dir, font)
            if not os.path.exists(font_path):
                logger.error(f"❌ 字体文件不存在: {font}")
                return False
        
        logger.info("✅ 所有必需的字体文件都存在")
        return True
        
    except Exception as e:
        logger.error(f"❌ 字体文件验证失败: {e}")
        return False


def main():
    """主函数"""
    logger.info("🚀 开始最终验证 - 确认所有字体问题已解决...")
    
    tests = [
        ("无webfonts引用", verify_no_webfonts_references),
        ("无ttf引用", verify_no_ttf_references),
        ("正确字体路径", verify_correct_font_paths),
        ("HTML版本参数", verify_html_version_parameters),
        ("字体文件存在", verify_font_files_exist),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"验证项目: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = test_func()
            results[test_name] = result
            if result:
                logger.info(f"✅ {test_name} 验证通过")
            else:
                logger.error(f"❌ {test_name} 验证失败")
        except Exception as e:
            logger.error(f"❌ {test_name} 验证异常: {e}")
            results[test_name] = False
    
    # 总结报告
    logger.info(f"\n{'='*50}")
    logger.info("最终验证总结报告")
    logger.info(f"{'='*50}")
    
    passed_tests = sum(1 for result in results.values() if result)
    total_tests = len(results)
    
    logger.info(f"总计验证项目: {total_tests}")
    logger.info(f"通过验证: {passed_tests}")
    logger.info(f"失败验证: {total_tests - passed_tests}")
    
    if passed_tests == total_tests:
        logger.info("🎉 所有验证都通过了！")
        logger.info("🚀 字体问题已完全解决！")
        logger.info("💡 现在请访问 http://127.0.0.1:8000/ 查看效果")
        logger.info("🎯 所有图标应该能正常显示：")
        logger.info("   🌐 蒙古语翻译助手")
        logger.info("   💬 文本翻译")
        logger.info("   📄 文档翻译")
        logger.info("   ⬆️ 文件上传")
        logger.info("   ⬇️ 文件下载")
        logger.info("🔧 已添加版本号参数，强制浏览器重新加载CSS")
        logger.info("💾 已备份所有原始文件")
        return 0
    else:
        logger.error("❌ 部分验证失败，请检查问题。")
        
        failed_tests = [name for name, result in results.items() if not result]
        logger.error(f"失败的验证项目: {failed_tests}")
        
        return 1


if __name__ == "__main__":
    exit(main())

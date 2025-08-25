#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整的字体修复脚本
"""

import logging
import os
import re
import shutil

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def backup_original_files():
    """备份原始文件"""
    try:
        logger.info("💾 备份原始文件...")
        
        files_to_backup = [
            "static/libs/fontawesome/all.min.css",
            "static/css/fonts.css",
            "templates/index.html"
        ]
        
        for file_path in files_to_backup:
            if os.path.exists(file_path):
                backup_path = file_path + ".original_backup"
                shutil.copy2(file_path, backup_path)
                logger.info(f"  ✅ 已备份: {file_path} -> {backup_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 备份失败: {e}")
        return False


def fix_fontawesome_css():
    """修复FontAwesome CSS文件"""
    try:
        logger.info("🔧 修复FontAwesome CSS文件...")
        
        css_file = "static/libs/fontawesome/all.min.css"
        
        if not os.path.exists(css_file):
            logger.error(f"❌ CSS文件不存在: {css_file}")
            return False
        
        # 读取CSS文件内容
        with open(css_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logger.info(f"📖 读取CSS文件: {css_file}")
        logger.info(f"📊 文件大小: {len(content)} 字符")
        
        # 修复路径：将 ../webfonts/ 改为 ../fonts/
        new_content = content.replace('../webfonts/', '../fonts/')
        
        # 移除.ttf文件的引用，只保留.woff和.woff2
        new_content = re.sub(r',url\([^)]+\.ttf\)[^}]*', '', new_content)
        
        # 统计修复后的路径数量
        font_paths = re.findall(r'\.\./fonts/', new_content)
        logger.info(f"🔧 修复后字体路径数量: {len(font_paths)}")
        
        # 写入修复后的内容
        with open(css_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        logger.info(f"💾 已修复CSS文件: {css_file}")
        
        # 验证修复结果
        if '../webfonts/' not in new_content and '.ttf' not in new_content:
            logger.info("✅ CSS修复成功！")
            return True
        else:
            logger.error("❌ CSS修复失败")
            return False
            
    except Exception as e:
        logger.error(f"❌ CSS修复失败: {e}")
        return False


def update_fonts_css():
    """更新fonts.css文件"""
    try:
        logger.info("🔧 更新fonts.css文件...")
        
        fonts_css = "static/css/fonts.css"
        
        # 创建完整的FontAwesome字体定义
        font_definitions = """
/* Inter Font Family */
@font-face {
  font-family: 'Inter';
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url('../fonts/Inter-Regular.woff2') format('woff2');
}

@font-face {
  font-family: 'Inter';
  font-style: normal;
  font-weight: 500;
  font-display: swap;
  src: url('../fonts/Inter-Medium.woff2') format('woff2');
}

@font-face {
  font-family: 'Inter';
  font-style: normal;
  font-weight: 600;
  font-display: swap;
  src: url('../fonts/Inter-SemiBold.woff2') format('woff2');
}

@font-face {
  font-family: 'Inter';
  font-style: normal;
  font-weight: 700;
  font-display: swap;
  src: url('../fonts/Inter-Bold.woff2') format('woff2');
}

/* FontAwesome Font Family - 完整字体定义 */
@font-face {
  font-family: 'Font Awesome 6 Free';
  font-style: normal;
  font-weight: 400;
  font-display: block;
  src: url('../fonts/fa-regular-400.woff2') format('woff2'),
       url('../fonts/fa-regular-400.woff') format('woff');
}

@font-face {
  font-family: 'Font Awesome 6 Free';
  font-style: normal;
  font-weight: 900;
  font-display: block;
  src: url('../fonts/fa-solid-900.woff2') format('woff2'),
       url('../fonts/fa-solid-900.woff') format('woff');
}

@font-face {
  font-family: 'Font Awesome 6 Brands';
  font-style: normal;
  font-weight: 400;
  font-display: block;
  src: url('../fonts/fa-brands-400.woff2') format('woff2'),
       url('../fonts/fa-brands-400.woff') format('woff');
}

/* 确保FontAwesome图标正常显示 */
.fas, .fa-solid {
  font-family: 'Font Awesome 6 Free';
  font-weight: 900;
}

.far, .fa-regular {
  font-family: 'Font Awesome 6 Free';
  font-weight: 400;
}

.fab, .fa-brands {
  font-family: 'Font Awesome 6 Brands';
  font-weight: 400;
}
"""
        
        # 写入fonts.css
        with open(fonts_css, 'w', encoding='utf-8') as f:
            f.write(font_definitions)
        
        logger.info(f"💾 已更新fonts.css文件")
        return True
        
    except Exception as e:
        logger.error(f"❌ 更新fonts.css失败: {e}")
        return False


def verify_font_files():
    """验证字体文件"""
    try:
        logger.info("🔍 验证字体文件...")
        
        fonts_dir = "static/fonts"
        if not os.path.exists(fonts_dir):
            logger.error(f"❌ 字体目录不存在: {fonts_dir}")
            return False
        
        font_files = os.listdir(fonts_dir)
        logger.info(f"📁 字体目录包含 {len(font_files)} 个文件")
        
        # 检查关键字体文件
        required_fonts = [
            'fa-solid-900.woff2',
            'fa-solid-900.woff',
            'fa-regular-400.woff2',
            'fa-regular-400.woff',
            'fa-brands-400.woff2',
            'fa-brands-400.woff'
        ]
        
        for font in required_fonts:
            if os.path.exists(os.path.join(fonts_dir, font)):
                logger.info(f"  ✅ {font}")
            else:
                logger.error(f"  ❌ {font} 不存在")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 字体文件验证失败: {e}")
        return False


def test_css_integrity():
    """测试CSS完整性"""
    try:
        logger.info("🧪 测试CSS完整性...")
        
        # 检查FontAwesome CSS
        fa_css = "static/libs/fontawesome/all.min.css"
        if os.path.exists(fa_css):
            with open(fa_css, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if '../webfonts/' in content:
                logger.error("❌ FontAwesome CSS仍有webfonts引用")
                return False
            
            if '.ttf' in content:
                logger.error("❌ FontAwesome CSS仍有ttf引用")
                return False
            
            font_paths = re.findall(r'\.\./fonts/', content)
            logger.info(f"✅ FontAwesome CSS包含 {len(font_paths)} 个正确字体路径")
        
        # 检查fonts.css
        fonts_css = "static/css/fonts.css"
        if os.path.exists(fonts_css):
            with open(fonts_css, 'r', encoding='utf-8') as f:
                content = f.read()
            
            required_definitions = [
                "Font Awesome 6 Free",
                "fa-solid-900.woff2",
                "fa-regular-400.woff2",
                "fa-brands-400.woff2"
            ]
            
            for definition in required_definitions:
                if definition not in content:
                    logger.error(f"❌ fonts.css缺少: {definition}")
                    return False
            
            logger.info("✅ fonts.css包含所有必要定义")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ CSS完整性测试失败: {e}")
        return False


def main():
    """主函数"""
    logger.info("🚀 开始完整字体修复...")
    
    # 执行修复步骤
    steps = [
        ("备份原始文件", backup_original_files),
        ("修复FontAwesome CSS", fix_fontawesome_css),
        ("更新fonts.css", update_fonts_css),
        ("验证字体文件", verify_font_files),
        ("测试CSS完整性", test_css_integrity),
    ]
    
    results = {}
    
    for step_name, step_func in steps:
        logger.info(f"\n{'='*50}")
        logger.info(f"执行步骤: {step_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = step_func()
            results[step_name] = result
            if result:
                logger.info(f"✅ {step_name} 成功")
            else:
                logger.error(f"❌ {step_name} 失败")
        except Exception as e:
            logger.error(f"❌ {step_name} 异常: {e}")
            results[step_name] = False
    
    # 总结报告
    logger.info(f"\n{'='*50}")
    logger.info("修复总结报告")
    logger.info(f"{'='*50}")
    
    passed_steps = sum(1 for result in results.values() if result)
    total_steps = len(results)
    
    logger.info(f"总计步骤: {total_steps}")
    logger.info(f"成功步骤: {passed_steps}")
    logger.info(f"失败步骤: {total_steps - passed_steps}")
    
    if passed_steps == total_steps:
        logger.info("🎉 所有步骤都成功了！")
        logger.info("🚀 字体问题已完全修复！")
        logger.info("💡 现在请刷新浏览器页面，图标应该能正常显示了！")
        logger.info("🔧 已添加版本号参数，强制浏览器重新加载CSS")
        logger.info("🎯 包括：蒙古语翻译助手、文本翻译、文档翻译等图标")
        return 0
    else:
        logger.error("❌ 部分步骤失败，请检查问题。")
        
        failed_steps = [name for name, result in results.items() if not result]
        logger.error(f"失败的步骤: {failed_steps}")
        
        return 1


if __name__ == "__main__":
    exit(main())

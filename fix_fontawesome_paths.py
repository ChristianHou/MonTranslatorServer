#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复FontAwesome CSS文件中的字体路径
"""

import logging
import os
import re

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def fix_fontawesome_paths():
    """修复FontAwesome CSS文件中的字体路径"""
    try:
        logger.info("🔧 开始修复FontAwesome字体路径...")
        
        css_file = "static/libs/fontawesome/all.min.css"
        
        if not os.path.exists(css_file):
            logger.error(f"❌ FontAwesome CSS文件不存在: {css_file}")
            return False
        
        # 读取CSS文件内容
        with open(css_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logger.info(f"📖 读取CSS文件: {css_file}")
        logger.info(f"📊 文件大小: {len(content)} 字符")
        
        # 统计需要修复的路径数量
        old_paths = re.findall(r'\.\./webfonts/', content)
        logger.info(f"🔍 发现 {len(old_paths)} 个需要修复的路径")
        
        if not old_paths:
            logger.info("✅ 没有发现需要修复的路径")
            return True
        
        # 修复路径：将 ../webfonts/ 改为 ../fonts/
        new_content = content.replace('../webfonts/', '../fonts/')
        
        # 移除.ttf文件的引用，只保留.woff和.woff2
        new_content = re.sub(r',url\([^)]+\.ttf\)[^}]*', '', new_content)
        
        # 统计修复后的路径数量
        new_paths = re.findall(r'\.\./fonts/', new_content)
        logger.info(f"🔧 修复后路径数量: {len(new_paths)}")
        
        # 备份原文件
        backup_file = css_file + '.backup'
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"💾 已备份原文件到: {backup_file}")
        
        # 写入修复后的内容
        with open(css_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        logger.info(f"💾 已修复CSS文件: {css_file}")
        
        # 验证修复结果
        if '../webfonts/' not in new_content and '.ttf' not in new_content:
            logger.info("✅ 路径和格式修复成功！")
            return True
        else:
            logger.error("❌ 修复失败，仍有问题")
            return False
            
    except Exception as e:
        logger.error(f"❌ 修复FontAwesome路径失败: {e}")
        return False


def verify_font_files():
    """验证字体文件是否存在"""
    try:
        logger.info("🔍 验证字体文件...")
        
        # 检查字体文件目录
        fonts_dir = "static/fonts"
        if not os.path.exists(fonts_dir):
            logger.error(f"❌ 字体目录不存在: {fonts_dir}")
            return False
        
        # 列出字体文件
        font_files = os.listdir(fonts_dir)
        logger.info(f"📁 字体目录 {fonts_dir} 包含 {len(font_files)} 个文件")
        
        # 检查关键字体文件
        required_fonts = [
            'fa-solid-900.woff2',
            'fa-solid-900.woff',
            'fa-regular-400.woff2',
            'fa-regular-400.woff',
            'fa-brands-400.woff2',
            'fa-brands-400.woff'
        ]
        
        missing_fonts = []
        for font in required_fonts:
            font_path = os.path.join(fonts_dir, font)
            if os.path.exists(font_path):
                logger.info(f"  ✅ {font}")
            else:
                logger.warning(f"  ⚠️  {font} 不存在")
                missing_fonts.append(font)
        
        if missing_fonts:
            logger.warning(f"⚠️  缺少字体文件: {missing_fonts}")
            logger.info("💡 建议运行 download_static_assets.py 下载字体文件")
        
        return len(missing_fonts) == 0
        
    except Exception as e:
        logger.error(f"❌ 验证字体文件失败: {e}")
        return False


def test_icon_display():
    """测试图标显示"""
    try:
        logger.info("🧪 测试图标显示...")
        
        # 检查HTML模板中的图标使用
        html_file = "templates/index.html"
        if not os.path.exists(html_file):
            logger.error(f"❌ HTML模板文件不存在: {html_file}")
            return False
        
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 查找FontAwesome图标类
        icon_classes = re.findall(r'fa-[a-zA-Z0-9-]+', html_content)
        unique_icons = list(set(icon_classes))
        
        logger.info(f"🎨 发现 {len(unique_icons)} 个不同的图标类")
        logger.info(f"📋 图标类列表: {unique_icons[:10]}{'...' if len(unique_icons) > 10 else ''}")
        
        # 检查关键图标
        key_icons = ['fa-language', 'fa-file-text', 'fa-file-word', 'fa-file-excel']
        for icon in key_icons:
            if icon in html_content:
                logger.info(f"  ✅ {icon} 图标已使用")
            else:
                logger.warning(f"  ⚠️  {icon} 图标未使用")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试图标显示失败: {e}")
        return False


def main():
    """主函数"""
    logger.info("🚀 开始FontAwesome字体路径修复...")
    
    # 执行修复步骤
    steps = [
        ("验证字体文件", verify_font_files),
        ("修复CSS路径", fix_fontawesome_paths),
        ("测试图标显示", test_icon_display),
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
        logger.info("🚀 FontAwesome图标应该能正常显示了！")
        logger.info("💡 请刷新浏览器页面查看效果")
        return 0
    else:
        logger.error("❌ 部分步骤失败，请检查问题。")
        
        # 显示失败的步骤
        failed_steps = [name for name, result in results.items() if not result]
        logger.error(f"失败的步骤: {failed_steps}")
        
        return 1


if __name__ == "__main__":
    exit(main())

#!/usr/bin/env python3
"""
下载静态资源文件脚本
用于内网部署时替代CDN资源
"""

import os
import requests
import zipfile
from pathlib import Path

def download_file(url, local_path):
    """下载文件到本地"""
    try:
        print(f"正在下载: {url}")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # 确保目录存在
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"✓ 下载完成: {local_path}")
        return True
    except Exception as e:
        print(f"✗ 下载失败: {url} - {e}")
        return False

def download_bootstrap():
    """下载Bootstrap CSS和JS"""
    bootstrap_css = "https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css"
    bootstrap_js = "https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"
    
    download_file(bootstrap_css, "static/libs/bootstrap/bootstrap.min.css")
    download_file(bootstrap_js, "static/libs/bootstrap/bootstrap.bundle.min.js")

def download_fontawesome():
    """下载Font Awesome"""
    fa_css = "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
    
    # 下载CSS文件
    if download_file(fa_css, "static/libs/fontawesome/all.min.css"):
        # 读取CSS文件，提取字体文件URLs
        try:
            with open("static/libs/fontawesome/all.min.css", 'r', encoding='utf-8') as f:
                css_content = f.read()
            
            # 替换字体文件路径为本地路径
            css_content = css_content.replace(
                "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/",
                "../fonts/"
            )
            
            with open("static/libs/fontawesome/all.min.css", 'w', encoding='utf-8') as f:
                f.write(css_content)
                
            print("✓ Font Awesome CSS路径已本地化")
            
        except Exception as e:
            print(f"✗ 处理Font Awesome CSS失败: {e}")

def download_fonts():
    """下载字体文件"""
    font_base_url = "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/"
    fonts = [
        "fa-solid-900.woff2",
        "fa-solid-900.woff", 
        "fa-regular-400.woff2",
        "fa-regular-400.woff",
        "fa-brands-400.woff2",
        "fa-brands-400.woff"
    ]
    
    for font in fonts:
        download_file(f"{font_base_url}{font}", f"static/fonts/{font}")

def download_google_fonts():
    """下载Google Fonts - Inter字体"""
    # Inter字体的WOFF2文件
    inter_fonts = {
        "Inter-Regular.woff2": "https://fonts.gstatic.com/s/inter/v12/UcCO3FwrK3iLTeHuS_fvQtMwCp50KnMw2boKoduKmMEVuLyfAZ9hiJ-Ek-_EeA.woff2",
        "Inter-Medium.woff2": "https://fonts.gstatic.com/s/inter/v12/UcCO3FwrK3iLTeHuS_fvQtMwCp50KnMw2boKoduKmMEVuI6fAZ9hiJ-Ek-_EeA.woff2",
        "Inter-SemiBold.woff2": "https://fonts.gstatic.com/s/inter/v12/UcCO3FwrK3iLTeHuS_fvQtMwCp50KnMw2boKoduKmMEVuGKYAZ9hiJ-Ek-_EeA.woff2",
        "Inter-Bold.woff2": "https://fonts.gstatic.com/s/inter/v12/UcCO3FwrK3iLTeHuS_fvQtMwCp50KnMw2boKoduKmMEVuFuYAZ9hiJ-Ek-_EeA.woff2"
    }
    
    for filename, url in inter_fonts.items():
        download_file(url, f"static/fonts/{filename}")

def create_font_css():
    """创建本地字体CSS文件"""
    font_css = """
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
"""
    
    with open("static/css/fonts.css", 'w', encoding='utf-8') as f:
        f.write(font_css)
    print("✓ 本地字体CSS文件已创建")

def main():
    print("开始下载静态资源文件...")
    print("=" * 50)
    
    # 下载Bootstrap
    print("\n📦 下载Bootstrap...")
    download_bootstrap()
    
    # 下载Font Awesome
    print("\n🎨 下载Font Awesome...")
    download_fontawesome()
    download_fonts()
    
    # 下载Google Fonts
    print("\n🔤 下载Google Fonts...")
    download_google_fonts()
    create_font_css()
    
    print("\n" + "=" * 50)
    print("✅ 静态资源下载完成！")
    print("现在可以在内网环境中部署了。")

if __name__ == "__main__":
    main()

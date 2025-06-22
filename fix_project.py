#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de corrección automática - ECPlacas 2.0
"""
import os
import sys
import subprocess
import re

def fix_import_errors():
    """Corregir errores de import en archivos Python"""
    fixes = [
        {
            'file': 'backend/app.py',
            'old': 'from email.mime.text import MimeText',
            'new': 'from email.mime.text import MIMEText'
        }
    ]
    
    for fix in fixes:
        if os.path.exists(fix['file']):
            with open(fix['file'], 'r', encoding='utf-8') as f:
                content = f.read()
            
            content = content.replace(fix['old'], fix['new'])
            
            with open(fix['file'], 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"[OK] Fixed import in {fix['file']}")

def fix_encoding_issues():
    """Configurar encoding para Windows"""
    if sys.platform.startswith('win'):
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        os.environ['PYTHONLEGACYWINDOWSSTDIO'] = '1'
        print("[OK] Windows encoding configured")

def format_code():
    """Formatear código con Black e isort"""
    try:
        print("Formatting code with Black...")
        subprocess.run(['black', 'backend/', '--quiet'], check=False)
        
        print("Sorting imports with isort...")
        subprocess.run(['isort', 'backend/', '--quiet'], check=False)
        
        print("[OK] Code formatting completed")
    except Exception as e:
        print(f"[WARNING] Formatting failed: {e}")

def main():
    print("🔧 ECPlacas 2.0 - Auto Fix Script")
    print("=" * 50)
    
    fix_encoding_issues()
    fix_import_errors()
    format_code()
    
    print("=" * 50)
    print("✅ All fixes applied successfully!")
    print("Now you can run: python scripts/run_exam_tasks.py --compile")

if __name__ == "__main__":
    main()
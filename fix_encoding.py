#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix de encoding para Windows - ECPlacas 2.0
"""
import os
import sys
import locale

def fix_windows_encoding():
    """Configurar encoding UTF-8 para Windows"""
    if sys.platform.startswith('win'):
        # Configurar environment variables
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        os.environ['PYTHONLEGACYWINDOWSSTDIO'] = '1'
        
        # Configurar locale
        try:
            locale.setlocale(locale.LC_ALL, 'C.UTF-8')
        except locale.Error:
            try:
                locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
            except locale.Error:
                pass

# Ejecutar fix automáticamente al importar
fix_windows_encoding()
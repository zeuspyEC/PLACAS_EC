#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Safe Logger para Windows - ECPlacas 2.0
"""
import logging
import re
import sys


class SafeWindowsFormatter(logging.Formatter):
    """Formatter que remueve emojis en Windows"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Regex para remover emojis
        self.emoji_pattern = re.compile(
            r"[\U0001F600-\U0001F64F]|"  # emoticons
            r"[\U0001F300-\U0001F5FF]|"  # symbols & pictographs
            r"[\U0001F680-\U0001F6FF]|"  # transport & map symbols
            r"[\U0001F1E0-\U0001F1FF]|"  # flags
            r"[\U00002600-\U000027BF]|"  # misc symbols
            r"[\U0001F900-\U0001F9FF]|"  # supplemental symbols
            r"[\U0001FA70-\U0001FAFF]"  # symbols and pictographs extended-a
        )

    def format(self, record):
        # Formatear el mensaje
        msg = super().format(record)

        # En Windows, remover emojis
        if sys.platform.startswith("win"):
            msg = self.emoji_pattern.sub("", msg)
            # Reemplazar algunos emojis comunes con texto
            replacements = {
                "✅": "[OK]",
                "❌": "[ERROR]",
                "⚠️": "[WARNING]",
                "🔨": "[BUILD]",
                "🔍": "[LINT]",
                "🧪": "[TEST]",
                "🐳": "[DOCKER]",
                "🚀": "[DEPLOY]",
                "📁": "[DIR]",
                "📄": "[FILE]",
                "💻": "[TECH]",
                "🎯": "[TARGET]",
            }
            for emoji, text in replacements.items():
                msg = msg.replace(emoji, text)

        return msg


def get_safe_logger(name, level=logging.INFO):
    """Crear logger seguro para Windows"""
    logger = logging.getLogger(name)

    if not logger.handlers:
        # Handler para consola
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)

        # Handler para archivo
        file_handler = logging.FileHandler("logs/ecplacas_safe.log", encoding="utf-8")
        file_handler.setLevel(level)

        # Formatter seguro
        formatter = SafeWindowsFormatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        logger.setLevel(level)

    return logger

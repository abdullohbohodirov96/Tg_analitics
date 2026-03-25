"""
Task Classifier Service — Xabarlardan vazifalarni aniqlash va tahlil qilish.
Intent-based tahlil (uzbek, russian, dialects, misspellings).
"""
import re
from typing import Optional, Tuple

class TaskClassifier:
    """Xabarlarni task/vazifa ekanligini aniqlash va tozalash xizmati"""

    def __init__(self):
        # Vazifa aniqlash uchun kalit so'zlar va iboralar (regex)
        # O'zbekcha (lotin va kirill, shevalar)
        self.uz_patterns = [
            r"vazifa", r"vazifa(lar)?\s+joyiga", r"task(ga)?", 
            r"qilib\s+ber", r"tayyorlab\s+ber", r"yozib\s+ber", r"yechib\s+ber",
            r"ko'rib\s+chiq", r"hal\s+qil", r"eslatma", r"tashab\s+ber",
            r"tashlab\s+ber", r"qilib\s+qo'y", r"belgilang", r"qo'shing",
            r"kerak", r"tayyorlang", r"ertaga\s+qilib",
            # Kirillcha
            r"вазифа", r"қилиб\s+бер", r"тайёрлаб\s+бер", r"ёзиб\s+бер",
            r"кўриб\s+чиқ", r"ҳал\s+қил", r"эслатма", r"ташаб\s+бер",
            r"ташлаб\s+бер", r"қилиб\s+қўй", r"белгиланг", r"қўшинг",
            r"керак", r"тайёрланг"
        ]
        
        # Ruscha patterns
        self.ru_patterns = [
            r"сделайте", r"добавьте\s+в\s+задачи", r"надо\s+сделать",
            r"закиньте\s+в\s+задачи", r"посмотрите", r"подготовьте",
            r"задача", r"нужно", r"проверьте", r"исправьте"
        ]

        # Inkor etuvchi (Task bo'lmagan) patterns
        self.negative_patterns = [
            r"salom", r"assalom", r"rahmat", r"raxmat", r"yaxshimisiz",
            r"narxi\s+qancha", r"qancha\s+turadi", r"narxini\s+eting",
            r"qanaqa", r"mi", r"\?"
        ]

    def detect_intent(self, text: str) -> bool:
        """
        Xabar vazifa/topshiriq ekanligini aniqlash.
        """
        if not text or len(text) < 5:
            return False
            
        text_lower = text.lower()
        
        # 1. Juda qisqa yoki savol so'raydigan xabarlarni chiqarib tashlaymiz
        for pattern in self.negative_patterns:
            if re.search(pattern, text_lower):
                # Agar gapda "vazifa" so'zi bo'lmasa, savollarni task demaymiz
                if "vazifa" not in text_lower and "task" not in text_lower:
                    return False

        # 2. Vazifa ekanligini tasdiqlovchi patternlarni tekshiramiz
        all_patterns = self.uz_patterns + self.ru_patterns
        
        matches = 0
        for pattern in all_patterns:
            if re.search(pattern, text_lower):
                matches += 1
                
        # Hech bo'lmasa bitta match bo'lishi kerak
        return matches > 0

    def normalize_task_text(self, text: str) -> str:
        """
        Xabardan vazifaning qisqacha mazmunini ajratib olish (title uchun).
        """
        # Ortiqcha "iltimos", "marhamat" kabi so'zlarni olib tashlaymiz
        cleaned = re.sub(r"(iltimos|marhamat|shu|buni|shuni|илтимос|шу|буни|шуни|пожалуйста)", "", text, flags=re.IGNORECASE)
        
        # Ortiqcha bo'shliqlarni olib tashlash
        cleaned = " ".join(cleaned.split())
        
        # Birinchi 100 belgini qaytaramiz (agar uzun bo'lsa)
        if len(cleaned) > 100:
            return cleaned[:97] + "..."
        return cleaned

    def classify(self, text: str) -> Tuple[bool, str]:
        """
        Ham aniqlash, ham normalizatsiya qilish.
        """
        is_task = self.detect_intent(text)
        normalized = self.normalize_task_text(text) if is_task else ""
        return is_task, normalized

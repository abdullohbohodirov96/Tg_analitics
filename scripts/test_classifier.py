import sys
import os

# App papkasini pathga qo'shish
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.task_classifier import TaskClassifier

def test_classifier():
    classifier = TaskClassifier()
    
    test_cases = [
        # O'zbekcha - Tasklar
        ("vazifa qilib belgilang", True),
        ("shuni qilib berila iltimos", True),
        ("buni tayyorlang ertagacha", True),
        ("vazifalar joyiga tashab berila", True),
        ("shu masalani yechib bering", True),
        ("taskga qo'shing", True),
        ("buni hal qilib bering", True),
        
        # Kirillcha - Tasklar
        ("вазифа қилиб белгиланг", True),
        ("шуни қилиб берила", True),
        
        # Ruscha - Tasklar
        ("сделайте это пожалуйста", True),
        ("добавьте в задачи", True),
        ("нужно подготовить отчет", True),
        
        # Not Task (Casual conversation)
        ("salom, qalesiz?", False),
        ("rahmat kattakon", False),
        ("narxi qancha ekan?", False),
        ("ertaga bormisiz?", False),
    ]
    
    print("=== TaskClassifier Testlari ===")
    passed = 0
    for text, expected in test_cases:
        is_task, normalized = classifier.classify(text)
        result = "O'tdi" if is_task == expected else "Xato"
        if is_task == expected: passed += 1
        
        print(f"[{result}] Matn: {text[:30]:<30} | Kutilgan: {expected:<5} | Olingan: {is_task:<5} | Title: {normalized}")
        
    print(f"\nNatija: {passed}/{len(test_cases)} o'tdi.")

if __name__ == "__main__":
    test_classifier()

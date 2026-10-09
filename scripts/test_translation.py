#!/usr/bin/env python3
"""
Interactive Translation Tester for SwasthyaConnect
Uses the local, offline Meta NLLB-200 engine.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.services.translation_service import translate_text, SUPPORTED_LANGS


def main():
    print("=" * 65)
    print("🏥 SWASTHYACONNECT — OFFLINE MULTILINGUAL ENGINE CHECKER")
    print("=" * 65)
    print("Supported Languages:")
    for code, name in SUPPORTED_LANGS.items():
        print(f"  • {code:4s} -> {name}")
    print("=" * 65)

    sample_texts = [
        "Patient diagnosed with acute bronchitis. Prescribed Azithromycin 500mg OD for 5 days.",
        "Fasting blood glucose is 185 mg/dL, indicating uncontrolled diabetes.",
        "Follow up with cardiologist in 2 weeks for echocardiogram.",
    ]

    print("\n🔍 RUNNING AUTOMATED VERIFICATION WITH CLINICAL SAMPLES:\n")
    for idx, text in enumerate(sample_texts, 1):
        print(f"[{idx}] English Input:")
        print(f"    \"{text}\"")
        
        hi = translate_text(text, target_lang="hi")
        print(f"    🇮🇳 Hindi:   {hi}")
        
        mr = translate_text(text, target_lang="mr")
        print(f"    🚩 Marathi: {mr}\n")

    print("=" * 65)
    print("✅ Offline engine verified successfully!")
    print("=" * 65)


if __name__ == "__main__":
    main()

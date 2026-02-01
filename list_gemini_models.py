#!/usr/bin/env python3
"""
List all available Gemini models
"""

import google.generativeai as genai
import os

# Configure API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyAlVKgY-gtbtd5DI9KuDunnsbXO-K_cHy4')
genai.configure(api_key=GEMINI_API_KEY)

print("=" * 80)
print("Available Gemini Models")
print("=" * 80)
print()

try:
    models = genai.list_models()
    
    for model in models:
        # Check if the model supports generateContent
        if 'generateContent' in model.supported_generation_methods:
            print(f"✅ {model.name}")
            print(f"   Display Name: {model.display_name}")
            print(f"   Description: {model.description}")
            print(f"   Methods: {', '.join(model.supported_generation_methods)}")
            print()
    
    print("=" * 80)
    print(f"Total models supporting generateContent: {sum(1 for m in genai.list_models() if 'generateContent' in m.supported_generation_methods)}")
    print("=" * 80)
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    print("\nMake sure your GEMINI_API_KEY is set correctly:")
    print("export GEMINI_API_KEY='your-key-here'")

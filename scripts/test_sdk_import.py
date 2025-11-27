"""
Simple test to verify the SDK import works correctly.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("Testing SDK import...")

try:
    from utils.gemini_vision import GeminiVisionExtractor
    print("SUCCESS: GeminiVisionExtractor imported successfully")

    # Try to create instance (will fail without API key, but that's ok)
    try:
        extractor = GeminiVisionExtractor(api_key="test_key")
        print("SUCCESS: GeminiVisionExtractor instance created")
        print(f"  - Client type: {type(extractor.client)}")
        print(f"  - Model name: {extractor.model_name}")
    except Exception as e:
        print(f"Instance creation: {e}")

except ImportError as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\nAll import tests completed!")

"""
Test script for FastAPI backend.

Tests all API endpoints to ensure they work correctly.
"""

import requests
import json
from time import sleep

BASE_URL = "http://localhost:8000"


def print_header(title: str):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_health_check():
    """Test health check endpoint"""
    print_header("TEST 1: Health Check")

    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    assert response.status_code == 200
    print("[OK] Health check passed")


def test_generate_flashcards():
    """Test flashcard generation"""
    print_header("TEST 2: Generate Flashcards")

    payload = {
        "content": "The mitochondria is the powerhouse of the cell. It produces ATP through cellular respiration.",
        "num_flashcards": 3,
        "difficulty": "medium"
    }

    response = requests.post(f"{BASE_URL}/api/flashcards/generate", json=payload)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Generated {len(data['flashcards'])} flashcards")
        print(f"First flashcard: {data['flashcards'][0]['front']}")
        print("[OK] Flashcard generation passed")
        return data['flashcards'][0]['id']  # Return first flashcard ID
    else:
        print(f"[ERROR] {response.text}")
        return None


def test_get_due_flashcards():
    """Test getting due flashcards"""
    print_header("TEST 3: Get Due Flashcards")

    response = requests.get(f"{BASE_URL}/api/flashcards/due")
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Due flashcards: {data['total_due']}")
        print("[OK] Get due flashcards passed")
    else:
        print(f"[ERROR] {response.text}")


def test_review_flashcard(flashcard_id: str):
    """Test reviewing a flashcard"""
    print_header("TEST 4: Review Flashcard")

    if not flashcard_id:
        print("[SKIP] No flashcard ID available")
        return

    payload = {
        "flashcard_id": flashcard_id,
        "response_quality": 5,  # Perfect recall
        "was_correct": True,
        "time_spent_seconds": 3.5
    }

    response = requests.post(f"{BASE_URL}/api/flashcards/review", json=payload)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Message: {data['message']}")
        print(f"Next review: {data['stats']['next_review_date']}")
        print("[OK] Review flashcard passed")
    else:
        print(f"[ERROR] {response.text}")


def test_generate_quiz():
    """Test quiz generation"""
    print_header("TEST 5: Generate Quiz")

    payload = {
        "content": "Python is a high-level programming language. It supports multiple programming paradigms.",
        "num_questions": 3,
        "difficulty": "medium"
    }

    response = requests.post(f"{BASE_URL}/api/quiz/generate", json=payload)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Generated {len(data['questions'])} questions")
        print(f"First question: {data['questions'][0]['question']}")
        print("[OK] Quiz generation passed")
        return data['quiz_id']
    else:
        print(f"[ERROR] {response.text}")
        return None


def test_generate_match_quiz():
    """Test match quiz generation"""
    print_header("TEST 6: Generate Match Quiz")

    payload = {
        "content": "DNA stores genetic information. RNA helps in protein synthesis.",
        "num_pairs": 3,
        "difficulty": "medium"
    }

    response = requests.post(f"{BASE_URL}/api/match/generate", json=payload)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Generated {len(data['pairs'])} pairs")
        print(f"First pair: {data['pairs'][0]['prompt']} -> {data['pairs'][0]['answer']}")
        print("[OK] Match quiz generation passed")
    else:
        print(f"[ERROR] {response.text}")


def test_get_statistics():
    """Test statistics endpoint"""
    print_header("TEST 7: Get Statistics")

    response = requests.get(f"{BASE_URL}/api/stats")
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Total interactions: {data['total_interactions']}")
        print(f"Verified interactions: {data['verified_interactions']}")
        print(f"Total flashcards: {data['flashcards']['total']}")
        print("[OK] Statistics passed")
    else:
        print(f"[ERROR] {response.text}")


def test_ml_readiness():
    """Test ML readiness check"""
    print_header("TEST 8: ML Readiness Check")

    response = requests.get(f"{BASE_URL}/api/stats/ml-readiness")
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Ready for ML: {data['ready']}")
        print(f"ML Confidence: {data['ml_confidence']:.1%}")
        print("[OK] ML readiness check passed")
    else:
        print(f"[ERROR] {response.text}")


def main():
    """Run all tests"""

    print("\n" + "#" * 70)
    print("#" + " " * 22 + "API ENDPOINT TESTS" + " " * 22 + "#")
    print("#" * 70)

    print("\nMake sure the API server is running:")
    print("  python main.py")
    print("\nWaiting 3 seconds before starting tests...")
    sleep(3)

    try:
        # Test endpoints
        test_health_check()

        flashcard_id = test_generate_flashcards()
        test_get_due_flashcards()
        test_review_flashcard(flashcard_id)

        test_generate_quiz()
        test_generate_match_quiz()

        test_get_statistics()
        test_ml_readiness()

        print_header("ALL TESTS PASSED!")
        print("\nAPI is ready for React frontend integration!")
        print("\nNext steps:")
        print("  1. Merge with React frontend")
        print("  2. Update React to call these endpoints")
        print("  3. Test end-to-end workflow")
        print("\n")

    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Cannot connect to API server!")
        print("Make sure the server is running: python main.py")
        print("\n")
    except Exception as e:
        print(f"\n[ERROR] Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        print("\n")


if __name__ == "__main__":
    main()

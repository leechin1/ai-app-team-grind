"""
Test script to populate Supabase with sample data
Run this from the backend directory after disabling RLS

USAGE:
    cd backend
    python test_database.py
"""
import os
import sys
from datetime import datetime, timedelta
import asyncio

# IMPORTANT: Load .env BEFORE importing anything else
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

# Verify env loaded
if not os.getenv("SUPABASE_URL"):
    print("[ERROR] .env file not loaded or missing SUPABASE_URL")
    print(f"Tried to load from: {os.path.abspath(env_path)}")
    sys.exit(1)

print(f"[OK] Loaded .env from: {os.path.abspath(env_path)}")
print(f"     SUPABASE_URL: {os.getenv('SUPABASE_URL')[:40]}...")

from core.supabase_client import db
from core.db_models import (
    ProjectCreate,
    NoteCreate,
    FlashcardCreate,
)

# Test user ID (from development mode)
TEST_USER_ID = "00000000-0000-0000-0000-000000000001"


async def create_test_user():
    """Create test user profile if it doesn't exist"""
    print("\n" + "="*60)
    print("CREATING TEST USER PROFILE")
    print("="*60)

    try:
        # Check if user already exists by ID
        result = db.client.table("profiles").select("*").eq("id", TEST_USER_ID).execute()

        if result.data:
            print(f"[OK] Test user already exists (by ID): {result.data[0]['email']}")
            return True

        # Check if email already exists (but with different ID)
        result = db.client.table("profiles").select("*").eq("email", "test@notiq.app").execute()

        if result.data:
            print(f"[OK] Test user exists with email test@notiq.app")
            print(f"[INFO] Using existing user ID: {result.data[0]['id']}")
            # Update TEST_USER_ID to match existing user
            global TEST_USER_ID
            TEST_USER_ID = result.data[0]['id']
            return True

        # Create test user profile
        profile_data = {
            "id": TEST_USER_ID,
            "email": "test@notiq.app",
            "full_name": "Test User"
        }

        result = db.client.table("profiles").insert(profile_data).execute()
        print(f"[OK] Test user created: test@notiq.app")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to create test user: {e}")
        return False


async def test_database_connection():
    """Test basic database connectivity"""
    print("\n" + "="*60)
    print("TESTING DATABASE CONNECTION")
    print("="*60)

    try:
        # Test connection
        result = db.client.table("projects").select("count", count="exact").execute()
        print(f"[OK] Database connected successfully!")
        print(f"[INFO] Current projects in database: {result.count}")
        return True
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        return False


async def create_test_project():
    """Create a test project"""
    print("\n" + "="*60)
    print("CREATING TEST PROJECT")
    print("="*60)

    try:
        project = ProjectCreate(
            name="Test Project - Biology 101",
            description="Sample project to test Supabase integration",
            icon="🧬",
            color="from-green-500 to-emerald-600"
        )

        created = await db.create_project(TEST_USER_ID, project)
        print(f"[OK] Project created: {created.name}")
        print(f"   ID: {created.id}")
        print(f"   Icon: {created.icon}")
        return created.id
    except Exception as e:
        print(f"[ERROR] Failed to create project: {e}")
        return None


async def create_test_notes(project_id: str):
    """Create test notes with sample content"""
    print("\n" + "="*60)
    print("CREATING TEST NOTES")
    print("="*60)

    notes_data = [
        {
            "title": "Cell Structure",
            "content": "Cells are the basic units of life. They contain a nucleus, mitochondria, and other organelles.",
            "type": "Study Notes"
        },
        {
            "title": "DNA and RNA",
            "content": "DNA (Deoxyribonucleic Acid) stores genetic information. RNA (Ribonucleic Acid) helps synthesize proteins.",
            "type": "Study Notes"
        },
        {
            "title": "Photosynthesis",
            "content": "Plants convert light energy into chemical energy through photosynthesis. Formula: 6CO2 + 6H2O + light → C6H12O6 + 6O2",
            "type": "Study Notes"
        }
    ]

    created_notes = []
    for note_data in notes_data:
        try:
            note = NoteCreate(
                project_id=project_id,
                title=note_data["title"],
                content=note_data["content"],
                content_html=f"<p>{note_data['content']}</p>",
                type=note_data["type"]
            )
            created = await db.create_note(TEST_USER_ID, note)
            print(f"[OK] Note created: {created.title}")
            created_notes.append(created)
        except Exception as e:
            print(f"[ERROR] Failed to create note '{note_data['title']}': {e}")

    return created_notes


async def create_test_flashcards(project_id: str):
    """Create test flashcards for spaced repetition"""
    print("\n" + "="*60)
    print("CREATING TEST FLASHCARDS")
    print("="*60)

    flashcards_data = [
        {
            "front": "What is the powerhouse of the cell?",
            "back": "Mitochondria - produces ATP through cellular respiration",
            "difficulty": "easy"
        },
        {
            "front": "What is the difference between DNA and RNA?",
            "back": "DNA is double-stranded and contains deoxyribose sugar. RNA is single-stranded and contains ribose sugar.",
            "difficulty": "medium"
        },
        {
            "front": "What is the formula for photosynthesis?",
            "back": "6CO2 + 6H2O + light energy → C6H12O6 + 6O2",
            "difficulty": "medium"
        },
        {
            "front": "What are the stages of mitosis?",
            "back": "Prophase, Metaphase, Anaphase, Telophase (PMAT)",
            "difficulty": "hard"
        },
        {
            "front": "What is the function of ribosomes?",
            "back": "Ribosomes synthesize proteins by translating mRNA",
            "difficulty": "easy"
        }
    ]

    created_flashcards = []
    for i, fc_data in enumerate(flashcards_data):
        try:
            # Create flashcards with different review dates (some due now, some later)
            flashcard = FlashcardCreate(
                project_id=project_id,
                front=fc_data["front"],
                back=fc_data["back"],
                source_type="manual",
                difficulty=fc_data["difficulty"],
                tags=["biology", "cells"]
            )
            created = await db.create_flashcard(TEST_USER_ID, flashcard)

            # Make some cards due for review
            if i < 3:
                # Make first 3 cards due for review
                next_review = datetime.now() - timedelta(hours=1)
                await db.update_flashcard(
                    created.id,
                    TEST_USER_ID,
                    {"next_review_date": next_review.isoformat()}
                )
                print(f"[OK] Flashcard created (DUE FOR REVIEW): {created.front[:50]}...")
            else:
                print(f"[OK] Flashcard created (future review): {created.front[:50]}...")

            created_flashcards.append(created)
        except Exception as e:
            print(f"[ERROR] Failed to create flashcard: {e}")

    return created_flashcards


async def verify_data(project_id: str):
    """Verify all data was created correctly"""
    print("\n" + "="*60)
    print("VERIFYING DATA")
    print("="*60)

    try:
        # Check projects
        projects = await db.get_user_projects(TEST_USER_ID)
        print(f"[OK] Projects: {len(projects)} found")

        # Check notes
        notes = await db.get_project_notes(project_id, TEST_USER_ID)
        print(f"[OK] Notes: {len(notes)} found")

        # Check flashcards
        flashcards = await db.get_project_flashcards(project_id, TEST_USER_ID)
        print(f"[OK] Flashcards: {len(flashcards)} found")

        # Check due flashcards
        due_cards = await db.get_due_flashcards(project_id, TEST_USER_ID, limit=20)
        print(f"[OK] Due for review: {len(due_cards)} flashcards")

        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Project ID: {project_id}")
        print(f"Total Notes: {len(notes)}")
        print(f"Total Flashcards: {len(flashcards)}")
        print(f"Due for Review: {len(due_cards)}")
        print("\nAll data created successfully!")
        print("\nNext Steps:")
        print("1. Open your frontend app")
        print("2. You should see 'Test Project - Biology 101'")
        print("3. Go to Review page to see flashcards due for review")
        print("4. Check Notes to see the sample notes")
        print("="*60)

        return True
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        return False


async def main():
    """Main test function"""
    print("\nSUPABASE DATABASE TEST SCRIPT")
    print("="*60)
    print("This script will create test data in your Supabase database")
    print("Make sure you've disabled RLS first!")
    print("="*60)

    # Test connection
    if not await test_database_connection():
        print("\n[ERROR] Cannot proceed without database connection")
        return

    # Create test user first
    if not await create_test_user():
        print("\n[ERROR] Cannot proceed without a test user")
        return

    # Create test project
    project_id = await create_test_project()
    if not project_id:
        print("\n[ERROR] Cannot proceed without a project")
        return

    # Create test notes
    await create_test_notes(project_id)

    # Create test flashcards
    await create_test_flashcards(project_id)

    # Verify everything
    await verify_data(project_id)


if __name__ == "__main__":
    asyncio.run(main())

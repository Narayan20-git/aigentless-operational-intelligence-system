"""
Aigentless — Embeddings Generation Script
Generates vector embeddings for FAQs and Amenity descriptions
Uses Google text-embedding-004 model (768 dimensions)
Stores embeddings in Supabase pgvector columns

Usage:
  python scripts/generate_embeddings.py
  python scripts/generate_embeddings.py --table faqs
  python scripts/generate_embeddings.py --table amenities
"""
import os
import sys
import time
import argparse
from dotenv import load_dotenv
import google.generativeai as genai

# Add project root to sys.path so config module can be found
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.database import get_client

load_dotenv()

genai.configure(api_key=os.environ.get("GOOGLE_API_KEY", ""))
supabase = get_client()

parser = argparse.ArgumentParser()
parser.add_argument("--table", choices=["faqs", "amenities", "all"], default="all")
args = parser.parse_args()

def get_embedding(text: str) -> list[float]:
    """Get 768-dim embedding from Gemini embedding model."""
    result = genai.embed_content(
        model="models/gemini-embedding-001",
        content=text,
        task_type="retrieval_document",
        output_dimensionality=768
    )
    return result["embedding"]

def embed_faqs():
    """Generate embeddings for all published FAQs with answers."""
    print("\n── Generating FAQ embeddings ──")
    faqs = supabase.table("property_faqs") \
        .select("id, question, answer, category") \
        .eq("is_published", True) \
        .neq("answer", "") \
        .is_("embedding", "null") \
        .execute().data or []

    print(f"  Found {len(faqs)} FAQs without embeddings")
    success = 0
    for i, faq in enumerate(faqs):
        try:
            # Combine question + answer for richer embedding
            text = f"FAQ Category: {faq['category']}\nQuestion: {faq['question']}\nAnswer: {faq['answer']}"
            embedding = get_embedding(text)
            supabase.table("property_faqs").update({
                "embedding": embedding
            }).eq("id", faq["id"]).execute()
            success += 1
            print(f"  ✓ [{i+1}/{len(faqs)}] {faq['question'][:60]}...")
            time.sleep(0.1)  # Rate limiting
        except Exception as e:
            print(f"  ✗ Failed: {faq['id']} — {e}")

    print(f"  Done: {success}/{len(faqs)} FAQ embeddings generated")

def embed_amenities():
    """Generate embeddings for all amenities with descriptions."""
    print("\n── Generating Amenity embeddings ──")
    amenities = supabase.table("property_amenities") \
        .select("id, name, description, category") \
        .neq("description", "") \
        .is_("embedding", "null") \
        .execute().data or []

    print(f"  Found {len(amenities)} amenities without embeddings")
    success = 0
    for i, amenity in enumerate(amenities):
        try:
            text = f"Amenity: {amenity['name']}\nCategory: {amenity['category']}\nDescription: {amenity['description']}"
            embedding = get_embedding(text)
            supabase.table("property_amenities").update({
                "embedding": embedding
            }).eq("id", amenity["id"]).execute()
            success += 1
            print(f"  ✓ [{i+1}/{len(amenities)}] {amenity['name']}")
            time.sleep(0.1)
        except Exception as e:
            print(f"  ✗ Failed: {amenity['id']} — {e}")

    print(f"  Done: {success}/{len(amenities)} Amenity embeddings generated")

print("="*55)
print("  Aigentless — Embeddings Generation")
print(f"  Model: gemini-embedding-001 (768 dimensions)")
print(f"  Table: {args.table}")
print("="*55)

if args.table in ("faqs", "all"):
    embed_faqs()
if args.table in ("amenities", "all"):
    embed_amenities()

print("\n✅ Embeddings generation complete!")
print("   pgvector indexes will auto-update for similarity search.")

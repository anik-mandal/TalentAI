import chromadb
import os

# PersistentClient saves to disk — data survives between runs
# Points to chroma_db/ folder in the project root
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CHROMA_PATH = os.path.join(_BASE_DIR, "chroma_db")
os.makedirs(_CHROMA_PATH, exist_ok=True)


def get_chroma_client():
    return chromadb.PersistentClient(path=_CHROMA_PATH)


def get_jobs_collection():
    # MUST match the name used in hr_portal.py — "company_requirements"
    return get_chroma_client().get_or_create_collection(name="company_requirements")


def get_candidates_collection():
    return get_chroma_client().get_or_create_collection(name="screened_candidates")


def store_job_in_chroma(job_id, job_text):
    collection = get_jobs_collection()
    collection.upsert(documents=[job_text], ids=[str(job_id)])
    print(f"Job {job_id} stored in ChromaDB successfully")


def get_job_context(job_id):
    collection = get_jobs_collection()
    try:
        results = collection.get(ids=[str(job_id)])
        if results and results["documents"]:
            return results["documents"][0]
    except Exception:
        pass
    return ""


def check_duplicate_resume(resume_text, threshold=0.95):
    """
    Check if a similar resume already exists in ChromaDB.
    Returns True if duplicate found (similarity > threshold).
    """
    collection = get_candidates_collection()

    if collection.count() == 0:
        return False

    try:
        results = collection.query(
            query_texts=[resume_text[:1000]],
            n_results=1
        )

        if results and results.get("distances"):
            # ChromaDB default uses L2 distance; lower = more similar
            # For cosine distance: similarity = 1 - distance
            distance = results["distances"][0][0]
            similarity = 1 - distance

            if similarity > threshold:
                return True

    except Exception:
        pass

    return False


def store_candidate_resume(candidate_id, resume_text):
    """Store a candidate resume in ChromaDB for duplicate detection."""
    collection = get_candidates_collection()
    collection.upsert(
        documents=[resume_text[:1000]],
        ids=[str(candidate_id)]
    )
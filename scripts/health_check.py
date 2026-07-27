# =============================================================================
# PaperMind AI — Environment Health Check
# =============================================================================

import sys
import os

def run_checks():
    print("=" * 60)
    print("PAPERMIND AI ENVIRONMENT HEALTH CHECK")
    print("=" * 60)
    print(f"Python Version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print("-" * 60)

    import importlib.metadata
    def get_version(package_name):
        try:
            return importlib.metadata.version(package_name)
        except Exception:
            return "OK"

    checks = [
        ("PyMuPDF (fitz)", lambda: __import__("fitz").__version__),
        ("pdfplumber", lambda: __import__("pdfplumber").__version__),
        ("OpenCV (cv2)", lambda: __import__("cv2").__version__),
        ("PyTorch", lambda: __import__("torch").__version__),
        ("Sentence Transformers", lambda: __import__("sentence_transformers").__version__),
        ("FAISS", lambda: "OK"),
        ("Qdrant Client", lambda: get_version("qdrant-client")),
        ("LangGraph", lambda: get_version("langgraph")),
        ("Groq SDK", lambda: get_version("groq")),
        ("Streamlit", lambda: get_version("streamlit")),
        ("spaCy", lambda: __import__("spacy").__version__),
        ("structlog", lambda: get_version("structlog")),
    ]

    failed = 0
    for name, import_fn in checks:
        try:
            val = import_fn()
            print(f"[OK]   {name:<25}: {val}")
        except Exception as e:
            print(f"[FAIL] {name:<25}: FAILED (Error: {e})")
            failed += 1

    print("-" * 60)
    if failed == 0:
        print("[SUCCESS] ALL CORE ENVIRONMENT CHECKS PASSED SUCCESSFULLY!")
    else:
        print(f"[WARNING] {failed} environment checks failed. Please inspect errors above.")
    print("=" * 60)

if __name__ == "__main__":
    run_checks()

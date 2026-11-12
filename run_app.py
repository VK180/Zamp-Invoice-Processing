import os
import sys
import subprocess
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"), override=True)
import uvicorn

def main():
    print("=" * 70)
    print("  ZAMP AI SOLUTIONS ANALYST — AP INVOICE PROCESSING ENGINE (PS-1)")
    print("=" * 70)

    # 1. Ensure sample PDFs are generated
    samples_dir = os.path.join(os.path.dirname(__file__), "backend", "sample_invoices")
    if not os.path.exists(samples_dir) or len(os.listdir(samples_dir)) < 6:
        print("[*] Generating realistic test invoice PDFs for scenarios & edge cases...")
        try:
            from backend.generator import generate_all_samples
            generate_all_samples()
        except Exception as e:
            print(f"[!] Warning generating samples: {e}")

    # 2. Check frontend build
    dist_dir = os.path.join(os.path.dirname(__file__), "frontend", "dist")
    if not os.path.exists(dist_dir):
        print("[*] Building production React frontend...")
        frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
        subprocess.run(["npm", "run", "build"], cwd=frontend_dir, shell=True, check=True)

    print("\n[+] System ready!")
    print("----------------------------------------------------------------------")
    print("  >> LIVE APPLICATION URL:  http://127.0.0.1:8000")
    print("  >> API DOCUMENTATION:     http://127.0.0.1:8000/docs")
    print("----------------------------------------------------------------------")
    print("  Press Ctrl+C to stop the server.\n")

    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=False)

if __name__ == "__main__":
    main()

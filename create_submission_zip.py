"""
Utility script to create a clean, submission-ready ZIP package of the ITC project under 10MB.
Excludes Git version control metadata, cache directories, and redundant intermediate files.
"""

import os
import zipfile


def make_submission_zip(output_filename="ITC_Project.zip"):
    exclude_patterns = [
        os.sep + ".git",
        os.sep + "__pycache__",
        os.sep + ".pytest_cache",
        os.sep + ".backup_before_audit_repairs",
        os.sep + ".streamlit",
        os.sep + "outputs" + os.sep + "IEEE_Wireless_Communication_Paper",
        os.sep + "outputs" + os.sep + "generate_docx.py",
        os.sep + "outputs" + os.sep + "generate_figures.py",
        os.sep + "outputs" + os.sep + "generate_pdf.py",
    ]

    base_dir = os.path.dirname(os.path.abspath(__file__))
    zip_path = os.path.join(base_dir, output_filename)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
        for root, dirs, files in os.walk(base_dir):
            # Sort files for deterministic archive creation
            for f in sorted(files):
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, base_dir)

                if f.endswith(".zip") or f.endswith(".pyc") or f.endswith(".pyo"):
                    continue

                if any(p in (os.sep + rel_path) for p in exclude_patterns):
                    continue

                zipf.write(full_path, rel_path)

    # Validate integrity
    with zipfile.ZipFile(zip_path, "r") as z:
        corrupted = z.testzip()
        if corrupted:
            raise RuntimeError(f"Archive file verification failed on: {corrupted}")

    size_bytes = os.path.getsize(zip_path)
    size_mb = size_bytes / (1024 * 1024)
    print(f"Created: {output_filename}")
    print(f"Size: {size_mb:.2f} MB ({size_bytes:,} bytes)")
    print(f"Status: Under 10 MB limit ({size_bytes / 10_000_000 * 100:.1f}% of 10MB limit)")
    return zip_path


if __name__ == "__main__":
    make_submission_zip()

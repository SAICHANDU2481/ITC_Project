"""
Automated unit and integration test for Streamlit app logic and HTTP server.
"""

import urllib.request
import pytest
import os
import sys

def test_streamlit_server_online():
    url = "http://127.0.0.1:8501"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=5) as response:
        assert response.status == 200
        html = response.read().decode('utf-8', errors='ignore')
        assert "Streamlit" in html or "streamlit" in html.lower()


def test_app_script_syntax_and_imports():
    # Verify app.py can be compiled and parsed without any syntax or import errors
    import app
    assert hasattr(app, 'APP_DIR')
    assert os.path.exists(app.APP_DIR)


def test_dashboard_header_privacy_and_assignment_badge():
    """
    Focused regression test: Verifies that the Streamlit dashboard header and UI
    do not expose personal information (student name or registration number)
    and that the assignment badge displays exactly 'Assignment: Wired Network'
    without any registration digit.
    """
    app_path = os.path.join(os.path.dirname(__file__), "..", "app.py")
    with open(app_path, "r", encoding="utf-8") as f:
        app_code = f.read()

    # 1. Verify personal details are completely removed from visible header and UI
    assert "Student: Aravind" not in app_code, "Student name badge must be removed from dashboard."
    assert "Reg: 23BCE7551" not in app_code, "Registration number badge must be removed from dashboard."
    assert "Aravind" not in app_code, "Student name must not appear in app.py UI elements."
    assert "Assignment: Wired Network (Digit 1)" not in app_code, "Registration digit must be removed from assignment badge."
    assert "Digit 1" not in app_code, "Digit 1 must not appear in dashboard."

    # 2. Verify assignment badge remains visible and correctly formatted
    assert '<span class="badge badge-success">Assignment: Wired Network</span>' in app_code, (
        "Assignment badge must be present with text 'Assignment: Wired Network'."
    )

    # 3. Verify download filename does not expose personal details
    assert "IEEE_Conference_Paper_23BCE7551_Aravind.pdf" not in app_code, (
        "Download button must not use personal name/reg in download filename."
    )


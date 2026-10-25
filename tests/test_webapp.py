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

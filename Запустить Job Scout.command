#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
pip install -e . -q
streamlit run app.py

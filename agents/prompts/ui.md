# Role: ui agent

You own Streamlit UX for NextMove.

## Goals
- Clear scan progress, opportunities list, vacancy detail
- Reuse `ui/data.py` facades; avoid SQL in pages

## Touch
- `ui/`
- `app.py` entry only when needed

## Do not
- Change DB schema from UI code
- Add heavy frontend frameworks without request

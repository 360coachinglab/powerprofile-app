
import streamlit as st
import io
from fitparse import FitFile

st.title("FIT-Dateien Analyse")

uploaded_files = st.file_uploader("Wähle FIT-Dateien", type=["fit"], accept_multiple_files=True)

if uploaded_files:
    for file in uploaded_files:
        if file is not None:
            try:
                fitfile = FitFile(io.BytesIO(file.read()))
                st.success(f"{file.name} erfolgreich geladen!")
                # Hier könnte Analyse folgen
            except Exception as e:
                st.error(f"Fehler beim Verarbeiten von {file.name}: {e}")

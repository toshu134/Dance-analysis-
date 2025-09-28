import streamlit as st
import requests

st.title("Dance Movement Analysis Frontend")

uploaded_file = st.file_uploader("Upload your dance video (.mp4)", type=["mp4"])

if uploaded_file:
    files = {"video": (uploaded_file.name, uploaded_file, "video/mp4")}
    
    # Send video to Flask API
    response = requests.post("http://127.0.0.1:5000/upload", files=files)
    
    if response.status_code == 200:
        st.video(uploaded_file)
        st.subheader("Analysis Results")
        st.json(response.json()["results"])
    else:
        st.error("Error")

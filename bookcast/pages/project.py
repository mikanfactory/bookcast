import streamlit as st
from bookcast.pdf_to_image import convert_pdf_to_images

st.write("project page")

uploaded_file = st.file_uploader("Upload a file", type=["pdf"])
if uploaded_file is not None:
    with st.spinner("Processing..."):
        file_name = uploaded_file.name
        with open(f"downloads/{file_name}", "wb") as f:
            f.write(uploaded_file.getbuffer())

        images = convert_pdf_to_images(file_name)

        st.write(images[0])

        st.success(f"File '{uploaded_file.name}' uploaded successfully!")

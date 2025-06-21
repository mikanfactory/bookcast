import streamlit as st

st.write("podcast setting page")


def callable(*args, **kwargs):
    print("--------------------------")
    print(args)
    print("--------------------------")
    print(kwargs)
    print("--------------------------")


st.number_input(
    label="foo",
    min_value=1,
    max_value=10,
    on_change=callable,
    label_visibility="hidden",
)

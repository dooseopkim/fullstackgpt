import streamlit as st
from datetime import datetime

"""
#7.2 Data Flow (06:18)

 - Data가 변경될 때마다 Python 파일 전체가 다시 실행될 것임.
"""

today = datetime.today().strftime("%H:%M:%S")
st.header(today)


model = st.selectbox("Choose your model",("GPT-3", "GPT-4"))

if model == "GPT-3":
    st.write("cheap")
else:
    st.write("not cheap")
    st.write(model)

    name = st.text_input("What is your name?")
    st.write(name)

    value = st.slider("temperature", min_value=0.1, max_value=1.0)
    st.write(value)
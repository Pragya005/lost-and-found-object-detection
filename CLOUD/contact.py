# contact.py
import streamlit as st
import pandas as pd

def run():
    st.title("📞 Contact")

    st.write("""
    **AI Lost & Found System**  
    Minor Project
    """)

    data = {
        "Name": ["Pragya Varshney", "Aryan Jain", "Astha Bansal"],
        "Email": [
            "9923103039@mail.jiit.ac.in",
            "9923103046@mail.jiit.ac.in",
            "9923103056@mail.jiit.ac.in"
        ]
    }

    df = pd.DataFrame(data)

    df.index = df.index + 1
    df.index.name = "S.No."

    st.dataframe(df, use_container_width=True)

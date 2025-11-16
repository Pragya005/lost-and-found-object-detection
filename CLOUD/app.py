# app.py
import streamlit as st
from streamlit_option_menu import option_menu
import cloud_dashboard
import live
import search
import contact

st.set_page_config(page_title="AI Lost & Found Dashboard", layout="wide")

# -----------------------------
# TOP NAVIGATION MENU
# -----------------------------
selected = option_menu(
    menu_title=None,
    options=["Home", "Live", "Search", "Contact"],
    icons=["house", "camera", "search", "telephone"],
    orientation="horizontal",
    menu_icon="cast",
    default_index=0,
    styles={
        "container": {"padding": "10px", "background-color": "#000000"},
        "icon": {"color": "white", "font-size": "22px"},
        "nav-link": {
            "font-size": "18px",
            "text-align": "center",
            "margin": "0px",
            "color": "white",
        },
        "nav-link-selected": {"background-color": "#02ab21"},
    },
)

# -----------------------------
# PAGE ROUTING
# -----------------------------
if selected == "Home":
    cloud_dashboard.run()

elif selected == "Live":
    live.run()

elif selected == "Search":
    search.run()

elif selected == "Contact":
    contact.run()

# We are essentially routing the multiple pages into a single interface
import streamlit as st

text_editor = st.Page("builtin_text_editor.py", title="Text Editor", icon=":material/add_circle:")

pg = st.navigation([text_editor])

st.set_page_config(page_title="Data manager", page_icon=":material/edit:")
pg.run()
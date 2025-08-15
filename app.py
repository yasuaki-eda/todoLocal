import streamlit as st
import altair as alt
import pandas as pd

st.title("ToDo App")

st.write("Welcome to the ToDo application!")

# Sample chart
df = pd.DataFrame({
    'category': ['A', 'B', 'C', 'D', 'E'],
    'value': [5, 7, 3, 8, 4]
})

c = alt.Chart(df).mark_bar().encode(
    x='category',
    y='value'
)

st.altair_chart(c, use_container_width=True)

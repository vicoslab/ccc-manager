import streamlit as st

def confirmation(title):

    @st.dialog(title)
    def d(message, complete):
        st.write(message)
        
        _, left, right = st.columns([0.7, 0.15, 0.15])
        if left.button('No'):
            st.rerun()
        if right.button('Yes', type='primary'):
            complete()
            st.rerun()

    return d
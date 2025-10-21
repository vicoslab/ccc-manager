import streamlit as st
from container import add_container_with_defaults
import unicodedata

container_df = st.session_state['container_df']
user_df = st.session_state['user_df']

@st.dialog('Add user', on_dismiss='rerun')
def add_user(k, df):
    with st.form(key='add-user'):
        fullname = st.text_input('Full name', key=f'user-{k}-fullname')
        email = st.text_input('Email', key=f'user-{k}-email')
        if st.form_submit_button('Add') and fullname and email:
            type_ = {'Researcher': 'researcher', 'PhD': 'researcher', 'Student': 'student', 'LKM': 'student_LKM'}[k]
            name = unicodedata.normalize('NFKD', fullname).encode('ascii','ignore').decode().lower().split(' ')
            df.loc[email, ['USER_FULLNAME', 'USER_TYPE', 'USER_EMAIL', 'USER_NAME']] = \
                [fullname, type_, email, name[0]]
            
            if st.session_state['mentor_view']:
                df.loc[email, 'USER_MENTOR'] = st.session_state['mentor_view']
            
            add_container_with_defaults(container_df[k], name, f'{"".join(name)}-workspace', email)

            st.session_state['selected_user'] = k, email
            st.switch_page('edit-user.py')

if st.session_state['mentor_view']:
    st.html('''
        <style>
            blockquote, p {
                margin: 0 !important;
            }
        </style>
    ''')
    st.write(f'> Showing only users, mentored by `{st.session_state["mentor_view"]}` ')

for k, df in user_df.items():
    filtered = df
    if st.session_state['mentor_view']:
        filtered = filtered[filtered['USER_MENTOR'] == st.session_state['mentor_view']]
    
    if not st.session_state.view_deleted:
        filtered = filtered[filtered['DISABLED'] != True]

    if len(filtered) == 0:
        continue
    
    st.header(k, divider='gray')

    with st.container(horizontal=True, key=f'user-{k}'):
        for i, idx in enumerate(filtered.index):
            name, mentor, disabled = filtered.loc[idx, ['USER_FULLNAME', 'USER_MENTOR', 'DISABLED']]
            if st.session_state['mentor_view'] and mentor != st.session_state['mentor_view']:
                continue
            
            if disabled == disabled and disabled:
                name = f':red[{name}]'
            
            if mentor == mentor and not st.session_state['mentor_view']: # not nan
                mentor = f' `{mentor}`'
            else:
                mentor = ''

            if st.button(name + mentor, key=f'{k}-{i}'):
                st.session_state['selected_user'] = k, idx
                st.switch_page('edit-user.py')

        if st.button('', icon=':material/add:', key=f'add-{k}'):
            add_user(k, df)

st.write('> To view containers which don\'t belong to any user, click <a href=/containers target=_self>here</a>.', unsafe_allow_html=True)

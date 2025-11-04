import streamlit as st
from container import add_container_with_defaults
import unicodedata

container_df = st.session_state['container_df']
user_df = st.session_state['user_df']

@st.dialog('Add user', on_dismiss='rerun', width='medium')
def add_user(k, df):
        fullname = st.text_input('Full name', key=f'user-{k}-fullname')
        email = st.text_input('Email', key=f'user-{k}-email')
        mentor = st.selectbox('Mentor', st.session_state.mentors, st.session_state.mentors.index(st.session_state['mentor_view']), accept_new_options = True)
        
        cols = st.columns([2,6])
        pubkey = cols[0].segmented_control('Use public key from', options = ['Text', 'GitHub'], default='Text')
        
        if pubkey == 'Text':
            key = cols[1].text_input('Public key', '', key=f'user-{k}-pk')
        else:
            key = cols[1].text_input('Github username', '', key=f'user-{k}-pkgh')

        if st.button('Add') and fullname and email and key:
            type_ = {'Researcher': 'researcher', 'PhD': 'researcher', 'Student': 'student', 'LKM': 'student_LKM'}[k]
            name = unicodedata.normalize('NFKD', fullname).encode('ascii','ignore').decode().lower().split(' ')
            df.loc[email, ['USER_FULLNAME', 'USER_TYPE', 'USER_EMAIL', 'USER_NAME']] = \
                [fullname, type_, email, name[0]]
            
            df.loc[email, 'USER_PUBKEY' if pubkey == 'Text' else 'USER_PUBKEY_FROM_GITHUB'] = key

            if mentor:
                df.loc[email, 'USER_MENTOR'] = mentor
            
            add_container_with_defaults(container_df[k], name, f'{"".join(name)}-workspace', email)

            st.switch_page('commit.py')

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

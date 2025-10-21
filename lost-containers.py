import streamlit as st
import container

user_emails = set()
for df in st.session_state['user_df'].values():
    user_emails.update(df['USER_EMAIL'])

st.write('This page shows containers inaccessible through a user (i.e. email doesn\'t match).')

shown = False
for k, df in st.session_state['container_df'].items():

    orphaned = df[df['USER_EMAIL'].apply(lambda x: x not in user_emails)]

    if len(orphaned) == 0:
        continue

    st.header(k, divider='gray')
    
    for id in orphaned.index:
        c = orphaned.loc[id]
        with st.expander(c['STACK_NAME']):
            df.loc[id, 'USER_EMAIL'] = st.text_input('User email', c['USER_EMAIL'])
            container.show_ui(None, k, id, id)
    shown = True

if not shown:
    st.write('> No invalid containers found')

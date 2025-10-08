import streamlit as st
from container import add_container_with_defaults

container_df = st.session_state['container_df']
user_df = st.session_state['user_df']

columns = {
    'USER_FULLNAME': 'Name',
    'USER_TYPE': 'Type',
    'USER_EMAIL': 'Email',
    'USER_NAME': 'Username',
    'USER_MENTOR': 'Mentor',
    'USER_PUBKEY': st.column_config.TextColumn(label='Pubkey', width=100),
    'USER_PUBKEY_FROM_GITHUB': 'Pubkey (GitHub)',
    'ADMIN_USER_ACCESS': 'Admin',
    'ADDITIONAL_PRIVATE_DATA_MOUNT_GROUPS': 'Data mounts',
    'DISABLED': 'Disabled',
    'PURGE_USER_DATA': 'Purge data',
}

for k, df in user_df.items():
    st.write(f'## {k}')

    with st.container(horizontal=True, key=f'user-{k}'):
        for i, idx in enumerate(df.index):
            name, mentor = df.loc[idx, ['USER_FULLNAME', 'USER_MENTOR']]
            
            if mentor == mentor: # not nan
                mentor = f' `{mentor}`'
            else:
                mentor = ''

            if st.button(name + mentor, key=f'{k}-{i}'):
                st.session_state['selected_user'] = k, i
                st.switch_page('edit-user.py')

        with st.popover('', icon=':material/add:'):
            email = st.text_input('Email', key=f'user-{k}-add')
            if email:
                type_ = {'Researcher': 'researcher', 'PhD': 'researcher', 'Student': 'student', 'LKM': 'student_LKM'}[k]
                name = email[:email.index('@')]
                df.loc[email, ['USER_FULLNAME', 'USER_TYPE', 'USER_EMAIL']] = [name, type_, email]
                
                add_container_with_defaults(container_df[k], f'{name}-workspace', email)

                st.session_state['selected_user'] = k, len(df) - 1
                st.switch_page('edit-user.py')

import streamlit as st

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

selection = st.dataframe(user_df[['USER_FULLNAME','USER_EMAIL','USER_MENTOR','USER_TYPE']],
    column_config=columns,
    selection_mode = 'single-row',
    on_select = 'rerun',
    hide_index = True,
    key = 'users',
    #num_rows = 'dynamic',
)

if selection['selection']['rows']:
    st.session_state['selected_user'] = selection['selection']['rows'][0]
    st.switch_page('edit-user.py')

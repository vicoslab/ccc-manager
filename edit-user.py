import streamlit as st
import pandas as pd
import itertools
import container

user_df = st.session_state['user_df']
container_df = st.session_state['container_df']

def checknan(x, default):
    if x == x:
        return x
    return default

id = st.session_state['selected_user']
person = user_df.iloc[id]

# selection = st.dataframe(shown_containers, column_config=colcfg.container,
#     key = 'containers',
#     selection_mode = 'single-row',
#     on_select = 'rerun',
#     hide_index = True,
# )
# if selection['selection']['rows']:
#     st.session_state['selected_container'] = selection['selection']['rows'][0]
#     st.switch_page('edit-container.py')

inputs = {}

cols = st.columns(3)
inputs['USER_FULLNAME'] = cols[0].text_input('Full name', person['USER_FULLNAME'])
inputs['USER_EMAIL'] = cols[1].text_input('Email', person['USER_EMAIL'])
inputs['USER_NAME'] = cols[2].text_input('Username', person['USER_NAME'])

cols = st.columns(2)
mentors = list(user_df['USER_MENTOR'].cat.categories)
inputs['USER_TYPE'] = cols[0].segmented_control('Role', options = user_df['USER_TYPE'].cat.categories, default = person['USER_TYPE'])
inputs['USER_MENTOR'] = cols[1].selectbox('Mentor', mentors, mentors.index(person['USER_MENTOR']) if person['USER_MENTOR'] in mentors else None, accept_new_options = True)

cols = st.columns([1,7])
pubkey = cols[0].segmented_control('Use public key from', options = ['Text', 'GitHub'], default='Text')
if pubkey == 'Text':
    inputs['USER_PUBKEY'] = cols[1].text_area('Public key', checknan(person['USER_PUBKEY'], ''))
    inputs['USER_PUBKEY_FROM_GITHUB'] = checknan(person['USER_PUBKEY_FROM_GITHUB'], '')
else:
    inputs['USER_PUBKEY_FROM_GITHUB'] = cols[1].text_input('Github username', checknan(person['USER_PUBKEY_FROM_GITHUB'], ''))
    inputs['USER_PUBKEY'] = checknan(person['USER_PUBKEY'], '')

if st.session_state.advanced_mode:
    cols = st.columns(2)
    _tags = ['ADMIN', 'DISABLED', 'PURGE_DATA']
    tags = cols[0].multiselect(
        'Tags',
        _tags,
        default=[_tags[i] 
                for i,v in enumerate(['ADMIN_USER_ACCESS', 'DISABLED', 'PURGE_USER_DATA'])
                if checknan(person[v], False)],
        key=f'user-tags')
    inputs['ADMIN_USER_ACCESS'] = 'ADMIN' in tags
    inputs['DISABLED'] = 'DISABLED' in tags
    inputs['PURGE_USER_DATA'] = 'PURGE_DATA' in tags
    inputs['ADDITIONAL_PRIVATE_DATA_MOUNT_GROUPS'] = cols[1].multiselect('Additional private data mount groups', set(itertools.chain(*user_df['ADDITIONAL_PRIVATE_DATA_MOUNT_GROUPS'].dropna().values)), default = person['ADDITIONAL_PRIVATE_DATA_MOUNT_GROUPS'] or None, accept_new_options=True)

# Make sure we write back only things that actually changed
for k,v in inputs.items():
    row_index = user_df.index[id]
    if isinstance(v, str):
        if person[k] != v:
            user_df.loc[row_index, k] = v if v != '' else None
    elif isinstance(v, list):
        if person[k] != v:
            user_df.loc[row_index, k] = v if v != [] else None
    elif isinstance(v, bool):
        if person[k] != v:
            user_df.loc[row_index, k] = v if v != False else None
    elif v == None:
        if person[k] != v:
            user_df.loc[row_index, k] = None            
    else:
        raise ValueError(f'Unexpected type for key \'{k}\'', v)

# Containers
mask = container_df['USER_EMAIL'] == person['USER_EMAIL']
shown_containers = container_df[mask]
shown_index = container_df.index[mask]

@st.dialog('Confirm container deletion')
def confirm_delete(idx):
    st.write(f'Are you sure you want to delete container \'{shown_containers.loc[shown_index[i], "STACK_NAME"]}\'?')
    
    _, left, right = st.columns([0.7, 0.15, 0.15])
    if left.button('No'):
        st.rerun()
    if right.button('Yes', type='primary'):
        container_df.drop(shown_index[idx], inplace=True)
        st.rerun()
    

for i in range(len(shown_containers)):
    c = shown_containers.iloc[i]
    
    with st.expander(f'Container: {c["STACK_NAME"]}'):
        container.show_ui(shown_index[i], key=i)
    
        if st.button('Delete', key=f'c{i}-del', type='primary'):
            confirm_delete(i)
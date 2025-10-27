import streamlit as st
import itertools
import container
from confirmation import confirmation
import random
import unicodedata

container_df = st.session_state['container_df']

def checknan(x, default):
    if x == x:
        return x
    return default

if 'selected_user' not in st.session_state:
    st.switch_page('manage-users.py')

group, id = st.session_state['selected_user']
user_df = st.session_state['user_df'][group]
person = user_df.loc[id]

inputs = {}

cols = st.columns(3)
inputs['USER_FULLNAME'] = cols[0].text_input('Full name', person['USER_FULLNAME'])
inputs['USER_EMAIL'] = cols[1].text_input('Email', person['USER_EMAIL'])
inputs['USER_NAME'] = cols[2].text_input('Username', checknan(person['USER_NAME'], None))

cols = st.columns(2)
mentors = st.session_state['mentors']
if person['USER_MENTOR'] == person['USER_MENTOR'] and person['USER_MENTOR'] not in mentors:
    mentors = mentors + [person['USER_MENTOR']]

roles = st.session_state['roles']
inputs['USER_TYPE'] = cols[0].segmented_control('Role', roles, default = checknan(person['USER_TYPE'], 'student'), key='user-role')
inputs['USER_MENTOR'] = cols[1].selectbox('Mentor', mentors, mentors.index(person['USER_MENTOR']) if person['USER_MENTOR'] in mentors else None, accept_new_options = True)

cols = st.columns([1,6])
pubkey_source = 'Text' if type(person['USER_PUBKEY']) == str and len(person['USER_PUBKEY']) > 0 else 'GitHub'
pubkey = cols[0].segmented_control('Use public key from', options = ['Text', 'GitHub'], default=pubkey_source)
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
    
    groups = set(itertools.chain(*user_df['ADDITIONAL_PRIVATE_DATA_MOUNT_GROUPS'].dropna().values))
    inputs['ADDITIONAL_PRIVATE_DATA_MOUNT_GROUPS'] = cols[1].multiselect(
        'Additional private data mount groups',
        groups,
        default = checknan(person['ADDITIONAL_PRIVATE_DATA_MOUNT_GROUPS'], None),
        accept_new_options=True)

# Make sure we write back only things that actually changed
for k,v in inputs.items():
    if isinstance(v, str):
        if person[k] != v:
            user_df.loc[id, k] = v if v != '' else None
    elif isinstance(v, list):
        if person[k] != v:
            user_df.loc[id, k] = v if v != [] else None
    elif isinstance(v, bool):
        if person[k] != v:
            user_df.loc[id, k] = v if v != False else None
    elif v == None:
        if person[k] == person[k] and person[k] != v:
            user_df.loc[id, k] = None
    else:
        raise ValueError(f'Unexpected type for key \'{k}\'', v)

confirm_delete = confirmation('Confirm container deletion')

# Containers
for container_group, df in container_df.items():
    mask = df['USER_EMAIL'] == person['USER_EMAIL']
    shown_containers = df[mask]
    shown_index = df.index[mask]

    if inputs['USER_EMAIL'] != person['USER_EMAIL'] and len(inputs['USER_EMAIL']):
        df.loc[mask, 'USER_EMAIL'] = inputs['USER_EMAIL']

    for i in range(len(shown_containers)):
        c = shown_containers.iloc[i]

        with st.expander(f'Container: {c["STACK_NAME"]}'):
            container.show_ui(group, container_group, shown_index[i], key=f'{container_group}-{i}')

            id = shown_index[i]
            if st.button('Delete', key=f'c{container_group}-{i}-del', type='primary'):
                # this is a bit of a hack to make sure the callback references
                # the correct values instead of the last ones
                get_callback = lambda df, id: lambda: df.drop(id, inplace=True)
                confirm_delete(
                    f'Are you sure you want to delete container \'{c["STACK_NAME"]}\'?',
                    get_callback(df, id))

if st.button('', icon=':material/add:'):
    rand = f'{random.getrandbits(20):05x}'
    container_name = f'unnamed-container-{rand}'
    name = unicodedata.normalize('NFKD', person['USER_FULLNAME']).encode('ascii','ignore').decode().lower().split(' ')
    container.add_container_with_defaults(container_df[group], name + [rand], container_name, person['USER_EMAIL'])
    st.rerun()

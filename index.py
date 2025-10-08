import streamlit as st
from yamlhandler import load_users, load_containers, load_nodes

#st.login()

_nodes_yaml = '../inventory/vicos.yml'
_user_yaml = '../inventory/group_vars/ccc-cluster/user-list.yml'
_container_yaml = '../inventory/group_vars/ccc-cluster/user-containers.yml'

nav_pages = [
    st.Page('manage-users.py', icon=":material/person:", title="Manage users"),
    st.Page('commit.py', icon=":material/settings:", title="Review changes", url_path="review"),
]
hidden_pages = [
    st.Page('edit-user.py', icon=":material/settings:", title="Edit user", url_path="user"),
]

st.html('''
<style>
.st-key-global-options {
    position: absolute;
    bottom: 15px;
    padding-right: 20px;
}
</style>
''')

current_page = st.navigation(pages=nav_pages + hidden_pages, position='hidden')

st.sidebar.write('## ccc-inventory')
for page in nav_pages:
    st.sidebar.page_link(page)

st.set_page_config(layout="wide")

if not hasattr(st.session_state, 'delete_confirmation'):
    st.session_state['delete_confirmation'] = 0
if not hasattr(st.session_state, 'mentor_view'):
    st.session_state['mentor_view'] = None
    
if not hasattr(st.session_state, 'nodes'):
    with open(_nodes_yaml) as f:
        load_nodes(st.session_state, f)
    
if not hasattr(st.session_state, 'user_df'):
    with open(_user_yaml) as f:
        load_users(st.session_state, f)

if not hasattr(st.session_state, 'container_df'):
    with open(_container_yaml) as f:
        load_containers(st.session_state, f)

with st.sidebar.container(key='global-options'):
    if 'advanced_mode' not in st.session_state:
        st.session_state.advanced_mode = False

    st.session_state['mentor_view'] = st.selectbox('View as mentor', st.session_state['mentors'], None, placeholder='View as mentor', label_visibility='hidden')
    a = st.toggle('Show extra options', st.session_state.advanced_mode, key='advanced-toggle')
    if a != st.session_state.advanced_mode:
        st.session_state.advanced_mode = a

st.title(f"{current_page.icon} {current_page.title}")

current_page.run()

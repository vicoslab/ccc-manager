import streamlit as st
import config
from yamlhandler import load_users, load_containers, load_nodes

#st.login()

nav_pages = [
    st.Page('manage-users.py', icon=":material/person:", title="Manage users"),
    st.Page('commit.py', icon=":material/settings:", title="Apply changes", url_path="apply"),
]
hidden_pages = [
    st.Page('lost-containers.py', icon=":material/deployed_code:", title="Orphaned containers", url_path="containers"),
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
    with open(config.nodes) as f:
        load_nodes(st.session_state, f)
    
if not hasattr(st.session_state, 'user_df'):
    with open(config.users) as f:
        load_users(st.session_state, f)

if not hasattr(st.session_state, 'container_df'):
    with open(config.containers) as f:
        load_containers(st.session_state, f)

with st.sidebar.container(key='global-options'):
    if 'advanced_mode' not in st.session_state:
        st.session_state.advanced_mode = False
    if 'view_deleted' not in st.session_state:
        st.session_state.view_deleted = False

    st.session_state['mentor_view'] = st.selectbox('View as mentor', st.session_state['mentors'], None, placeholder='View as mentor', label_visibility='hidden')
    st.session_state.advanced_mode = st.toggle('Show extra options', st.session_state.advanced_mode, key='advanced-toggle')
    st.session_state.view_deleted = st.toggle('Show disabled users', st.session_state.view_deleted, key='deleted-toggle')

st.title(f"{current_page.icon} {current_page.title}")

current_page.run()

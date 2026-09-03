import streamlit as st
import config
from yamlhandler import load_users, load_containers, load_nodes, has_pending_changes
import subprocess
import time
import logs

# How often (in seconds) we are willing to contact the remote to check for new commits.
FETCH_INTERVAL_SECONDS = 60
# How long we wait, with no local (uncommitted) changes, before automatically pulling
# in remote changes without requiring the user to click the "Sync now" button.
AUTO_SYNC_INTERVAL_SECONDS = 10 * 60

def get_current_git_head():
    result = subprocess.run(
        ['git', 'rev-parse', 'HEAD'],
        cwd='/opt/ccc-inventory',
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f'Warning: could not read git HEAD: {result.stderr.strip()}', flush=True)
        return None
    return result.stdout.strip()

def get_upstream_git_head():
    result = subprocess.run(
        ['git', 'rev-parse', '@{u}'],
        cwd='/opt/ccc-inventory',
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()

def fetch_remote():
    result = subprocess.run(
        ['git', 'fetch', '--prune'],
        cwd='/opt/ccc-inventory',
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f'Warning: could not fetch remote changes: {result.stderr.strip()}', flush=True)

def sync_inventory():
    result = subprocess.run(
        ['git', 'pull', '--ff-only'],
        cwd='/opt/ccc-inventory',
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f'Warning: could not pull remote changes: {result.stderr.strip()}', flush=True)
    with open(config.users) as f:
        st.session_state['_user_plaintext'] = f.read()
    load_users(st.session_state)
    with open(config.containers) as f:
        st.session_state['_container_plaintext'] = f.read()
    load_containers(st.session_state)
    st.session_state['_last_sync_time'] = time.time()

#st.login()

nav_pages = [
    st.Page('manage-users.py', icon=":material/person:", title="Manage users"),
    st.Page('commit.py', icon=":material/settings:", title="Apply changes", url_path="apply"),
]

if config.PORTAINER_TOKEN is not None:
    nav_pages.append(st.Page('container-dashboard.py', icon=":material/deployed_code_alert:", title="Deployed containers", url_path="dashboard"))

hidden_pages = [
    st.Page('lost-containers.py', icon=":material/deployed_code:", title="Orphaned containers", url_path="containers"),
    st.Page('edit-user.py', icon=":material/settings:", title="Edit user", url_path="user"),
    st.Page('raw-config.py', icon=":material/code:", title="YAML configuration files", url_path="config"),
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

st.sidebar.write('## ccc-manager')
for page in nav_pages:
    st.sidebar.page_link(page)

st.set_page_config(layout="wide")

if not hasattr(st.session_state, 'init_done'):
    st.session_state['delete_confirmation'] = 0
    st.session_state['mentor_view'] = None
    if config.PORTAINER_TOKEN is not None:
        with st.spinner('Initializing portainer integration'):
            st.session_state['portainer'] = logs.init(config.PORTAINER_URL, config.PORTAINER_TOKEN)
    with st.spinner("Fetching changes from git..."):
        fetch_remote()
        st.session_state['_last_fetch_time'] = time.time()
    with st.spinner("Loading yaml...", show_time=True):
        with open(config.nodes) as f:
            load_nodes(st.session_state, f)
        sync_inventory()
    st.session_state.init_done = True

with st.sidebar.container(key='global-options'):
    if 'advanced_mode' not in st.session_state:
        st.session_state.advanced_mode = False
    if 'view_deleted' not in st.session_state:
        st.session_state.view_deleted = False

    st.session_state['mentor_view'] = st.selectbox('View as mentor', st.session_state['mentors'], None, placeholder='View as mentor', label_visibility='hidden')
    st.session_state.advanced_mode = st.toggle('Show extra options', st.session_state.advanced_mode, key='advanced-toggle')
    st.session_state.view_deleted = st.toggle('Show disabled users', st.session_state.view_deleted, key='deleted-toggle')

now = time.time()
if now - st.session_state.get('_last_fetch_time', 0) > FETCH_INTERVAL_SECONDS:
    fetch_remote()
    st.session_state['_last_fetch_time'] = now

current_head = get_current_git_head()
upstream_head = get_upstream_git_head()
remote_diverged = bool(upstream_head) and upstream_head != current_head

if remote_diverged:
    pending_changes = has_pending_changes(st.session_state)

    # Automatically pull in remote changes once enough time has passed since the
    # last sync, but only if the user has no unsaved local edits that could conflict.
    if not pending_changes and now - st.session_state.get('_last_sync_time', 0) > AUTO_SYNC_INTERVAL_SECONDS:
        sync_inventory()
        st.rerun()

    with st.sidebar:
        st.warning(
            'The inventory was updated by another user. '
            + ('Syncing will discard any unsaved changes.' if pending_changes else 'Click below to fetch the latest changes.'),
            icon='⚠️',
        )
        if st.button('🔄 Sync now', key='sync-notification', use_container_width=True):
            sync_inventory()
            st.rerun()

st.title(f"{current_page.icon} {current_page.title}")

current_page.run()

import streamlit as st
from yamlhandler import save_users, save_containers, load_users, load_containers
import subprocess
import tempfile
from ansi2html import Ansi2HTMLConverter
from confirmation import confirmation
import config

conv = Ansi2HTMLConverter()
convert = lambda x: f'<div>{conv.convert(x, full=False)}</div>'

base_diff = subprocess.run(
    ['git', 'diff', '--color', '--ws-error-highlight=all'],
    cwd='/opt/ccc-inventory',
    capture_output=True
).stdout.decode().splitlines()

if base_diff:
    print('Warning: found unmanaged changes, deleting')
    subprocess.run(['git', 'restore', '.'], cwd='/opt/ccc-inventory')

st.session_state.diff_size = 0
with tempfile.NamedTemporaryFile('w') as f:
    save_users(st.session_state, f)
    f.write('\0x04')
    user_diff = subprocess.run(
        ['git', 'diff', '--no-index', '--color', '--ws-error-highlight=all', '-p', '--numstat', config.users, f.name],
        capture_output=True
    ).stdout.decode().splitlines()
    
    # parse numstat line and skip it
    if user_diff:
        add, del_, _ = user_diff[0].split('\t', maxsplit=3)
        st.session_state.diff_size += int(add) + int(del_)
        user_diff = user_diff[2:]

with tempfile.NamedTemporaryFile('w') as f:
    save_containers(st.session_state, f)
    f.write('\0x04')
    container_diff = subprocess.run(
        ['git', 'diff', '--no-index', '--color', '--ws-error-highlight=all', '-p', '--numstat', config.containers, f.name],
        capture_output=True
    ).stdout.decode().splitlines()

    # parse numstat line and skip it
    if container_diff:
        add, del_, _ = container_diff[0].split('\t', maxsplit=3)
        st.session_state.diff_size += int(add) + int(del_)
        container_diff = container_diff[2:]


confirm_discard = confirmation('Confirm discard')
def discard():
    with open(config.users) as f:
        load_users(st.session_state, f)

    with open(config.containers) as f:
        load_containers(st.session_state, f)

@st.dialog('Commit changes', width='large')
def commit():
    with st.form('commit-form'):
        message = st.text_input('Short description of the changes')
        if st.form_submit_button('Commit') and message:
            with open(config.users, 'w') as f:
                save_users(st.session_state, f)
                
            with open(config.containers, 'w') as f:
                save_containers(st.session_state, f)
            p = subprocess.run(['bash', 'commit.sh', message], capture_output=True)
            # Don't discard if script failed as that would import uncommitted changes and no longer show them
            # The changes which we saved will get reverted from the file upon rerun
            if p.returncode == 0:
                discard()
                st.rerun()
            else:
                out = p.stdout.decode().splitlines()
                st.write(':red[Could not pull with rebase. Remove any changes causing a merge conflict.]')
                st.divider()
                st.html(f'''
                    {conv.produce_headers()}
                    <pre class='ansi2html-content'>{''.join(map(convert, out))}</pre>
                ''')

if st.session_state.diff_size > 0:
    with st.container(horizontal=True):
        if st.session_state.diff_size > 20:
            with st.popover('Save'):
                st.write('Large diff detected. Are you sure you want to save?')
                with st.container(horizontal=True, horizontal_alignment='right'):
                    if st.button('Yes'):
                        commit()
        elif st.button("Save"):
            commit()

        if st.button('Discard changes', type='primary'):
            confirm_discard('Are you sure you want to discard changes?', discard)

st.write('## Changes in user configuration')
if user_diff:
    st.html(f'''
        {conv.produce_headers()}
        <pre class='ansi2html-content'>{''.join(map(convert, user_diff))}</pre>
    ''')
else:
    st.write('No changes')

st.write('## Changes in container configuration')
if container_diff:
    st.html(f'''
        {conv.produce_headers()}
        <pre class='ansi2html-content'>{''.join(map(convert, container_diff))}</pre>
    ''')
else:
    st.write('No changes')

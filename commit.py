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

def diff(stdin, filename, *flags):
    default_flags = ['--no-index', '--color', '--ws-error-highlight=all']
    return subprocess.run(
        ['git', 'diff', *default_flags, *flags, '-', filename],
        capture_output=True,
        input=stdin,
        text=True,
    ).stdout

def process_diff(original_text, save_fn, filename):
    with tempfile.NamedTemporaryFile('w') as f:

        save_fn(st.session_state, f)
        f.write('\0x04')
        
        stat = diff(original_text, f.name, '--numstat')
        
        # parse numstat line and skip it
        if stat:
            add, del_, _ = stat.split('\t', maxsplit=3)
            st.session_state.diff_size += int(add) + int(del_)
            
            d = diff(original_text, f.name).splitlines(keepends=True)
            
            for i in range(4):
                d[i] = d[i].replace('a/-', 'a/' + filename)
                d[i] = d[i].replace(f.name[1:], filename)
        else:
            d = []
    return d

st.session_state.diff_size = 0
user_filename = config.users[len(config.INVENTORY_DIR)+1:]
user_diff = process_diff(st.session_state['_user_plaintext'], save_users, user_filename)

container_filename = config.containers[len(config.INVENTORY_DIR)+1:]
container_diff = process_diff(st.session_state['_container_plaintext'], save_containers, container_filename)

confirm_discard = confirmation('Confirm discard')
def discard():
    load_users(st.session_state)
    load_containers(st.session_state)

@st.dialog('Commit changes', width='large')
def commit():
    with st.form('commit-form'):
        message = st.text_input('Short description of the changes')
        if st.form_submit_button('Commit') and message:
            with tempfile.NamedTemporaryFile('w') as f:
                f.writelines(user_diff + [] + container_diff + [])
                f.write('\0x04')
                f.flush()
                p = subprocess.run(['bash', 'commit.sh', f.name, message], capture_output=True)
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

st.header(':blue[Changes in user configuration]', divider='blue')
if user_diff:
    st.html(f'''
        {conv.produce_headers()}
        <pre class='ansi2html-content'>{''.join(map(convert, user_diff))}</pre>
    ''')
else:
    st.write('No changes')

st.header(':blue[Changes in container configuration]', divider='blue')
if container_diff:
    st.html(f'''
        {conv.produce_headers()}
        <pre class='ansi2html-content'>{''.join(map(convert, container_diff))}</pre>
    ''')
else:
    st.write('No changes')

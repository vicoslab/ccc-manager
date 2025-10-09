import streamlit as st
import pandas as pd
import numpy as np
from yamlhandler import save_users, save_containers, load_users, load_containers
import subprocess
import tempfile
from ansi2html import Ansi2HTMLConverter
from confirmation import confirmation
import config

conv = Ansi2HTMLConverter()
convert = lambda x: f'<div>{conv.convert(x, full=False)}</div>'

st.session_state.diff_size = 0
with tempfile.NamedTemporaryFile('w') as f:
    save_users(st.session_state, f)
    f.write('\0x04')
    user_diff = subprocess.run(
        ['git', 'diff', '--no-index', '--color', '--ws-error-highlight=all', config.users, f.name],
        capture_output=True
    ).stdout.decode().splitlines()
    st.session_state.diff_size += len(user_diff)

with tempfile.NamedTemporaryFile('w') as f:
    save_containers(st.session_state, f)
    f.write('\0x04')
    container_diff = subprocess.run(
        ['git', 'diff', '--no-index', '--color', '--ws-error-highlight=all', config.containers, f.name],
        capture_output=True
    ).stdout.decode().splitlines()
    st.session_state.diff_size += len(container_diff)


confirm_discard = confirmation('Confirm discard')
def discard():
    with open(config.users) as f:
        load_users(st.session_state, f)

    with open(config.containers) as f:
        load_containers(st.session_state, f)

@st.dialog('Commit changes')
def commit():
    with st.form('commit-form'):
        message = st.text_input('Short description of the changes')
        if st.form_submit_button('Commit'):
            with open(config.users, 'w') as f:
                save_users(st.session_state, f)
                
            with open(config.containers, 'w') as f:
                save_containers(st.session_state, f)
            subprocess.run(['bash', 'commit.sh', message])
            st.rerun()

if st.session_state.diff_size > 0:
    with st.container(horizontal=True):
        if st.session_state.diff_size > 50:
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

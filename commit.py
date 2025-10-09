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

st.write('## Changes in user configuration')
with tempfile.NamedTemporaryFile('w') as f:
    save_users(st.session_state, f)
    f.write('\0x04')
    diff = subprocess.run(
        ['git', 'diff', '--no-index', '--color', '--ws-error-highlight=all', config.users, f.name],
        capture_output=True
    ).stdout.decode().splitlines()
    
    if diff:
        # warn if diff is large?

        st.html(f'''
            {conv.produce_headers()}
            <pre class='ansi2html-content'>{''.join(map(convert, diff))}</pre>
        ''')
    else:
        st.write('No changes')

st.write('## Changes in container configuration')
with tempfile.NamedTemporaryFile('w') as f:
    save_containers(st.session_state, f)
    f.write('\0x04')
    diff = subprocess.run(
        ['git', 'diff', '--no-index', '--color', '--ws-error-highlight=all', config.containers, f.name],
        capture_output=True
    ).stdout.decode().splitlines()
    
    if diff:
        # warn if diff is large?

        st.html(f'''
            {conv.produce_headers()}
            <pre class='ansi2html-content'>{''.join(map(convert, diff))}</pre>
        ''')
    else:
        st.write('No changes')


confirm_discard = confirmation('Confirm discard')
def discard():
    with open(config.users) as f:
        load_users(st.session_state, f)

    with open(config.containers) as f:
        load_containers(st.session_state, f)

with st.container(horizontal=True):
    if st.button("Save"):
        with open(config.users, 'w') as f:
            save_users(st.session_state, f)
            
        with open(config.containers, 'w') as f:
            save_containers(st.session_state, f)

    if st.button('Discard changes', type='primary'):
        confirm_discard('Are you sure you want to discard changes?', discard)

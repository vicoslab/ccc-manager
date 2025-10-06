import streamlit as st
import pandas as pd
import numpy as np
from yamlhandler import save_users, save_containers
import subprocess
import tempfile
from ansi2html import Ansi2HTMLConverter

_user_yaml = '../inventory/group_vars/ccc-cluster/user-list.yml'
_container_yaml = '../inventory/group_vars/ccc-cluster/user-containers.yml'
    
conv = Ansi2HTMLConverter()
convert = lambda x: f'<div>{conv.convert(x, full=False)}</div>'

st.write('## Changes in user configuration')
with tempfile.NamedTemporaryFile('w') as f:
    save_users(st.session_state, f)
    f.write('\0x04')
    diff = subprocess.run(
        ['git', 'diff', '--no-index', '--color', '--ws-error-highlight=all', _user_yaml, f.name],
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
        ['git', 'diff', '--no-index', '--color', '--ws-error-highlight=all', _container_yaml, f.name],
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

if st.button("Save"):
    with open(_user_yaml, 'w') as f:
        save_users(st.session_state, f)
        
    with open(_container_yaml, 'w') as f:
        save_containers(st.session_state, f)

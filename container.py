import streamlit as st
import pandas as pd
import numpy as np
import itertools
import math
from image_info import get_available_images

df_columns = {
    'STACK_NAME': 'Container name',
    'STORAGE_NAME': 'Storage name',
    'USER_EMAIL': 'User email',
    'CONTAINER_IMAGE': 'Docker image',
    'INSTALL_PACKAGES': 'Packages',
    'RUN_PRIVILEGED': 'Privileged',
    'ENABLE_DOCKER_ACCESS': 'Docker access',
    'SHM_SIZE': 'Shared memory',
    'FRP_PORTS': 'FRP ports',
    'ALLOWED_NODES': 'Allowed nodes',
    'DEPLOYMENT_NODES': 'Deployment nodes',
    'EXTRA_ENVS': 'Extra envs',
    'DISABLED': 'Disabled',
}

def checknan(x, default):
    if x == x:
        return x
    return default


def add_container_with_defaults(df, name, email):
    # all base images with cuda (they already come sorted descending by version)
    images = [x for x in get_available_images() if ':base-' in x and 'cuda' in x]
    df.loc[len(df), ['STACK_NAME', 'USER_EMAIL', 'CONTAINER_IMAGE', 'FRP_PORTS']] = [
        name,
        email,
        images[0],
        { 'TCP': [22] },
    ]

def show_ui(user_group, container_group, id, key=None):
    container_df = st.session_state['container_df'][container_group]
    user_df = st.session_state['user_df'][user_group]
    container = container_df.loc[id]

    if 'available_images' not in st.session_state:
        st.session_state.available_images = get_available_images()
    images = st.session_state.available_images
    # we don't use set here to keep the ordering
    images += [x for x in container_df['CONTAINER_IMAGE'].cat.categories if x not in images]

    inputs = {}
    inputs['USER_EMAIL'] = container['USER_EMAIL']
    
    cols = st.columns(2)
    inputs['STACK_NAME'] = cols[0].text_input('Container name', container['STACK_NAME'], key=f'c{key}-stack')
    #inputs['STORAGE_NAME'] = st.text_input('Storage name', container['STORAGE_NAME'], key=f'c{key}-storage'),
    inputs['CONTAINER_IMAGE'] = cols[1].selectbox(
        'Docker image',
        images,
        index = images.index(container['CONTAINER_IMAGE']) if container['CONTAINER_IMAGE'] in images else None,
        accept_new_options = True,
        key=f'c{key}-image')
    
    if st.session_state.advanced_mode:
        inputs['INSTALL_PACKAGES'] = st.multiselect(
            'Additional packages to install',
            set(itertools.chain(*container_df['INSTALL_PACKAGES'].dropna().values)),
            default = container['INSTALL_PACKAGES'] or None,
            accept_new_options=True,
            key=f'c{key}-pkgs')
        
        cols = st.columns([3,1])
        _tags = ['DISABLED', 'DOCKER', 'PRIVILEGED']
        tags = cols[0].multiselect(
            'Tags',
            _tags,
            default=[_tags[i] 
                    for i,v in enumerate(['DISABLED', 'ENABLE_DOCKER_ACCESS', 'RUN_PRIVILEGED'])
                    if checknan(container[v], False)],
            key=f'c{key}-tags')
        inputs['DISABLED'] = 'DISABLED' in tags
        inputs['ENABLE_DOCKER_ACCESS'] = 'DOCKER' in tags
        inputs['RUN_PRIVILEGED'] = 'PRIVILEGED' in tags
        inputs['SHM_SIZE'] = cols[1].text_input('Shared memory size', container['SHM_SIZE'], key=f'c{key}-shm')
        
        inputs['FRP_PORTS'] = ports = container['FRP_PORTS'].copy()
        cols = st.columns(2)
        inputs['FRP_PORTS']['TCP'] = cols[0].multiselect('TCP ports',
            ports['TCP'] if 'TCP' in ports else [22],
            default=ports['TCP'] if 'TCP' in ports else [22],
            accept_new_options=True,
            key=f'c{key}-tcp')
        
        cols[1].html('<label><p style="margin: 0; font-size: 0.875rem; margin-bottom: -0.6rem;">HTTP ports</p></label>')
        flex = cols[1].container(horizontal=True, key=f'c{key}-flexhttp')
        
        @st.dialog('Edit http port', on_dismiss='rerun')
        def edit_http(i):

            http = container['FRP_PORTS']['HTTP'][i]
            
            with st.form('Edit HTTP port'):
                cols = st.columns(2)
                
                inputs = {}
                inputs['user'] = cols[0].text_input('User', http['user'] if 'user' in http else None, placeholder=user_df.loc[container['USER_EMAIL']]['USER_NAME'])
                inputs['pass'] = cols[1].text_input('Password', http['pass'] if 'pass' in http else None)
                
                cols = st.columns(2)
                inputs['port'] = cols[0].text_input('Port', http['port'])
                inputs['https_without_pass'] = cols[1].checkbox('HTTPS without pass', 'https_without_pass' in http and http['https_without_pass'])
                inputs['health_check'] = cols[1].checkbox('Health check', 'health_check' in http and http['health_check'] == 'true')
                
                inputs['subdomain'] = cols[0].text_input('Subdomain', http['subdomain'])
                inputs['subdomain_hostname_prefix'] = cols[1].checkbox('Subdomain hostname prefix', 'subdomain_hostname_prefix' not in http or http['subdomain_hostname_prefix'])

                with st.container(horizontal=True):
                    if st.form_submit_button('Save', key='port-save'):
                        inputs['health_check'] = 'true' if inputs['health_check'] else 'false'
                        order = ['port', 'subdomain', 'user', 'pass', 'https_without_pass', 'health_check', 'subdomain_hostname_prefix']
                        container['FRP_PORTS']['HTTP'][i] = {k: inputs[k] for k in order}
                        st.rerun()

                    if st.form_submit_button('Delete', type='primary', key='port-delete'):
                        ports['HTTP'].pop(i)
                        st.rerun()
        
        if 'HTTP' in ports:
            for i,http in enumerate(ports['HTTP']):
                
                http = ports['HTTP'][i]
                if 'subdomain_hostname_prefix' not in http or http['subdomain_hostname_prefix']:
                    host_prefix = '<host>-'
                else:
                    host_prefix = ''
                if flex.button(f'{host_prefix+http["subdomain"]} `{http["port"]}`'):
                    edit_http(i)

        if flex.button('', icon=':material/add:', key=f'c{key}-newhttp'):
            if 'HTTP' not in ports:
                ports['HTTP'] = []
            i = len(ports['HTTP'])
            ports['HTTP'].append({ 'port': '', 'subdomain': '' })
            edit_http(i)
        
        #inputs['FRP_PORTS'] = st.text_area('FRP ports [YAML]', container['FRP_PORTS'], key=f'c{key}-frp')
        
        cols = st.columns(2)
        inputs['ALLOWED_NODES'] = cols[0].multiselect(
            'Allowed nodes',
            set(itertools.chain(*container_df['ALLOWED_NODES'].dropna().values)),
            default = checknan(container['ALLOWED_NODES'], None),
            accept_new_options=True,
            key=f'c{key}-nallow')
        inputs['DEPLOYMENT_NODES'] = cols[1].multiselect(
            'Deployment nodes',
            set(itertools.chain(*container_df['DEPLOYMENT_NODES'].dropna().values)),
            default = checknan(container['DEPLOYMENT_NODES'], None),
            accept_new_options=True,
            key=f'c{key}-ndeploy')
        
        inputs['EXTRA_ENVS'] = container['EXTRA_ENVS'].copy() if container['EXTRA_ENVS'] else {}
        cols[1].html('<label><p style="margin: 0; font-size: 0.875rem; margin-bottom: -0.6rem;">Extra environment variables</p></label>')
        flex = cols[1].container(horizontal=True, key=f'c{key}-flexenvs')
        
        @st.dialog('Edit environment variable', on_dismiss='rerun')
        def edit_env(key=None):

            cols = st.columns(2)
            k = cols[0].text_input('Key', key)
            v = cols[1].text_input('Value', container['EXTRA_ENVS'][k] if container['EXTRA_ENVS'] and k in container['EXTRA_ENVS'] else None)

            if k:
                inputs['EXTRA_ENVS'][k] = v

                if container['EXTRA_ENVS'] != inputs['EXTRA_ENVS']:
                    container_df.at[id, 'EXTRA_ENVS'] = inputs['EXTRA_ENVS'] or None

            if st.button('Delete', type='primary') and k:
                del inputs['EXTRA_ENVS'][k]
                
                if container['EXTRA_ENVS'] != inputs['EXTRA_ENVS']:
                    container_df.at[id, 'EXTRA_ENVS'] = inputs['EXTRA_ENVS'] or None
                st.rerun()

        if container['EXTRA_ENVS']:
            for k in container['EXTRA_ENVS']:
                if flex.button(k):
                    edit_env(k)
            
        if flex.button('', icon=':material/add:', key=f'c{key}-newenv'):
            edit_env()
    
    if 'HTTP' in container['FRP_PORTS']:
        http = container['FRP_PORTS']['HTTP']
        if 'user' in http and not http['user']:
            del http['user']
        if 'https_without_pass' in http and not http['https_without_pass']:
            del http['https_without_pass']
        # default is true
        if 'subdomain_hostname_prefix' in http and http['subdomain_hostname_prefix']:
            del http['subdomain_hostname_prefix']
    
    for k,v in inputs.items():
        if isinstance(v, str):
            if container[k] != v:
                container_df.at[id, k] = v if v != '' else None
        elif isinstance(v, list):
            if container[k] != v:
                container_df.at[id, k] = v if v != [] else None
        elif isinstance(v, bool):
            if container[k] != v:
                container_df.at[id, k] = v if v != False else None
        elif isinstance(v, dict):
            if container[k] != v:
                container_df.at[id, k] = v if v != {} else None
        elif v == None:
            if container[k] != v:
                container_df.at[id, k] = None
        else:
            raise ValueError('Unexpected type', v)
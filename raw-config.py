import copy
import io

import streamlit as st

import config
from yamlhandler import save_containers, save_users


def copy_dataframe_groups(groups):
    return {group: df.copy(deep=True) for group, df in groups.items()}


def build_render_state():
    """Copy only the state needed for YAML rendering.

    The YAML save helpers update their input state while preserving comments and
    formatting. Rendering from a small copied state lets this read-only page show
    the current in-memory configuration without mutating the editor session.
    """
    keys_to_copy = [
        '_user_header_raw',
        '_user_header_researcher',
        '_user_header_student_phd',
        '_user_header_student',
        '_user_header_lkm',
        '_user_data_raw',
        '_container_header_raw',
        '_container_header_researcher',
        '_container_header_student_phd',
        '_container_header_student',
        '_container_header_lkm',
        '_container_data_raw',
    ]
    render_state = {key: copy.deepcopy(st.session_state[key]) for key in keys_to_copy}
    render_state['user_df'] = copy_dataframe_groups(st.session_state['user_df'])
    render_state['container_df'] = copy_dataframe_groups(st.session_state['container_df'])
    return render_state


def render_yaml(save_fn):
    output = io.StringIO()
    save_fn(build_render_state(), output)
    return output.getvalue()


st.write(
    'These are the current YAML configuration files generated from the users and '
    'containers currently loaded in the editor.'
)

user_tab, container_tab = st.tabs(['Users', 'Containers'])

with user_tab:
    st.caption(config.users)
    st.code(render_yaml(save_users), language='yaml')

with container_tab:
    st.caption(config.containers)
    st.code(render_yaml(save_containers), language='yaml')

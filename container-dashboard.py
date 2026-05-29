import streamlit as st
import config
from logs import fetch_logs, format_html, init
from streamlit_theme import st_theme
import re

theme = st_theme()
st.html('''
<style>
/* Keep the deployed-containers dashboard compact so more workspaces fit on one line. */
[class *= st-key-table] [data-testid="stHorizontalBlock"] {
    gap: 0.25rem !important;
}
[class *= st-key-table] [data-testid="stLayoutWrapper"] {
    margin-bottom: 0.125rem;
}
[class *= st-key-table] button {
    min-height: 1.75rem;
    padding: 0.125rem 0.25rem;
}
[class *= st-key-table] button p {
    font-size: 0.875rem;
    line-height: 1rem;
}
</style>
''')

if theme:
    st.html('''
    <style>
    h3 > span {{
        position: absolute;
        top: 50%;
    }}
    button:disabled {{
        cursor: unset !important;
        user-select: text;
    }}
    .stSpinner [data-testid="stMarkdownContainer"] /* fix for markdown content breaking up the timer */ {{
        width: unset;
    }}
    .stLinkButton a {{
        color: cornflowerblue;
        border: 1px solid #518ee778;
    }}
    [class *= st-key-nowrap] button {{
        white-space: nowrap;
        text-overflow: ellipsis;
    }}
    [data-testid="stLayoutWrapper"] {{
        border-bottom: 1px solid transparent;
    }}
    [data-testid="stLayoutWrapper"]:hover {{
        border-color: {fadedText40};
    }}
    [class *= st-key-table] > div:first-child {{
        position: sticky;
        align-self: flex-start;
        top: 50px;
        background: {backgroundColor};
        z-index: 1;
    }}
    </style>
    '''.format(**theme))

if config.PORTAINER_TOKEN is None:
    st.write('Portainer not available')
    st.stop()


def _get_filter_keywords(filter_text):
    return [token.casefold() for token in re.split(r'[\s,;]+', filter_text.strip()) if token]


def _filter_containers(container_lookup, keywords):
    if not keywords:
        return set(container_lookup)

    selected = set()
    for container, email in container_lookup.items():
        haystack = f'{container} {email or ""}'.casefold()
        if any(keyword in haystack for keyword in keywords):
            selected.add(container)
    return selected


def _is_valid_stack_name(stack_name):
    if stack_name is None:
        return False
    if isinstance(stack_name, str):
        return bool(stack_name.strip())
    return stack_name == stack_name


container_lookup = {
    row['STACK_NAME']: row.get('USER_EMAIL')
    for df in st.session_state['container_df'].values()
    for _, row in df.iterrows()
    if _is_valid_stack_name(row.get('STACK_NAME'))
}

filter_text = st.text_input(
    'Filter deployed containers',
    key='dashboard_filter',
    placeholder='Container name or user email keyword',
    help='Separate multiple keywords with spaces, commas, or semicolons. A container is included if any keyword matches its name or email.',
)
filter_keywords = _get_filter_keywords(filter_text)
user_containers = _filter_containers(container_lookup, filter_keywords)

if filter_keywords:
    st.caption(f'Matched {len(user_containers)} of {len(container_lookup)} configured containers. Click Refresh to fetch only these containers.')
else:
    st.caption(f'Showing all {len(container_lookup)} configured containers. Add a filter before Refresh to avoid fetching logs for every container.')

if st.button('Refresh'):
    st.session_state.pop('servers', None)
    st.session_state['servers_filter'] = tuple(filter_keywords)
    st.session_state['refresh_servers'] = True
    st.rerun()

if 'servers' in st.session_state and st.session_state.get('servers_filter') != tuple(filter_keywords):
    st.session_state.pop('servers', None)
    st.info('The filter changed. Click Refresh to fetch deployed container status for the current filter.')
    st.stop()

if 'servers' not in st.session_state and st.session_state.pop('refresh_servers', False):
    with st.spinner('Refreshing containers (this might take a minute)', show_time=True):
        _servers = init(config.PORTAINER_URL, config.PORTAINER_TOKEN)
        st.session_state['servers'] = {}
        for name, (id, containers) in _servers.items():
            user_server_containers = [(k, v) for k, v in containers.items() if k in user_containers]
            if user_server_containers:
                names, values = zip(*user_server_containers)
                l = fetch_logs(config.PORTAINER_URL, config.PORTAINER_TOKEN, id, names, limit=5000)
                st.session_state['servers'][name] = id, dict(zip(names, zip(values, l)))
            else:
                st.session_state['servers'][name] = id, {}
        st.session_state['servers_filter'] = tuple(filter_keywords)

if 'servers' not in st.session_state:
    st.write('Enter an optional filter and click Refresh to load deployed container status.')
    st.stop()

servers = st.session_state['servers']
user_containers = sorted(user_containers)

column_widths = [3] + [0.4] * len(servers)

with st.container(key='table'):
    cols = st.columns(column_widths, gap="small")
    cols[0].subheader('Container')
    for col, title in zip(cols[1:], servers):
        col.subheader(title, text_alignment='center')

    if not user_containers:
        st.write('No containers match the current filter.')

    for c in user_containers:
        cols = st.columns(column_widths, gap="small")
        cols[0].button(c, type='tertiary', disabled=True, key=f'nowrap-{c}')

        for col, (name, (id, containers)) in zip(cols[1:], servers.items()):
            if c in containers:
                info, lines = containers[c]
                text = '🔴'
                if info['State'] == 'running':
                    if lines is None:
                        text = '⚪'
                    else:
                        try:
                            start = len(lines) - 1 - lines[::-1].index((1, 'Starting pre-service scripts in /etc/runit_init.d'))
                            text = '🟡'
                            if any('/etc/runit_init.d/99_welcome_msg.sh' in x for _, x in lines[start:]):
                                text = '🟢'
                        except ValueError:
                            text = '🟣'
                if col.button(text, type='tertiary', key=f'dashboard-{name}-{c}', width='stretch'):
                    @st.dialog(f'`{c}` on `{name}`', width='large')
                    def view_logs():
                        st.link_button('Open in portainer', f'{config.PORTAINER_URL}/#!/{id}/docker/containers/{info["Id"]}', icon=':material/captive_portal:')
                        with st.spinner('Fetching log'):
                            lines = fetch_logs(config.PORTAINER_URL, config.PORTAINER_TOKEN, id, [c])[0]
                        st.html(format_html(lines))
                    view_logs()

            else:
                col.button('/', type='tertiary', key=f'dashboard-{name}-{c}', disabled=True, width='stretch')

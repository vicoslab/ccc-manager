import streamlit as st
import config
from logs import fetch_logs, format_html, init
from itertools import chain

st.html('''
<style>
[class *= st-key-yellow] button {
    border: 1px solid #a38930;
}
[class *= st-key-green] button {
    border: 1px solid forestgreen;
}
[class *= st-key-red] button {
    border: 1px solid #cd2e2e;
}
.stLinkButton a {
    color: skyblue;
    border: 1px solid #87ceeb78;
}
[class *= st-key-nowrap] button {
    white-space: nowrap;
    text-overflow: ellipsis;
}
[data-testid="stLayoutWrapper"] {
    border-bottom: 1px solid transparent;
}
[data-testid="stLayoutWrapper"]:hover {
    border-color: #ffffff66;
}
[class *= st-key-table] > div:first-child {
    position: sticky;
    align-self: flex-start;
    top: 50px;
    background: rgb(14, 17, 23);
    z-index: 1;
}
</style>
''')

if config.PORTAINER_TOKEN is None:
    st.write('Portainer not available')
    st.stop()

user_containers = set(chain(*[list(df['STACK_NAME']) for df in st.session_state['container_df'].values()]))
if 'servers' not in st.session_state:
    with st.spinner('Refreshing containers (this might take a minute)', show_time=True):
        _servers = init(config.PORTAINER_URL, config.PORTAINER_TOKEN)
        st.session_state['servers'] = {}
        for name, (id, containers) in _servers.items():
            names, values = zip(*[(k,v) for k,v in containers.items() if k in user_containers])
            l = fetch_logs(config.PORTAINER_URL, config.PORTAINER_TOKEN, id, names)
            st.session_state['servers'][name] = id, dict(zip(names, zip(values, l)))

if st.button('Refresh'):
    del st.session_state['servers']
    st.rerun()

servers = st.session_state['servers']
user_containers = sorted(user_containers)

ncols = len(servers) + 1

with st.container(key='table'):
    cols = st.columns(ncols)
    cols[0].subheader('Container')
    for col, title in zip(cols[1:], servers):
        col.subheader(title, text_alignment='center')
        
    for c in user_containers:
        
        cols = st.columns(ncols)
        cols[0].button(c, type='tertiary', disabled=True, key=f'nowrap-{c}')
        
        for col, (name, (id, containers)) in zip(cols[1:], servers.items()):
            if c in containers:
                info, lines = containers[c]
                if info['State'] == 'exited':
                    text = '🔴'
                elif info['State'] == 'running' and any('/etc/runit_init.d/99_welcome_msg.sh' in x for _,x in lines):
                    text = '🟢'
                else:
                    text = '🟡'
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

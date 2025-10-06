import ruamel.yaml
from ruamel.yaml.comments import (CommentedSeq, CommentedMap, Comment,
                                  C_KEY_PRE, C_KEY_EOL, C_KEY_POST,
                                  C_VALUE_PRE, C_VALUE_EOL, C_VALUE_POST)
from ruamel.yaml.tokens import CommentToken
from ruamel.yaml.error import CommentMark
from ruamel.yaml.scalarstring import DoubleQuotedScalarString
import pandas as pd

yaml = ruamel.yaml.YAML(typ=['string'])
yaml.indent(mapping=2, sequence=4, offset=2)
yaml.preserve_quotes = True
yaml.width = 4096
yaml.boolean_representation = ['False', 'True']

def clear_comments(x):
    if isinstance(x, CommentedMap):
        r = CommentedMap({ k: clear_comments(x[k]) for k in x })
        if x.fa.flow_style():
            r.fa.set_flow_style()
        return r
    elif isinstance(x, CommentedSeq):
        r = CommentedSeq([ clear_comments(el) for el in x ])
        if x.fa.flow_style():
            r.fa.set_flow_style()
        return r
    return x

def copy_comments(from_, to):
    if isinstance(from_, CommentedMap):
        for x in from_:
            if x in to:
                copy_comments(from_[x], to[x])
        if len(from_) < len(to):
            # check if key before last has a \n comment
            check = to[list(to.keys())[-2]]
            if isinstance(check, CommentedMap):
                check = check[list(check.keys())[-1]]
            if hasattr(check, 'ca') and check.ca.end and check.ca.end[-1].value == '\n':
                check.ca.end.pop()

    if hasattr(from_, 'ca'):
        to.ca.comment = from_.ca.comment
        to.ca._items = from_.ca.items
        to.ca.end = from_.ca.end

def load_users(state, fd):

    state['_user_data_raw'] = user_data = yaml.load(fd.read())

    user_df = pd.DataFrame(user_data['deployment_users']).transpose()
    if 'ADDITIONAL_DEVICE_GROUPS' not in user_df.columns:
        user_df['ADDITIONAL_DEVICE_GROUPS'] = None

    order = ['USER_FULLNAME','USER_EMAIL','USER_MENTOR','USER_NAME','USER_PUBKEY','USER_PUBKEY_FROM_GITHUB','USER_TYPE', 'ADDITIONAL_DEVICE_GROUPS', 'ADDITIONAL_PRIVATE_DATA_MOUNT_GROUPS', 'ADMIN_USER_ACCESS', 'DISABLED', 'PURGE_USER_DATA']

    # Make sure we don't lose any values when reordering
    a, b = set(order), set(user_df.columns)
    if a != b:
        raise ValueError(f'Mismatch in user columns: {a ^ b}.')

    user_df = user_df[order]
    user_df['USER_TYPE'] = user_df['USER_TYPE'].astype('category')
    user_df['USER_MENTOR'] = user_df['USER_MENTOR'].astype('category')
    user_df['ADDITIONAL_PRIVATE_DATA_MOUNT_GROUPS'] = user_df['ADDITIONAL_PRIVATE_DATA_MOUNT_GROUPS'].apply(lambda x: [] if isinstance(x, float) else list(x))

    state['user_df'] = user_df

def save_users(state, fd):
    edited_user_df = state['user_df']
    user_data = state['_user_data_raw']

    old_data = user_data['deployment_users']
    user_data['deployment_users'] = CommentedMap({ id: CommentedMap({ k: v for k,v in user.items() if v == v and v != None and v != [] }) for id, user in edited_user_df.transpose().to_dict().items()})

    # keep starting comment
    user_data['deployment_users'].ca.comment = old_data.ca.comment

    user_data_keys = list(user_data['deployment_users'])
    for i, (key, x) in enumerate(user_data['deployment_users'].items()):
        
        if 'ADDITIONAL_PRIVATE_DATA_MOUNT_GROUPS' in x:
            x['ADDITIONAL_PRIVATE_DATA_MOUNT_GROUPS'] = CommentedSeq(x['ADDITIONAL_PRIVATE_DATA_MOUNT_GROUPS'])
            x['ADDITIONAL_PRIVATE_DATA_MOUNT_GROUPS'].fa.set_flow_style()

        # find old comments and attach them to new data
        if key in old_data:
            el = old_data[key]
            x.ca.comment = el.ca.comment
            x.ca._items = el.ca.items
            for k in el:
                if k in x and hasattr(x[k], 'ca'):
                    x[k].ca.comment = el[k].ca.comment
                    x[k].ca._items = el[k].ca.items


        # Skip newline in front if previous element ends with ADDITIONAL_PRIVATE_DATA_MOUNT_GROUPS
        if i == 0:
            continue
        last = user_data['deployment_users'][user_data_keys[i-1]]
        lastkey = list(last)[-1]
        if lastkey != 'ADDITIONAL_PRIVATE_DATA_MOUNT_GROUPS' or last[lastkey].ca.end:
            continue

        user_data['deployment_users'].ca.set(key, 1, [CommentToken('\n', column=0, start_mark=CommentMark(0))])

    yaml.dump(user_data, fd)

def load_containers(state, fd):

    state['_container_data_raw'] = container_data = yaml.load(fd.read())

    container_df = pd.DataFrame(container_data['deployment_containers'])
    order = ['STACK_NAME','STORAGE_NAME','USER_EMAIL','CONTAINER_IMAGE','DEPLOYMENT_NODES','ALLOWED_NODES','INSTALL_PACKAGES', 'RUN_PRIVILEGED','ENABLE_DOCKER_ACCESS','SHM_SIZE', 'DISABLED','FRP_PORTS','EXTRA_ENVS']

    # Make sure we don't lose any values when reordering
    a, b = set(order), set(container_df.columns)
    if a != b:
        raise ValueError(f'Mismatch in container columns: {a ^ b}.')

    container_df = container_df[order]
    container_df['CONTAINER_IMAGE'] = container_df['CONTAINER_IMAGE'].astype('category')
    container_df['INSTALL_PACKAGES'] = container_df['INSTALL_PACKAGES'].apply(lambda x: x.split(' '))
    container_df['STORAGE_NAME'] = container_df['STORAGE_NAME'].apply(lambda x: x if x == x else None)
    #container_df['FRP_PORTS'] = container_df['FRP_PORTS'].apply(lambda x: yaml.dump_to_string(clear_comments(x)) if x == x else '').astype(str)
    #container_df['EXTRA_ENVS'] = container_df['EXTRA_ENVS'].apply(lambda x: yaml.dump_to_string(clear_comments(x)) if x == x else '').astype(str)
    container_df['EXTRA_ENVS'] = container_df['EXTRA_ENVS'].apply(lambda x: x if x == x else None)

    state['container_df'] = container_df

def save_containers(state, fd):
    edited_container_df = state['container_df']
    container_data = state['_container_data_raw']

    old_data = container_data['deployment_containers']
    container_data['deployment_containers'] = CommentedSeq([CommentedMap({ k: v for k,v in c.items() if v == v and v != None and v != '' }) for c in edited_container_df.to_dict('records')])


    # keep starting comment
    container_data['deployment_containers'].ca.comment = old_data.ca.comment
    
    for i, x in enumerate(container_data['deployment_containers']):
        
        if 'INSTALL_PACKAGES' in x:
            x['INSTALL_PACKAGES'] = DoubleQuotedScalarString(' '.join(x['INSTALL_PACKAGES']))
        # set format for yaml objects
        if 'FRP_PORTS' in x:
            x['FRP_PORTS'] = CommentedMap(x['FRP_PORTS'])
            x['FRP_PORTS'].fa.set_block_style()
            if 'TCP' in x['FRP_PORTS']:
                x['FRP_PORTS']['TCP'] = CommentedSeq(x['FRP_PORTS']['TCP'])
                x['FRP_PORTS']['TCP'].fa.set_flow_style()
            if 'HTTP' in x['FRP_PORTS']:
                x['FRP_PORTS']['HTTP'] = CommentedSeq(x['FRP_PORTS']['HTTP'])
                x['FRP_PORTS']['HTTP'].fa.set_block_style()
                for j in range(len(x['FRP_PORTS']['HTTP'])):
                    port = CommentedMap(x['FRP_PORTS']['HTTP'][j])
                    if 'user' in port and port['user'] == None:
                        del port['user']
                    if 'subdomain_hostname_prefix' in port and port['subdomain_hostname_prefix'] == True:
                        del port['subdomain_hostname_prefix']
                    if 'https_without_pass' in port and port['https_without_pass'] == False:
                        del port['https_without_pass']
                    port.fa.set_flow_style()
                    for k, v in port.items():
                        if type(v) == str:
                            port[k] = DoubleQuotedScalarString(v)
                    x['FRP_PORTS']['HTTP'][j] = port
                    
                    
            
        if 'EXTRA_ENVS' in x:
            x['EXTRA_ENVS'] = CommentedMap(x['EXTRA_ENVS'])
            x['EXTRA_ENVS'].fa.set_block_style()

        # find old comments and attach them to new data
        el = [y for y in old_data if x['STACK_NAME'] == y['STACK_NAME']]
        if el:
            copy_comments(el[0], x)

        # Skip newline in front if we're first element
        if i == 0:
            continue    

        # Skip newline in front if previous element has a comment (which will add a newline)
        last = container_data['deployment_containers'][i-1]
        lastkey = list(last.keys())[-1]
        if any([x != None and x[2] is not None for x in last[lastkey].ca.items.values()]):
            continue
        if isinstance(last[lastkey], CommentedMap):
            last = last[lastkey]
            lastkey = list(last.keys())[-1]
            if hasattr(last[lastkey], 'ca') and last[lastkey].ca.end:
                continue

        container_data['deployment_containers'].ca.set(i, 1, [CommentToken('\n', column=0, start_mark=CommentMark(0))])
    
    yaml.dump(container_data, fd)

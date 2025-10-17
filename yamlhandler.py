import ruamel.yaml
from ruamel.yaml.comments import (CommentedSeq, CommentedMap, Comment,
                                  C_KEY_PRE, C_KEY_EOL, C_KEY_POST,
                                  C_VALUE_PRE, C_VALUE_EOL, C_VALUE_POST)
from ruamel.yaml.tokens import CommentToken
from ruamel.yaml.error import CommentMark
from ruamel.yaml.scalarstring import DoubleQuotedScalarString
import pandas as pd
from collections import Counter

import container

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

# do not change formatting!!!
researcher_header = '  ##############################\n  ## ViCoS Researchers #########\n  ##############################\n'
student_phd_header = '  ##############################\n  ## ViCoS Students ############\n  ##############################\n\n  # PhD students\n'
student_header = '  # Other\n'
lkm_header = '\n  ##############################\n  ## LKM Researchers/students ##\n  ##############################\n\n'
def load_users(state, fd):

    # read full file and manually section off groups
    full = fd.read()
    header, rest = full.split(researcher_header)
    researchers, rest = rest.split(student_phd_header)
    stud_phd, rest = rest.split(student_header)
    stud, lkm = rest.split(lkm_header)
    
    state['_user_header_raw'] = header
    prefix = 'data:\n' # since header got split off we add a placeholder to each group individually
    items = [('Researcher', researchers),('PhD', stud_phd),('Student', stud),('LKM', lkm)]
    state['_user_data_raw'] = { k: yaml.load(prefix + v) for k, v in items }
    
    state['user_df'] = {}
    state['roles'] = [*ruamel.yaml.YAML().load(full)['deployment_types'].keys()]
    mentors = []
    order = ['USER_FULLNAME','USER_EMAIL','USER_MENTOR','USER_NAME','USER_PUBKEY','USER_PUBKEY_FROM_GITHUB','USER_TYPE', 'ADDITIONAL_DEVICE_GROUPS', 'ADDITIONAL_PRIVATE_DATA_MOUNT_GROUPS', 'ADMIN_USER_ACCESS', 'DISABLED', 'PURGE_USER_DATA']
    for group, v in state['_user_data_raw'].items():    

        df = pd.DataFrame(v['data']).transpose()

        # Make sure we don't lose any values when reordering
        for k in df.columns:
            if k not in order:
                raise ValueError(f'{k} present in DataFrame but not in reordering')
        # Make sure dataframe has all necessary columns
        for k in order:
            if k not in df.columns:
                df[k] = None
        
        df = df[order]
        df['USER_TYPE'] = df['USER_TYPE'].astype('category').cat.set_categories(state['roles'])
        mentors += list(df['USER_MENTOR'].dropna())
        df['ADDITIONAL_PRIVATE_DATA_MOUNT_GROUPS'] = df['ADDITIONAL_PRIVATE_DATA_MOUNT_GROUPS'].apply(lambda x: [] if x != x or x is None else list(x))

        state['user_df'][group] = df
    
    state['mentors'] = [k for k,_ in Counter(mentors).most_common()]

def save_users(state, fd):
    
    segments = {}
    for group, user_data in state['_user_data_raw'].items():
        
        edited_user_df = state['user_df'][group]
        old_data = user_data['data']
        user_data['data'] = CommentedMap({ id: CommentedMap({ k: v for k,v in user.items() if v == v and v != None and v != [] }) for id, user in edited_user_df.transpose().to_dict().items()})

        # keep starting comment
        user_data['data'].ca.comment = old_data.ca.comment

        user_data_keys = list(user_data['data'])
        for i, (key, x) in enumerate(user_data['data'].items()):
            
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
            last = user_data['data'][user_data_keys[i-1]]
            lastkey = list(last)[-1]
            if lastkey != 'ADDITIONAL_PRIVATE_DATA_MOUNT_GROUPS' or last[lastkey].ca.end:
                continue

            user_data['data'].ca.set(key, 1, [CommentToken('\n', column=0, start_mark=CommentMark(0))])

        strdump = yaml.dump_to_string(user_data)
        segments[group] = strdump[strdump.index('\n')+1:] + '\n' # skip placeholder line and add trailing newline (the parser seems to skip it)
    
    fd.write(''.join([
        state['_user_header_raw'],
        researcher_header,
        segments['Researcher'],
        '\n' if segments['Researcher'][-2:] != '\n\n' else '',
        student_phd_header,
        segments['PhD'],
        '\n' if segments['PhD'][-2:] != '\n\n' else '',
        student_header,
        segments['Student'],
        lkm_header,
        segments['LKM']
    ]))

def load_containers(state, fd):

    # read full file and manually section off groups
    full = fd.read()
    header, rest = full.split(researcher_header)
    researchers, rest = rest.split(student_phd_header)
    stud_phd, rest = rest.split(student_header)
    stud, lkm = rest.split(lkm_header)
    
    state['_container_header_raw'] = header
    prefix = 'deployment_containers:\n' # since header got split off we add a placeholder to each group individually
    items = [('Researcher', researchers),('PhD', stud_phd),('Student', stud),('LKM', lkm)]
    state['_container_data_raw'] = { k: yaml.load(prefix + v.lstrip('\n')) for k, v in items }

    state['container_df'] = {}
    images = container.get_available_images()
    packages = []
    order = ['STACK_NAME','STORAGE_NAME','USER_EMAIL','CONTAINER_IMAGE','DEPLOYMENT_NODES','ALLOWED_NODES','INSTALL_PACKAGES', 'RUN_PRIVILEGED','ENABLE_DOCKER_ACCESS','SHM_SIZE', 'DISABLED','FRP_PORTS','EXTRA_ENVS']
    for group, v in state['_container_data_raw'].items():
        
        df = pd.DataFrame(v['deployment_containers'])

        # Make sure we don't lose any values when reordering
        for k in df.columns:
            if k not in order:
                raise ValueError(f'{k} present in DataFrame but not in reordering')
        # Make sure dataframe has all necessary columns
        for k in order:
            if k not in df.columns:
                df[k] = None

        df = df[order]

        df['CONTAINER_IMAGE'] = df['CONTAINER_IMAGE'].astype('category')
        images += [x for x in df['CONTAINER_IMAGE'].cat.categories if x not in images]

        df['INSTALL_PACKAGES'] = df['INSTALL_PACKAGES'].apply(lambda x: x.split(' '))
        df['INSTALL_PACKAGES'].transform(packages.extend)

        df['STORAGE_NAME'] = df['STORAGE_NAME'].apply(lambda x: x if x == x else None)
        #df['FRP_PORTS'] = df['FRP_PORTS'].apply(lambda x: yaml.dump_to_string(clear_comments(x)) if x == x else '').astype(str)
        #df['EXTRA_ENVS'] = df['EXTRA_ENVS'].apply(lambda x: yaml.dump_to_string(clear_comments(x)) if x == x else '').astype(str)
        df['EXTRA_ENVS'] = df['EXTRA_ENVS'].apply(lambda x: x if x == x else None)

        state['container_df'][group] = df
    
    state['packages'] = sorted(set(packages))
    for df in state['container_df'].values():
        df['CONTAINER_IMAGE'] = df['CONTAINER_IMAGE'].cat.set_categories(images)

def save_containers(state, fd):
    
    segments = {}
    for group, container_data in state['_container_data_raw'].items():
    
        edited_container_df = state['container_df'][group]

        old_data = container_data['deployment_containers']
        container_data['deployment_containers'] = CommentedSeq([CommentedMap({ k: v for k,v in c.items() if v == v and v != None and v != '' }) for c in edited_container_df.to_dict('records')])
        
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
        
        strdump = yaml.dump_to_string(container_data)
        segments[group] = strdump[strdump.index('\n')+1:] + '\n' # skip placeholder line and add trailing newline (the parser seems to skip it)
        #segments[group] = strdump + '\n'
    
    fd.write(''.join([
        state['_container_header_raw'],
        researcher_header,
        segments['Researcher'],
        '\n' if segments['Researcher'][-2:] != '\n\n' else '',
        student_phd_header,
        segments['PhD'],
        '\n' if segments['PhD'][-2:] != '\n\n' else '',
        student_header,
        segments['Student'],
        lkm_header,
        segments['LKM']
    ]))

def load_nodes(state, fd):

    data = yaml.load(fd.read())
    state['nodes'] = [*data['all']['children']['ccc-cluster']['hosts'].keys()]

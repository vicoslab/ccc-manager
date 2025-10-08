import requests
import json
import os
import streamlit as st
from datetime import datetime

def get_available_images(cacheFile='./docker-image.cache.txt'):
    # We cache response for 1 week
    if os.path.exists(cacheFile) and (datetime.now() - datetime.fromtimestamp(os.stat(cacheFile).st_mtime)).days < 7:
        # keep it in state so we don't read file constantly
        if '_cat_images' not in st.session_state:
            with open(cacheFile) as f:
                st.session_state['_cat_images'] = f.readlines()
        return st.session_state['_cat_images']

    url = 'https://hub.docker.com/v2/repositories/vicoslab/ccc/tags?page_size=1000'
    resp = json.loads(requests.get(url).text)
    results = resp['results']

    while resp['next'] != None:
        resp = json.loads(requests.get(resp['next']).text)
        results += resp['results']

    results.sort(key=lambda x: x['name'], reverse=True)
    results.sort(key=lambda x: x['name'].split('-')[0])

    tags = map(lambda x: 'vicoslab/ccc:' + x['name'], results)
    tags = list(filter(lambda x: '-latest-' not in x, tags))

    with open(cacheFile, 'w') as f:
        f.write('\n'.join(tags))
    
    return tags

if __name__ == '__main__':
    get_available_images()
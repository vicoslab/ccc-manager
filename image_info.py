import requests
import json
import os
from datetime import datetime

def get_available_images(state, cacheFile='./docker-image.cache.txt'):
    # Cron should run this every week, but we leave some wiggle room
    if os.path.exists(cacheFile) and (datetime.now() - datetime.fromtimestamp(os.stat(cacheFile).st_mtime)).days < 6:
        # keep it in state so we don't read file constantly
        if '_cat_images' not in state:
            with open(cacheFile) as f:
                state['_cat_images'] = f.readlines()
        return state['_cat_images']

    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'Fetching docker images for ccc')
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
    import sys
    get_available_images({}, sys.argv[1])
#!/usr/bin/env python3
"""Compare upstream revision and compiler recipe before downloading the statewide PBF."""
import hashlib,json,os,urllib.request,urllib.error
from pathlib import Path
from prepare_map_channel import SOURCE

def main():
    repo=os.environ.get('MAP_PUBLIC_REPOSITORY') or 'lucasnoronha88/RadarWaze-Maps'
    import re
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repo):raise ValueError('Invalid publisher repository')
    with urllib.request.urlopen(urllib.request.Request(SOURCE,method='HEAD'),timeout=60) as r:
        revision='|'.join([r.headers.get('ETag',''),r.headers.get('Last-Modified',''),r.headers.get('Content-Length','')])
    if revision=='||':raise ValueError('Upstream has no stable revision metadata')
    revision+='|recipe:'+hashlib.sha256(Path('tools/build_road_graph_v2.py').read_bytes()).hexdigest()
    previous={}
    try:
        with urllib.request.urlopen(f'https://github.com/{repo}/releases/download/sp-roadmap/latest.json',timeout=30) as r:
            previous=json.loads(r.read(65537))
    except urllib.error.HTTPError as e:
        if e.code!=404:raise
    changed=previous.get('source_revision')!=revision
    Path('source-revision.txt').write_text(revision)
    with open(os.environ['GITHUB_OUTPUT'],'a') as out:
        out.write(f'changed={str(changed).lower()}\nrepository={repo}\n')
    print('Source changed; preparing map' if changed else 'Source unchanged; no statewide download or conversion')

if __name__=='__main__':main()

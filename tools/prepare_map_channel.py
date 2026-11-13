#!/usr/bin/env python3
"""Publish metadata only after verifying the Android-compatible package and its hashes."""
import argparse,hashlib,json,re,zipfile
from pathlib import Path
from urllib.parse import urlparse

SOURCE='https://download.openstreetmap.fr/extracts/south-america/brazil/southeast/sao-paulo-latest.osm.pbf'

def prepare(package,url,revision,output):
    parsed=urlparse(url)
    if parsed.scheme!='https' or parsed.username or parsed.password: raise ValueError('HTTPS package URL required')
    package=Path(package)
    with zipfile.ZipFile(package) as z:
        if sorted(z.namelist())!=['edges.csv','manifest.json','restrictions.csv']:raise ValueError('Unexpected package files')
        m=json.loads(z.read('manifest.json'))
        assert m['format']=='radarwaze-road-graph-v2' and m['region']=='SP' and m['scope']=='full-sp'
        assert m['edges']>100000 and m['routing_safe'] is False
        for name,key in [('edges.csv','sha256'),('restrictions.csv','restrictions_sha256')]:
            digest=hashlib.sha256();count=0
            with z.open(name) as data:
                for line in data:
                    digest.update(line)
                    if line.strip() and not line.startswith(b'#'):count+=1
            assert digest.hexdigest()==m[key], 'Package integrity failure'
            assert count==m['edges' if name=='edges.csv' else 'restrictions'], 'Record count mismatch' 
    with package.open('rb') as data: sha=hashlib.file_digest(data,'sha256').hexdigest()
    result={'format':'radarwaze-map-channel-v1','package_format':m['format'],'region':'SP',
        'version':m['version'],'min_app_version_code':37,'url':url,'sha256':sha,
        'edges_sha256':m['sha256'],'restrictions_sha256':m['restrictions_sha256'],
        'bytes':package.stat().st_size,'source_url':SOURCE,'source_revision':revision,
        'attribution':'© OpenStreetMap contributors; Open Database License (ODbL) 1.0',
        'license_url':'https://www.openstreetmap.org/copyright'}
    Path(output).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('package');p.add_argument('--url',required=True);p.add_argument('--source-revision',required=True);p.add_argument('--output',default='latest.json');a=p.parse_args()
    prepare(a.package,a.url,a.source_revision,a.output)

#!/usr/bin/env python3
import hashlib,json,tempfile,zipfile
from pathlib import Path
from prepare_map_channel import prepare

def main():
    with tempfile.TemporaryDirectory() as temp:
        p=Path(temp);package=p/'map.zip'
        edges=b'1,2,-23,-46,-23,-45.999,1,100,0\n'*100001
        turns=b'# turns\n'
        m={'format':'radarwaze-road-graph-v2','region':'SP','scope':'full-sp','edges':100001,'restrictions':0,
            'routing_safe':False,'version':'fixture-1','sha256':hashlib.sha256(edges).hexdigest(),
            'restrictions_sha256':hashlib.sha256(turns).hexdigest()}
        def write():
            with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED) as z:
                z.writestr('edges.csv',edges);z.writestr('restrictions.csv',turns);z.writestr('manifest.json',json.dumps(m))
        write();r=prepare(package,'https://maps.example.org/map.zip','revision',p/'latest.json')
        assert r['bytes']==package.stat().st_size and r['version']=='fixture-1'
        assert r['edges_sha256']==m['sha256'] and r['source_revision']=='revision'
        try:prepare(package,'http://maps.example.org/map.zip','revision',p/'latest.json');raise RuntimeError('HTTP accepted')
        except ValueError:pass
        m['edges']=100002;write()
        try:prepare(package,'https://maps.example.org/map.zip','revision',p/'latest.json');raise RuntimeError('Bad count accepted')
        except AssertionError:pass
        m['edges']=100001;m['sha256']='0'*64;write()
        try:prepare(package,'https://maps.example.org/map.zip','revision',p/'latest.json');raise RuntimeError('Bad hash accepted')
        except AssertionError:pass
    print('PASS: prepared channel integrity, counts, HTTPS and version metadata')
if __name__=='__main__':main()

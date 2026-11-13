#!/usr/bin/env python3
"""Build experimental OSM node-aware road graph v2 (not turn-restriction safe)."""
import argparse
import hashlib
import json
import math
import tempfile
import zipfile
from pathlib import Path

import osmium

DRIVABLE = {'motorway','trunk','primary','secondary','tertiary','unclassified','residential','living_street','service','motorway_link','trunk_link','primary_link','secondary_link','tertiary_link','road'}

class Extract(osmium.SimpleHandler):
    def __init__(self, output):
        super().__init__()
        self.output=output
        self.count=0
        self.restrictions=[]
        self.unsupported_restrictions=0
    def relation(self, relation):
        tags={t.k:t.v for t in relation.tags}
        if tags.get("type")!="restriction":
            return
        if 'motorcar' in tags.get('except','').split(';') or 'motor_vehicle' in tags.get('except','').split(';'):
            return
        if any('conditional' in key for key in tags):
            self.unsupported_restrictions+=1
            return
        restriction=tags.get("restriction:motorcar",tags.get("restriction:motor_vehicle",tags.get("restriction","")))
        if not restriction.startswith(("no_","only_")):
            return
        members={}
        for member in relation.members:
            if member.role in ("from","to","via"):
                members.setdefault(member.role,[]).append((member.type,member.ref))
        if len(members.get("from",[]))!=1 or len(members.get("to",[]))!=1 or len(members.get("via",[]))!=1:
            return
        source=members["from"][0]; target=members["to"][0]; via=members["via"][0]
        if source[0]!="w" or target[0]!="w" or via[0]!="n":
            self.unsupported_restrictions+=1
            return
        self.restrictions.append((source[1],via[1],target[1],restriction))
    def way(self, way):
        tags={t.k:t.v for t in way.tags}
        if tags.get('highway') not in DRIVABLE:
            return
        if any(tags.get(k) in ('no','private') for k in ('access','vehicle','motor_vehicle','motorcar')):
            return
        oneway=tags.get('oneway')
        direction=0 if oneway in ('no','false','0') else (-1 if oneway=='-1' else (1 if oneway in ('yes','true','1') or tags.get('junction')=='roundabout' or tags.get('highway') in ('motorway','motorway_link') else 0))
        layer=tags.get('layer','0')
        if not layer.lstrip('-').isdigit():
            layer='0'
        nodes=list(way.nodes)
        for a,b in zip(nodes,nodes[1:]):
            if a.ref==b.ref or not a.location.valid() or not b.location.valid():
                continue
            dy=(b.location.lat-a.location.lat)*111320.0
            dx=(b.location.lon-a.location.lon)*111320.0*math.cos(math.radians((a.location.lat+b.location.lat)/2))
            if not 0<math.hypot(dx,dy)<=20000:
                continue
            self.output.write(f'{a.ref},{b.ref},{a.location.lat:.7f},{a.location.lon:.7f},{b.location.lat:.7f},{b.location.lon:.7f},{direction},{way.id},{layer}\n')
            self.count+=1

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('input')
    parser.add_argument('--output',default='sp-road-graph-v2.zip')
    parser.add_argument('--scope',choices=('sample-only','full-sp'),default='sample-only')
    args=parser.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/'edges.csv'
        with path.open('w',encoding='utf-8',newline='') as output:
            output.write('# radarwaze-road-graph-v2:node_a,node_b,lat_a,lon_a,lat_b,lon_b,oneway,way_id,layer\n')
            extractor=Extract(output)
            extractor.apply_file(args.input,locations=True)
        restrictions_path=Path(tmp)/'restrictions.csv'
        with restrictions_path.open('w',encoding='utf-8',newline='') as output:
            output.write('# from_way,via_node,to_way,restriction\n')
            for source,via,target,restriction in extractor.restrictions:
                output.write(f'{source},{via},{target},{restriction}\n')
        if extractor.count<=1000:
            raise RuntimeError('Too few road segments')
        with path.open('rb') as source:
            sha=hashlib.file_digest(source,'sha256').hexdigest()
        with restrictions_path.open('rb') as source:
            restrictions_sha=hashlib.file_digest(source,'sha256').hexdigest()
        manifest={'version':sha[:16]+restrictions_sha[:16],'unsupported_restrictions':extractor.unsupported_restrictions,'restrictions':len(extractor.restrictions),'restrictions_sha256':restrictions_sha,'format':'radarwaze-road-graph-v2','region':'SP','scope':args.scope,'edges':extractor.count,'sha256':sha,'routing_safe':False,'limitations':['via_way_and_conditional_restrictions_not_supported','road_level_and_gps_not_field_validated']}
        with zipfile.ZipFile(args.output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=7,allowZip64=True) as archive:
            archive.write(path,'edges.csv')
            archive.write(restrictions_path,'restrictions.csv')
            archive.writestr('manifest.json',json.dumps(manifest))
        print(f'PASS: {extractor.count} directed-capable edges with original OSM node IDs; routing_safe=false')

if __name__=='__main__':
    main()


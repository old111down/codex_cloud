#!/usr/bin/env python3
"""Create exact artificial fixtures used by the logged CPU smoke tests."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
R=ROOT/'papers/et_bert/runtime-artifacts'
R.mkdir(parents=True,exist_ok=True)
contents={}
for name,n in [('train',8),('dev',4),('test',4)]:
    contents[name+'.tsv']='label\ttext_a\n'+''.join(
        str(i%2)+'\t'+('abcd 1234 ef01 abcd 1234' if i%2 else '0000 0001 0002 0000 0001')+'\n'
        for i in range(n))
contents['unlabeled.tsv']='text_a\nabcd 1234 ef01\n0000 0001 0002\n'
contents['synthetic_burst_corpus.txt']=('abcd 1234 ef01 2345 3456 4567\n0000 0001 0002 0003 0004 0005\n\n')*24
rows=[]
for name,value in contents.items():
    p=R/name
    if p.exists():
        assert p.read_text()==value, f'Refusing to overwrite changed fixture: {p}'
    else:
        p.write_text(value)
    rows.append({'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
out={'scope':'Deterministic artificial hex-token fixtures only; no real traffic, no paper dataset or label meaning','files':rows}
(ROOT/'evidence/et_bert/synthetic_input_manifest.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))

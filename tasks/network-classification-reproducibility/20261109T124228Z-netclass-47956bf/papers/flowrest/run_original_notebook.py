#!/usr/bin/env python3
"""Execute original notebook cells in order, stopping at first original exception."""
import hashlib,json,sys,time,os
from pathlib import Path
root=Path(__file__).resolve().parents[2]
which=sys.argv[1]
if hasattr(os,'sched_getaffinity'):
 os.sched_setaffinity(0,set(sorted(os.sched_getaffinity(0))[:2]));print('cpu_affinity',sorted(os.sched_getaffinity(0)),flush=True)
p=root/'upstream/flowrest/Python'/('Conference_version/unsw_iot_per_flow_16_classes.ipynb' if which=='conference' else 'Full_version/Unibs_flowrest_analysis.ipynb')
x=json.loads(p.read_text()); ns={'__name__':'__audit_notebook__'}
print(json.dumps({'notebook':str(p.relative_to(root)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'scope':'Sequential original cells until first exception; not a completed notebook run'}),flush=True)
for i,c in enumerate(x['cells']):
 if c['cell_type']!='code':continue
 print('Executing original cell',i,flush=True)
 exec(compile(''.join(c['source']),str(p)+'#cell'+str(i),'exec'),ns)

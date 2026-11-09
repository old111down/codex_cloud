"""Retrieve legal author copy and inspect public weight serialization without unpickling."""
import datetime
import hashlib
import json
from pathlib import Path
import pickletools
import urllib.request
import zipfile

ROOT=Path(__file__).resolve().parents[2]
E=ROOT/'evidence/pegasus'
E.mkdir(exist_ok=True)
log=[]
requests=[
 ('paper_final.pdf','https://madsys.cs.tsinghua.edu.cn/publication/pegasus-a-universal-framework-for-scalable-deep-learning-inference-on-the-dataplane/SIGCOMM2025-zhang.pdf','GET'),
 ('google_drive_peerrush_headers.json','https://drive.google.com/uc?export=download&id=1JY_UcLr_ZrIfzYLEmCVPn3LMza_b_bhH','HEAD'),
 ('acm_final_headers.json','https://dl.acm.org/doi/pdf/10.1145/3718958.3750529','HEAD')]
for rel,url,method in requests:
    r={'url':url,'method':method,'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    try:
        req=urllib.request.Request(url,method=method,headers={'User-Agent':'reproduction-audit'})
        with urllib.request.urlopen(req,timeout=40) as q:
            r.update(status=q.status,final_url=q.url,
                     headers={k:q.headers.get(k) for k in ('content-type','content-length','content-disposition')})
            data=q.read() if method=='GET' else json.dumps(r,indent=2).encode()
        (E/rel).write_bytes(data)
        r.update(path=rel,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    except Exception as e:
        r['error']=str(e)
    log.append(r)
(E/'retrieval_log.json').write_text(json.dumps(log,indent=2)+'\n')
p=ROOT/'upstream/pegasus/software/save/mlp/PeerRush/MLP_PeerRush.pt'
with zipfile.ZipFile(p) as z:
    name=next(n for n in z.namelist() if n.endswith('data.pkl'))
    raw=z.read(name)
    ops=[{'opcode':op.name,'argument':arg,'offset':pos} for op,arg,pos in pickletools.genops(raw)
         if op.name in ('GLOBAL','STACK_GLOBAL','REDUCE','NEWOBJ','NEWOBJ_EX')]
out={'source':'https://github.com/afireswallow/Pegasus',
     'commit_sha':'a73bd327fbf0db2550a9bc1e304b96e0aa550cba',
     'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,
     'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'pickle_global_operations':ops,
     'scope':'Static pickle opcode review only; no unpickle in retrieval harness; not a formal safety proof'}
(E/'mlp_weights_static_review.json').write_text(json.dumps(out,indent=2)+'\n')
print('Weight GLOBAL operations:',[r for r in ops if r['opcode']=='GLOBAL'])
print(json.dumps(log,indent=2))

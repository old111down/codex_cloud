#!/usr/bin/env python3
"""Collect public, read-only source snapshots for network candidates (no credentials)."""
import urllib.request, json, pathlib, hashlib, datetime, concurrent.futures, subprocess
BASE=pathlib.Path(__file__).resolve().parents[1]
REPOS={'leo':'Purdue-ISL/Leo','brain_on_switch':'InspiringGroup-Lab/Brain-on-Switch','linc':'haolinyan/LINC','iisy':'In-Network-Machine-Learning/IIsy'}
SOURCES={
'leo': {'paper.pdf':'https://www.usenix.org/system/files/nsdi24-jafri.pdf','paper_page.html':'https://www.usenix.org/conference/nsdi24/presentation/jafri'},
'brain_on_switch': {'paper.pdf':'https://www.usenix.org/system/files/nsdi24-yan.pdf','paper_page.html':'https://www.usenix.org/conference/nsdi24/presentation/yan'},
'linc': {'conference.html':'https://icnp24.cs.ucr.edu/acceptedpapers.html','paper.pdf':'https://ieeexplore.ieee.org/iel8/10858485/10858498/10858585.pdf','paper_author.pdf':'https://smartinternet.group/wp-content/uploads/2024/09/paper-yhl-linc-icnp.pdf','crossref.json':'https://api.crossref.org/works/10.1109%2FICNP61940.2024.10858585'},
'iisy': {'paper_page.html':'https://ora.ox.ac.uk/objects/uuid:ce439a67-a6ff-44f3-ab20-c6e355a90aff','paper.pdf':'https://ora.ox.ac.uk/objects/uuid:ce439a67-a6ff-44f3-ab20-c6e355a90aff/files/s7s75df26h','crossref.json':'https://api.crossref.org/works/10.1109%2FTNET.2024.3364757'}}
EXTRA={'brain_on_switch':['dataset/README.md','model/README.md','IMIS/system/README.md','p4/README.md','IMIS/YaTC/README.md'],'linc':['requirements.txt','train_nn.py'],'iisy':['Data/readme.md','main.py','src/Iris_dataset.py']}
log=[]
def fetch(id,name,url):
 d=BASE/'evidence'/'candidates'/id;d.mkdir(parents=True,exist_ok=True)
 rec={'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'url':url,'file':str((d/name).relative_to(BASE))}
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'traffic-repro-audit-public-research/1.0'})
  with urllib.request.urlopen(req,timeout=40) as r: data=r.read();rec.update(status=r.status,final_url=r.url)
  (d/name).write_bytes(data);rec.update(size_bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
 except Exception as e: rec['error']=str(e)
 log.append(rec);return rec

def repo(id,repo):
 rec=fetch(id,'repository_api.json','https://api.github.com/repos/'+repo)
 if rec.get('status')!=200:return
 meta=json.loads((BASE/rec['file']).read_text());branch=meta['default_branch']
 commit_rec=fetch(id,'commit_api.json',f'https://api.github.com/repos/{repo}/commits/{branch}')
 if commit_rec.get('status')!=200:return
 sha=json.loads((BASE/commit_rec['file']).read_text())['sha']
 fetch(id,'tree_api.json',f'https://api.github.com/repos/{repo}/git/trees/{branch}?recursive=1')
 for name,url in SOURCES[id].items():fetch(id,name,url)
 for path in EXTRA.get(id,[]): fetch(id,path.replace('/','__'),'https://raw.githubusercontent.com/'+meta['full_name']+'/'+sha+'/'+path)
 if meta.get('license'): fetch(id,'LICENSE','https://raw.githubusercontent.com/'+meta['full_name']+'/'+sha+'/LICENSE')
 for name in ['README.md','README','README.MD']:
  rec=fetch(id,'README.md','https://raw.githubusercontent.com/'+meta['full_name']+'/'+sha+'/'+name)
  if rec.get('status')==200:break
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(lambda p:repo(*p),REPOS.items()))
for id in REPOS:
 d=BASE/'evidence'/'candidates'/id
 pdf=d/('paper_author.pdf' if id=='linc' else 'paper.pdf')
 if pdf.exists() and pdf.read_bytes().startswith(b'%PDF'):
  subprocess.run(['pdftotext','-layout',str(pdf),str(d/'paper.txt')],check=True)
(BASE/'evidence'/'candidates'/'network_fetch_log.json').write_text(json.dumps(log,indent=2)+'\n')
for r in log: print(r.get('status','ERR'),r['file'],r.get('error',''))

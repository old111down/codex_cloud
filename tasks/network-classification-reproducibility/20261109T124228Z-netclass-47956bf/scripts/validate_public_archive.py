#!/usr/bin/env python3
"""Validate the public snapshot only; do not download or run source models."""
import argparse,hashlib,json,re,datetime as dt
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--write-manifest',action='store_true');a=p.parse_args()
manifest=ROOT/'reports/public_checksums.json'
forbidden={'.pdf','.html','.pcap','.pcapng','.pth','.pt','.pkl','.pickle','.onnx','.zip','.bin','.so','.pyc'}
errors=[];files=[]
for f in sorted(ROOT.rglob('*')):
 if f.is_symlink():
  errors.append('Symlink not permitted: '+str(f.relative_to(ROOT)));continue
 if not f.is_file():continue
 rel=str(f.relative_to(ROOT))
 if f.suffix.lower() in forbidden or '.git' in f.parts or '__pycache__' in f.parts:errors.append('Forbidden artifact: '+rel)
 if f.stat().st_size>2_000_000:errors.append('Oversized artifact: '+rel)
 if f==manifest:continue
 try:text=f.read_text()
 except UnicodeError:errors.append('Non-text artifact: '+rel);continue
 for pattern in (r'github_pat_[A-Za-z0-9_]{30,}',r'gh[pousr]_[A-Za-z0-9]{25,}',r'-----BEGIN (?:[A-Z ]+)?PRIVATE KEY-----',r'ccarenv_b64_[A-Za-z0-9_-]+',r'cecfg(?:ver)?_[A-Za-z0-9]+'):
  if re.search(pattern,text):errors.append('Potential secret/infrastructure identifier: '+rel)
 files.append({'path':rel,'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
for name in ('metadata.json','README.md','task_report.md','execution_log.md','papers.csv','coverage_matrix.csv','reproduction_results.csv'):
 if not (ROOT/name).exists():errors.append('Missing '+name)
try:
 import jsonschema
 schema=ROOT.parents[2]/'templates/metadata.schema.json'
 jsonschema.validate(json.loads((ROOT/'metadata.json').read_text()),json.loads(schema.read_text()),format_checker=jsonschema.FormatChecker())
 data=json.loads((ROOT/'metadata.json').read_text())
 for key in ('start_time_utc','end_time_utc','archive_started_time_utc','archive_completed_time_utc','original_deadline_utc','export_created_utc','research_completed_time_utc'):
  value=data.get(key)
  if value in (None,'Unknown'):continue
  parsed=dt.datetime.fromisoformat(value.replace('Z','+00:00'))
  if parsed.tzinfo is None or parsed.utcoffset()!=dt.timedelta(0):errors.append('Non-UTC task timestamp '+key)
except ImportError:errors.append('jsonschema unavailable; metadata schema not verified')
except Exception as e:errors.append('Metadata schema: '+str(e))
if a.write_manifest and not errors:manifest.write_text(json.dumps({'scope':'Published text subset only; excluded local evidence is in archive_manifest.csv','files':files},indent=2)+'\n')
if manifest.exists():
 for row in json.loads(manifest.read_text())['files']:
  f=ROOT/row['path']
  if not f.exists() or hashlib.sha256(f.read_bytes()).hexdigest()!=row['sha256']:errors.append('Checksum mismatch '+row['path'])
else:errors.append('Missing public checksum manifest (use --write-manifest after review)')
print(json.dumps({'public_files':len(files),'errors':errors},indent=2));raise SystemExit(bool(errors))

#!/usr/bin/env python3
"""Produce a public, record-free source/size/hash manifest after real validation."""
import csv
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def main():
    stats=json.loads((ROOT/'reports/aggregate_stats.json').read_text())
    info=json.loads((ROOT/'private/evidence/hf_repo.json').read_text())
    entries={e['rfilename']:e for e in info['siblings']};rev=info['sha'];rows=[]
    for w in stats['weeks']:
        week=w['week']
        for file,metadata in w['file_metadata'].items():
            rel=f'release/{week}/processed/{file}';e=entries[rel]
            observed=w['hashes'][file]
            assert observed==e['lfs']['sha256']
            rows.append({'week':week,'file':file,'source_url':f'https://huggingface.co/datasets/harvardMadsys/freeinference_agentic_trace/resolve/{rev}/{rel}',
                'dataset_revision':rev,'license':'CC-BY-4.0','bytes':e['size'],'sha256':observed,'rows':metadata['rows'],
                'status':'Verified: actual file bytes/hash plus release tables.json/manifest chain',
                'data_scope':'Public application trace; source data retained privately; no raw rows archived'})
    with (ROOT/'reports/data_manifest.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    summary={'dataset':'harvardMadsys/freeinference_agentic_trace','revision':rev,'license':'CC-BY-4.0','gated':info.get('gated'),
      'parquet_files':len(rows),'bytes':sum(r['bytes'] for r in rows),'weeks':len(stats['weeks']),
      'timestamp_scope':'2026-05-17 through 2026-09-05 completion weeks; derived starts may predate a week',
      'schema_consistent_across_selected_weeks':{file:len({w['file_metadata'][file]['schema'] for w in stats['weeks']})==1 for file in stats['weeks'][0]['file_metadata']},
      'all_actual_checksums_match':all(w['checks'][k] for w in stats['weeks'] for k in w['checks'] if 'sha256' in k),
      'raw_jsonl_downloaded':False,'raw_data_publication':False,'cache_duplicate':False}
    (ROOT/'reports/data_source_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))
if __name__=='__main__':main()

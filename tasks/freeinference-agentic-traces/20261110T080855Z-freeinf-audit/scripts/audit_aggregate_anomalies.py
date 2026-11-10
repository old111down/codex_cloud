#!/usr/bin/env python3
"""Inspect token-field observations and workload confounding without raw rows."""
import collections
import json
from pathlib import Path
import pandas as pd
import pyarrow.parquet as pq

ROOT=Path(__file__).resolve().parents[1]

def main():
    stats=json.loads((ROOT/'reports/aggregate_stats.json').read_text())
    anomalies=[]
    for w in stats['weeks']:
        if not w['observations_requiring_review']['cached_tokens_exceed_provider_prompt']:continue
        p=ROOT/'private/data/release'/w['week']/'requests.parquet'
        r=pq.read_table(p,columns=['model','provider','prompt_tokens','cache_read_tokens']).to_pandas()
        a=r[r.cache_read_tokens>r.prompt_tokens]
        grouped=a.groupby(['provider','model']).agg(rows=('model','size'),prompt_sum=('prompt_tokens','sum'),cached_sum=('cache_read_tokens','sum'))
        for (provider,model),g in grouped.iterrows():
            anomalies.append({'week':w['week'],'anonymous_provider':provider,'model_label':model,
                'rows':int(g['rows']),'prompt_sum':int(g['prompt_sum']),'cache_read_sum':int(g['cached_sum'])})
    models=stats['distributions']['request_model']; counts=stats['distributions']['top_level_session_harness']
    human={k:v for k,v in counts.items() if not k.startswith('eval:')}
    pairs=stats['confounding_crosstabs']['harness_by_model_requests']
    byh=collections.defaultdict(collections.Counter)
    for x in pairs:byh[x['left']][x['right']]+=x['count']
    dominance=[{'harness':h,'all_session_request_rows':sum(c.values()),'largest_model_label':c.most_common(1)[0][0],
                'largest_model_request_share':c.most_common(1)[0][1]/sum(c.values()),'distinct_model_labels':len(c)} for h,c in sorted(byh.items())]
    output={
      'status':'Verified aggregate observations; underlying provider semantics and causal confounding Unknown',
      'dataset_revision':stats['dataset_revision'],'source_commit':stats['source_commit'],
      'cached_exceeds_prompt_observations':anomalies,
      'cached_exceeds_prompt_interpretation':'Do not infer corruption: source fields may follow different provider token conventions, reporting/normalization may differ, true provider identities and raw responses are unavailable.',
      'historical_model_presence':{'exact_label':'mimo-v2.6-flash','rows':models.get('mimo-v2.6-flash',0),'any_mimo_casefold_substring_rows':sum(n for m,n in models.items() if 'mimo' in m.casefold()),'distinct_model_labels':len(models),'scope':'All released 16-week processed requests including children; says nothing conclusive about current supported routes.'},
      'human_top_level_harness_imbalance':{'sessions':sum(human.values()),'classes':len(human),'largest_class':max(human,key=human.get),'largest_class_sessions':max(human.values()),'largest_class_share':max(human.values())/sum(human.values()),'smallest_class':min(human,key=human.get),'smallest_class_sessions':min(human.values()),'max_min_count_ratio':max(human.values())/min(human.values())},
      'harness_model_dominance':dominance,
      'classification_limits':['These are co-occurrence diagnostics, not causal evidence or held-out classifier results.',
          'No task intent labels/text exist to quantify semantic task-distribution confounding.',
          'A random request split would mix reconstructed sessions, descendants and accounts; group split and new synchronized PCAP are needed.',
          'Absolute date, model, provider, tokens and public application labels are unavailable or shortcut-prone network-only classifier features.']}
    (ROOT/'reports/anomaly_and_confounding_aggregates.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(output,indent=2))
if __name__=='__main__':main()

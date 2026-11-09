"""Check original fixed-width arithmetic for a full-width feature input; no P4 execution."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
first=json.loads((ROOT/'evidence/leo/threshold_counterexample.json').read_text())
cases=[]
for item in first['cases']:
    c=item['parsed_constraint']
    x=65535
    p4_word=(x+((-c)&0xffff))&0xffff
    left=bool(p4_word&0x8000)
    cases.append({'feature_input':x,'reference_sklearn_left':x<=item['sklearn_threshold'],
                  'parsed_constraint':c,'neg_constraint_16bit':(-c)&0xffff,
                  'sum_16bit':p4_word,'generated_left':left,
                  'mismatch':left!=(x<=item['sklearn_threshold'])})
assert all(c['mismatch'] for c in cases)
out={'scope':'Python bit-vector evaluation of pinned generated P4 FEATURE_WIDTH16 add/MSB predicate; not actual P4 compilation/simulation or a statement about observed paper datasets',
     'original_generator_sha256':hashlib.sha256((ROOT/'upstream/leo/leo-generator/leo_ctrlplane.py').read_bytes()).hexdigest(),
     'p4_templates_sha256':hashlib.sha256((ROOT/'upstream/leo/leo-generator/leo_templates.py').read_bytes()).hexdigest(),
     'feature_domain':'Unsigned16-bit;65535 is representable by the generated header. Actual input frequency Unknown.',
     'cases':cases}
(ROOT/'evidence/leo/integer_domain_counterexamples.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))

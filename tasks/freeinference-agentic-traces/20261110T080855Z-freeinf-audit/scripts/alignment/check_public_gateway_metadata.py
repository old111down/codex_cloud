#!/usr/bin/env python3
"""Public, no-auth GET checks. Never invokes a model or saves response bodies."""
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from pathlib import Path
import json,time,uuid,datetime

def check(url, header_probe=False):
    synthetic_id=uuid.uuid4().hex
    headers={'User-Agent':'research-reproducibility-audit'}
    if header_probe: headers['X-Request-ID']=synthetic_id
    started=datetime.datetime.now(datetime.timezone.utc).isoformat(); t=time.monotonic()
    try:
        with urlopen(Request(url,headers=headers,method='GET'),timeout=20) as response:
            status=response.status
            matched=response.headers.get('x-request-id')==synthetic_id if header_probe else None
            # Read only the public model catalog; never read a user-log response.
            body=response.read(100000) if url.endswith('/v1/models') else b''
            catalog=json.loads(body).get('data',[]) if body else []
    except HTTPError as response:
        status=response.code
        matched=response.headers.get('x-request-id')==synthetic_id if header_probe else None
        catalog=[]
        response.close()
    except Exception as exc:
        return {'url':url,'start_utc':started,'status':'Unknown','error_type':type(exc).__name__,'elapsed_seconds':round(time.monotonic()-t,3)}
    result={'url':url,'start_utc':started,'status':status,'elapsed_seconds':round(time.monotonic()-t,3),'authentication_sent':False,'model_inference_invoked':False,'body_saved':False}
    if header_probe: result['synthetic_request_id_echo_matches']=matched
    if url.endswith('/v1/models'):
        ids=sorted(row.get('id','') for row in catalog)
        result['public_model_count']=len(ids)
        result['mimo_v2_6_flash_listed']='mimo-v2.6-flash' in ids
        result['public_model_ids']=ids
    return result

if __name__=='__main__':
    result={'scope':'No-auth public GET only; no inference; no credentials read or sent. User endpoint response body is not read.','checks':[check('https://freeinference.org/v1/models',True),check('https://freeinference.org/user/recent-requests?limit=1')]}
    out=Path('logs/alignment_public_http_checks.json'); out.write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result,indent=2))

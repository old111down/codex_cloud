#!/usr/bin/env python3
"""Random-initialized original base architecture forward; no paper data/weights."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import resource
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
UP=ROOT/'upstream/et_bert'
sys.path.insert(0,str(UP))
import torch
from uer.opts import finetune_opts
from uer.utils.config import load_hyperparam
from uer.utils.seed import set_seed
from uer.utils.tokenizers import BertTokenizer

spec=importlib.util.spec_from_file_location('etbert_classifier',UP/'fine-tuning/run_classifier.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
p=argparse.ArgumentParser()
finetune_opts(p)
args=p.parse_args(['--train_path','synthetic','--dev_path','synthetic',
                  '--config_path',str(UP/'models/bert/base_config.json'),
                  '--vocab_path',str(UP/'models/encryptd_vocab.txt'),
                  '--dropout','0.5'])
dropout_cli=args.dropout
args=load_hyperparam(args)
args.tokenizer=BertTokenizer(args)
args.labels_num=2
args.pooling='first'
args.soft_targets=False
args.soft_alpha=0.5
set_seed(7)
torch.set_num_threads(1)
model=module.Classifier(args).eval()
tokens=torch.tensor([[2]+[5,6,7,8,9]*3,[2]+[10,11,12,13,14]*3],dtype=torch.long)
segments=torch.ones_like(tokens)
start=time.perf_counter()
with torch.no_grad():
    loss,logits=model(tokens,torch.tensor([0,1]),segments)
elapsed=time.perf_counter()-start
assert logits.shape==(2,2)
assert torch.isfinite(logits).all() and torch.isfinite(loss)
out={'scope':'Synthetic CPU forward of unmodified Classifier with original base_config: no pretrained weights, no paper data, no accuracy reproduction',
     'architecture':{'layers':args.layers_num,'heads':args.heads_num,'hidden_size':args.hidden_size,
                     'embedding_size':args.emb_size,'feedforward_size':args.feedforward_size,
                     'vocab_size':len(args.tokenizer.vocab),'input_shape':list(tokens.shape)},
     'parameter_count':sum(v.numel() for v in model.parameters()),'seed':7,'threads':1,
     'cli_dropout':dropout_cli,'effective_config_dropout':args.dropout,
     'input_sha256':hashlib.sha256(tokens.numpy().tobytes()).hexdigest(),
     'logits_shape':list(logits.shape),'finite_loss':float(loss),
     'forward_wall_seconds_single_observation':elapsed,
     'max_rss_kib_process':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
     'metrics':{'paper_accuracy':'Unknown','paper_precision':'Unknown','paper_recall':'Unknown','paper_f1':'Unknown'},
     'limitations':['Artificial tokens and two synthetic labels','No pretraining or original checkpoint','Sequence16 not paper pretraining512; same base width/depth','Dropout0.1 from config overwrites requested0.5','Timing is a functional one-off observation, not comparable inference benchmark']}
(ROOT/'evidence/et_bert/cpu_model_smoke.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))

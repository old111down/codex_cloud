#!/usr/bin/env python3
"""Bounded synthetic classifier smoke; no paper metric equivalence claim."""
import json
import numpy as np
import pandas as pd
import pyshark
import xgboost as xgb
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score

# Linearly separated toy classes; these are synthetic, not network captures.
x = np.array([[i, i % 3, i * 0.1] * 5 for i in range(30)], dtype=float)
y = np.array([i % 3 for i in range(30)])
model = xgb.XGBClassifier(n_estimators=2, max_depth=2, n_jobs=2, eval_metric='mlogloss')
model.fit(StandardScaler().fit_transform(x), y)
pred = model.predict(StandardScaler().fit_transform(x))
assert pred.shape == y.shape
assert set(pred).issubset(set(y))
print(json.dumps({'test':'synthetic_dependency_and_fit_smoke','input_shape':list(x.shape),
                  'output_shape':list(pred.shape),'synthetic':True,'pass':True,
                  'note':'No paper accuracy, traffic-parser, throughput, or hardware claim'}, indent=2))

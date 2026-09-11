#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json

with open('results/a1_test.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print('Sample predictions vs ground truth:')
print('=' * 80)
for i in range(15):
    pred = data['predictions'][i]
    ref = data['references'][i]
    match = 'MATCH' if pred == ref else 'DIFF'
    print('{0}. {1}'.format(i+1, match))
    print('   Predicted:    "{0}"'.format(pred))
    print('   Ground truth: "{0}"'.format(ref))
    print()

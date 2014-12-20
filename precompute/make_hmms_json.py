from collections import defaultdict
import json
import os

hmm_descriptions = {}
for hf in os.listdir('../data/hmms/'):
  if not hf.startswith('.'):
    with open(os.path.join('../data/hmms', hf)) as f:
      description = None
      for l in f:
        if l.startswith('DESC') or l.startswith('NAME'):
          description = l.split(None, 1)[1].strip()
        elif l.startswith('HMM '):
          break
      if description:
        hmm_descriptions[hf.split('.')[0]] = description
  
all_hmms = hmm_descriptions.keys()

markers = []
with open('markers.txt') as f:
  markers = [l.strip() for l in f if l.strip() in hmm_descriptions]

properties = {}
with open('PROP_DEF_WITHOUT_DESCRIPTION_FIELD.TABLE') as f:
  for l in f:
    parts = l.strip().split('\t')
    properties[parts[0]] = (parts[1], parts[2], parts[3])

property_to_step = defaultdict(list)
with open('PROP_STEP.TABLE') as f:
  for l in f:
    parts = l.strip().split('\t')
    if len(parts) >= 2:
      property_to_step[parts[1]].append(parts[0])

step_to_accession = defaultdict(list)
with open('STEP_EV_LINK.TABLE') as f:
  for l in f:
    if 'HMM' in l:
      parts = l.strip().split('\t')
      if parts[2] in all_hmms:
        step_to_accession[parts[1]].append(parts[2])

property_to_hmms = {}
for prop, steps in property_to_step.iteritems():
  hmms = []
  for step in steps:
    hmms += step_to_accession[step]
  if len(hmms) > 0:
    property_to_hmms[prop] = hmms

properties = {k:v for k,v in properties.iteritems() if k in property_to_hmms}

go_to_property = defaultdict(set)
with open('PROP_GO_LINK.TABLE') as f:
  for l in f:
    parts = l.strip().split('\t')
    if parts[0] in properties:
      go_to_property[parts[1]].add(parts[0])

go_to_property = {k:list(v) for k,v in go_to_property.iteritems()}

with open('../data/hmms.json', 'w') as f:
  json.dump({'properties' : properties, 'prop_to_hmms' : property_to_hmms,
             'all_hmms' : hmm_descriptions, 'go_props': go_to_property,
             'markers' : markers}, f)

os.chmod('../data/hmms.json', 0774)

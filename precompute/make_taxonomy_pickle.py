# nodes.dmp and names.dmp is required. names.dmp should be trimmed to only
# include scientific names.
import pickle

names = {}
with open('trimmed.names.dmp') as f:
  for l in f:
    parts = l.split('|')
    names[int(parts[0].strip())] = parts[1].strip()

parents = {}
ranks = {}
with open('nodes.dmp') as f:
  for l in f:
    parts = l.split('|')
    taxid = int(parts[0].strip())
    parent = int(parts[1].strip())
    rank = parts[2].strip()
    parents[taxid] = parent
    ranks[taxid] = rank

with open('../data/taxonomy.pickle', 'w') as f:
  pickle.dump({'names': names, 'parents': parents, 'ranks': ranks}, f)

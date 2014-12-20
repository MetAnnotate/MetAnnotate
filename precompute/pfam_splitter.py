import os

def hmms():
  with open('Pfam-A.hmm') as f:
    lines = []
    for l in f:
      lines.append(l)
      if l.startswith('//'):
        yield lines
        lines = []

for hmm in hmms():
  name = hmm[2].split()[1].split('.')[0]
  with open(os.path.join('../data/hmms', '%s.HMM' % name), 'w') as f:
    f.writelines(hmm)

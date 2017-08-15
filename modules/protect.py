import json
import os
import shutil
import sqlite3
import sys

if len(sys.argv) < 2:
  print 'Job ID not provided'
  sys.exit(1)
job_id = sys.argv[1]

conn = sqlite3.connect('databases/results.db')
cursor = conn.cursor()
cursor.execute('SELECT result FROM results WHERE id = ? LIMIT 1', (job_id,))
rows = cursor.fetchall()
if len(rows) == 0:
  print 'No such job ID'
  sys.exit(1)

result = json.loads(rows[0][0])

def SecureFiles(data):
  for k, v in (data.items() if isinstance(data, dict) else enumerate(data)):
    if isinstance(v, dict) or isinstance(v, list):
      SecureFiles(v)
    elif isinstance(v, str) or isinstance(v, unicode):
      if v.startswith('_sample_'):
        continue
      # Krona files have ? parameters.
      old_path = v
      if '?' in old_path:
        old_path = old_path[:old_path.index('?')]
      output = os.path.join('output', os.path.basename(old_path))
      new_name = '_sample_%s' % old_path
      new_output = os.path.join('output', new_name)
      if os.path.isfile(output):
        shutil.move(output, new_output)
      if os.path.isfile(new_output):
        data[k] = '_sample_%s' % v
      # Moves ssi or phyloxml file.
      ssi_file = '%s.ssi' % v
      phyloxml_file = '%s.phyloxml' % v
      other_file = None
      if os.path.isfile(os.path.join('output', ssi_file)):
        other_file = ssi_file
      if os.path.isfile(os.path.join('output', phyloxml_file)):
        other_file = phyloxml_file
      if other_file:
        new_name = '_sample_%s' % other_file
        old_output = os.path.join('output', other_file)
        new_output = os.path.join('output', new_name)
        shutil.move(old_output, new_output)

SecureFiles(result)
cursor.execute('UPDATE results SET protected = 1, result = ? WHERE id = ?',
               (json.dumps(result), job_id))
conn.commit()
conn.close()

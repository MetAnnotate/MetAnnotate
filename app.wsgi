#!/usr/bin/python
"""
This is a WSGI script that utilizes the bottle framework to route URLs and
invoke templates.
"""

import atexit
import json
import logging
import os
import random
import re
import sqlite3
import signal
import socket
import subprocess
import sys
import tempfile
import time
import traceback
sys.path.append(os.path.dirname(__file__))

from Bio import SeqIO

import paramiko

from bottle import route, post, run, static_file, template, request, BaseRequest
from bottle import delete, default_app, abort, response, redirect

from beaker.middleware import SessionMiddleware

import celery
import celery.result as cr
import celery.backends.amqp as amqp
import celery.task.control as control

import tasks

local_run = False
host_name = socket.gethostname()

os.chdir(os.path.dirname(os.path.abspath(__file__)))
logging.basicConfig(level=logging.DEBUG)

# Allow large requests.
BaseRequest.MAX_PARAMS = 10000
BaseRequest.MEMFILE_MAX = 1024 * 1024

metagenomes_root = ''
with open('metagenome_directories_root.txt') as f:
  for l in f:
    metagenomes_root = l.strip()
    break

required_password = None
try:
  with open('metannotate.pw') as f:
    for l in f:
      required_password = l.strip()
      break
except IOError:
  pass

@route('/sequence/<filename>/<name>')
def GetSequence(filename, name):
  full = os.path.join('output', os.path.basename(filename))
  if not os.path.isfile(full):
    return ''
  child = subprocess.Popen(['esl-sfetch', full, name.split()[0]],
                           stdout=subprocess.PIPE)
  out, err = child.communicate()
  return out

@post('/tail/')
def GetTails():
  stdout = request.forms.stdout
  stderr = request.forms.stderr
  if stdout:
    stdout = os.path.basename(stdout)
    if stdout.startswith('tmp'):
      stdout = os.path.join('tmp', stdout)
    else:
      stdout = os.path.join('output', stdout)
  if stderr:
    stderr = os.path.basename(stderr)
    if stderr.startswith('tmp'):
      stderr = os.path.join('tmp', stderr)
    else:
      stderr = os.path.join('output', stderr)
  data = {}
  if os.path.isfile(stdout):
    data['stdout'] = os.popen('tail -20 %s' % stdout).read();
  if os.path.isfile(stderr):
    data['stderr'] = os.popen('tail -20 %s' % stderr).read();
  return data

@post('/stop/')
def StopProcess():
  pid = request.forms.pid
  if pid:
    if local_run:
      os.kill(pid, signal.SIGKILL)
      return
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    password = ''
    with open('celery.pw') as f:
      for l in f:
        password = l.strip()
        break
    ssh.connect(host_name, username='celery', password=password)
    ssh.exec_command('kill %d' % int(pid))

@post('/subtree/')
def subtree():
  tree_file = request.forms.tree
  node_name = request.forms.node
  homolog = request.forms.homolog
  p = subprocess.Popen(["python", "subtree.py", tree_file, node_name, homolog],
                       stdout=subprocess.PIPE)
  out, err = p.communicate()
  return out

@route('/')
def index():
  s = request.environ.get('beaker.session')
  if required_password and s.get('authenticated',0) == 0:
    return template('authenticate')
  return template('index')

@route('/about/')
def about():
  return template('about')

@route('/contact/')
def contact():
  return template('contact')

@route('/examples/')
def contact():
  return template('examples')

@route('/scripts/')
def contact():
  return template('scripts')

@route('/cite/')
def contact():
  return template('citations')

@post('/authenticate/')
def authenticate():
  password = request.forms.password
  if password == required_password:
    s = request.environ.get('beaker.session')
    s['authenticated'] = 1
  redirect('/')

@delete('/delete/<path>')
def delete_upload(path):
  path = os.path.join('input', os.path.basename(path))
  if os.path.isfile(path):
    os.remove(path)

def VerifyHMM(path):
  valid = False
  with tempfile.NamedTemporaryFile(dir='tmp') as stdout, \
       tempfile.NamedTemporaryFile(dir='tmp') as stderr:
    the_process = subprocess.Popen(['hmmstat', path],
                                   stdout=stdout, stderr=stderr)
    return_code = the_process.wait()
    if return_code == 0:
      stdout.flush()
      with open(stdout.name) as f:
        for l in f:
          if len(l) > 0 and l[0].isdigit():
            valid = True
            break
  return valid

@post('/hmm-upload/')
def upload_hmm_post():
  return {'files': handle_upload(request.files.items(), VerifyHMM)}

def VerifyORF(path):
  sequences = SeqIO.parse(path, 'fasta')
  total = sum(1 for s in sequences)
  return total != 0

@post('/orf-upload/')
def upload_orf_post():
  return {'files': handle_upload(request.files.items(), VerifyORF)}

def VerifyMSA(path):
  consensus = -1
  current_len = -1
  with open(path) as f:
    for l in f:
      if l.startswith('>'):
        if current_len >= 0:
          if consensus >= 0 and consensus != current_len:
            return False
          elif consensus == -1:
            consensus = current_len
        current_len = 0
      elif current_len >= 0:
        current_len += len(l) - 1
  if consensus > 0 and current_len == consensus:
    return VerifyORF(path) # Verify Fasta format.
  else:
    return False

@post('/msa-upload/')
def upload_msa_post():
  return {'files': handle_upload(request.files.items(), VerifyMSA)}

def VerifyTree(path):
  # Again, we need to launch a subrocess since ete2 cannot be imported here due
  # to a cyclic reference in the library.
  p = subprocess.Popen(["python", "tree_check.py", path])
  p.communicate()
  return p.returncode == 0

@post('/tree-upload/')
def upload_tree_post():
  return {'files': handle_upload(request.files.items(), VerifyTree)}

def VerifyLog(path):
  with open(path) as f:
    for l in f:
      if l.startswith('Command: '):
        return True
      return False

@post('/log-upload/')
def upload_log_post():
  return {'files': handle_upload(request.files.items(), VerifyLog)}

def DirectoryList(current):
  files = []
  for subfile in os.listdir(current):
    full_subfile = os.path.join(current, subfile)
    if os.path.isfile(full_subfile):
      if (subfile.endswith('.fa') or subfile.endswith('.faa') or
          subfile.endswith('.fasta')):
        files.append(subfile)
      else:
        continue
    elif os.path.isdir(full_subfile):
      sublist = DirectoryList(full_subfile)
      if len(sublist) > 0:
        files.append((subfile, sublist))
  return files

@route('/metagenomes/')
def metagenomes():
  metagenomes = []
  with open('metagenome_directories.txt') as f:
    for l in f:
      directory = os.path.join(metagenomes_root, l.strip())
      sublist = DirectoryList(directory)
      if len(sublist) > 0:
        metagenomes.append((os.path.basename(directory), sublist))
  return {'listing' : metagenomes}

#TODO(ppetrenk): Cancel job while active.
@route('/unsubmit/<job>')
def unsubmit(job):
  control.revoke(job)

  redirect('/status/%s' % job)

def RevokedJobs():
  process = os.popen('celery inspect revoked')
  output = process.read()
  process.close()
  jobs = []
  for l in output.split('\n'):
    m = re.search("[-\w]{16,}", l)
    if m:
      jobs.append(m.group(0))
  jobs.reverse()
  return jobs

def IsRevoked(job):
  return job in RevokedJobs()

def QueuedJobs():
  process = os.popen('celery inspect reserved')
  output = process.read()
  process.close()
  jobs = [re.search("id': u'([^']+)'", l).group(1)
          for l in output.split('\n') if 'id' in l]
  revoked = RevokedJobs()
  jobs = [j for j in jobs if j not in revoked]
  jobs.sort(key=lambda x: int(x.split('-')[1]))
  return jobs

def IsActive(job):
  process = os.popen('celery inspect active')
  output = process.read()
  process.close()
  jobs = [re.search("id': u'([^']+)'", l).group(1)
          for l in output.split('\n') if 'id' in l]
  return job in jobs

@post('/submit/')
def submit_job():
  hmm_evalue = request.forms.hmm_evalue
  refseq_hmm_evalue = request.forms.refseq_hmm_evalue
  percent_id = request.forms.percent_id
  min_coverage = request.forms.min_coverage
  min_alignment = request.forms.min_alignment
  hmm_file_names = (request.forms.hmm_files.split(',')
                    if request.forms.hmm_files else [])
  hmm_file_names = [p.split('||') for p in request.forms.hmm_files.split(',')]
  hmm_files = [(hf[0], os.path.join('input/', os.path.basename(hf[1])))
               for hf in hmm_file_names if not hf[1].startswith('stored-')]
  hmm_files += [(hf[0], os.path.join(
                  'data/hmms', '%s.HMM' % os.path.basename(hf[1][7:])))
                for hf in hmm_file_names if hf[1].startswith('stored-')]
  orf_file_names = ([p.split('||') for p in request.forms.orf_files.split(',')]
                    if request.forms.orf_files else [])
  orf_files = [(of[0], os.path.join('input/', os.path.basename(of[1])))
               for of in orf_file_names if not of[1].startswith('stored/')]
  orf_files += [(of[0], os.path.join(metagenomes_root, of[1][7:]))
                for of in orf_file_names if of[1].startswith('stored/')]
  reference_msa = request.forms.reference_msa
  if reference_msa:
    reference_msa = os.path.join('input', reference_msa)
  reference_tree = request.forms.reference_tree
  if reference_tree:
    reference_tree = os.path.join('input', reference_tree)
  reference_log = request.forms.reference_log
  if reference_log:
    reference_log = os.path.join('input', reference_log)
  filter_multi_orf = bool(request.forms.filter_multi_orf)
  filter_multi_refseq = bool(request.forms.filter_multi_refseq)
  transeq = bool(request.forms.transeq)
  force_msa = bool(request.forms.force_msa)
  mode = request.forms.mode or 'sequence'
  do_sequence_classification = mode in ('sequence', 'both')
  do_phylogenetic_classification = mode in ('phylogenetic', 'both')

  if (not reference_tree or not reference_msa or not reference_log or
      not os.path.isfile(reference_tree) or
      not os.path.isfile(reference_log) or
      not os.path.isfile(reference_msa)):
    reference_tree = None
    reference_msa = None
    reference_log = None
  else:
    new_location = os.path.join('realinput', os.path.basename(reference_tree))
    os.system('mv %s %s' % (reference_tree, new_location))
    reference_tree = new_location
    new_location = os.path.join('realinput', os.path.basename(reference_msa))
    os.system('mv %s %s' % (reference_msa, new_location))
    reference_msa = new_location
    new_location = os.path.join('realinput', os.path.basename(reference_log))
    os.system('mv %s %s' % (reference_log, new_location))
    reference_log = new_location

  for n, f in hmm_files + orf_files:
    if not os.path.isfile(f):
      abort(400, 'File has not been uploaded: %s' % f)
      return
  if len(hmm_files) < 1 or len(orf_files) < 1:
    abort(400, 'ORF or HMM file not supplied.')
    return
  try:
    hmm_evalue = abs(float(hmm_evalue))
  except ValueError:
    hmm_evalue = 1e-6
  try:
    refseq_hmm_evalue = abs(float(refseq_hmm_evalue))
  except ValueError:
    refseq_hmm_evalue = 1e-6
  try:
    min_coverage = abs(float(min_coverage))
  except ValueError:
    min_coverage = 0.0
  try:
    percent_id = min(abs(float(percent_id)), 1.0)
  except ValueError:
    precent_id = 0.5
  try:
    min_alignment = abs(int(min_alignment))
  except ValueError:
    min_alignment = 0
  moved_hmm_files = []
  moved_orf_files = []
  try:
    # Move input files to realinput.
    for old_files, new_files in ((hmm_files, moved_hmm_files),
                                 (orf_files, moved_orf_files)):
      for n,f in old_files:
        if f.startswith('input/'):
          new_location = os.path.join('realinput', os.path.basename(f))
          os.system('mv %s %s' % (f, new_location))
          new_files.append((n,new_location))
        else:
          new_files.append((n,f))
    # Schedules the job in the correct queue.
    s = request.environ.get('beaker.session')
    task = tasks.RunPipeline.apply_async(
      [moved_orf_files, moved_hmm_files, hmm_evalue, refseq_hmm_evalue,
       percent_id, do_sequence_classification,
       do_phylogenetic_classification, force_msa, filter_multi_orf,
       filter_multi_refseq, transeq, min_coverage, min_alignment,
       reference_msa, reference_tree, reference_log],
      task_id='%d-%d' % (int(random.random()*1000000000),
                         int(time.time()*1000000)))
    return {'job-id': task.task_id}
  except Exception, ex:
    traceback.print_exc(file=sys.stderr)
    # Makes sure input files do not accumulate due to unforseen errrors.
    for f in moved_hmm_files + [of[1] for of in moved_orf_files]:
      if f.startswith('realinput') and os.path.isfile(f):
        os.remove(f)
    raise ex

@route('/hmm_index')
def retrieve_hmm_index():
  return static_file('hmms.json', root='data', mimetype='text/json')

@route('/annotations/<results>')
def retrieve_results(results):
  output_file = 'output/%s' % os.path.basename(results)
  if not os.path.isfile(output_file):
    abort(404, 'Results file not found')
    return
  return static_file(results, root='output', download='%s.tsv' % results,
                     mimetype='text/plain')

@route('/reads/<reads>')
def retrieve_results(reads):
  output_file = 'output/%s' % os.path.basename(reads)
  if not os.path.isfile(output_file):
    abort(404, 'Results file not found')
    return
  return static_file(reads, root='output', download='%s.faa' % reads,
                     mimetype='text/plain')

@route('/alignment/<msa>')
def retrieve_alignment(msa):
  output_file = 'output/%s' % os.path.basename(msa)
  if not os.path.isfile(output_file):
    abort(404, 'Results file not found')
    return
  return static_file(msa, root='output', download=(msa if '.fa' in msa else
                                                   '%s.faa' % msa),
                     mimetype='text/plain')

@route('/zip/<all_files>')
def retrieve_zip(all_files):
  output_file = 'output/%s' % os.path.basename(all_files)
  if not os.path.isfile(output_file):
    abort(404, 'Results file not found')
    return
  return static_file(all_files, root='output', download=all_files,
                     mimetype='application/zip, application/octet-stream')

@route('/fasttree-log/<log>')
def retrieve_log(log):
  output_file = 'output/%s' % os.path.basename(log)
  if not os.path.isfile(output_file):
    abort(404, 'Results file not found')
    return
  return static_file(log, root='output', download='%s.txt' % log,
                     mimetype='text/plain')

@route('/krona/<krona>')
def retrieve_krona(krona):
  output_file = 'output/%s' % os.path.basename(krona)
  if not os.path.isfile(output_file):
    abort(404, 'Results file not found')
    return
  return static_file(krona, root='output', mimetype='text/html')

@route('/tree/<tree>')
def retrieve_tree(tree):
  output_file = 'output/%s' % os.path.basename(tree)
  if not os.path.isfile(output_file):
    abort(404, 'Results file not found')
    return
  return static_file(tree, root='output', download='%s.newick' % tree,
                     mimetype='text/plain')

@route('/status/<job>')
def status_page(job):
  return template('status', job=job)

@route('/job/<job>')
def check(job):
  s = request.environ.get('beaker.session')
  async_result = cr.AsyncResult(job, backend=amqp.AMQPBackend(tasks.app))
  result = {}

  # Running:
  celery_state = async_result.state
  celery_result = async_result.result
  if (celery_state != 'PENDING' and celery_state != 'FAILURE' and
      'states' in celery_result):
    result['meta'] = celery_result
    states = [
      ('TRANSEQ', 'Running EMBOSS Transeq on provided ORFs'),
      ('HMMSEARCH1', 'Performing hmmsearch on provided ORFs'),
      ('HMMSEARCH2', 'Performing hmmsearch on Refseq database'),
      ('USEARCH', 'Performing usearch to find closest homologs.'),
      ('HMMALIGN', 'Performing hmmalign on Refseq and ORF hits'),
      ('FASTTREE', 'Building tree for ORF and Refseq hits using FastTree and '
                   'pplacer'),
      ('TAXONOMY', 'Assigning Taxonomy'),
      ('SUCCESS', 'Job Completed'),
    ]
    final_states = []
    pipeline_states = result['meta']['states']
    overlap_states = [s[0] for s in states if s[0] in pipeline_states]
    current_state = overlap_states[-1]
    current_state_found = False
    for state, description in states:
      if state == current_state:
        current_state_found = True
      if current_state_found or state in pipeline_states:
        final_states.append((state, description))

    result['state'] = current_state,
    result['states'] = final_states
    return result
    
  # Queued:
  jobs = QueuedJobs()
  is_revoked = IsRevoked(job)
  if not is_revoked and job in jobs:
    result['position'] = [jobs.index(job) + 2, len(jobs) + 1]
    return result

  # Failure:
  if celery_state == 'FAILURE' or is_revoked:
    result['failed'] = True
    return result

  # Finished:
  conn = sqlite3.connect('databases/results.db')
  cursor = conn.cursor()
  cursor.execute('SELECT result FROM results WHERE id = ? LIMIT 1', (job,))
  rows = cursor.fetchall()
  if len(rows) > 0:
    result['result'] = json.loads(rows[0][0])
    return result

  # Doesn't exist:
  if not IsActive(job):
    result['no_exist'] = True

  return result

# Static files: CSS, JS, PNG, and JPEG.
@route('/css/<filename:re:.*\.css>')
def send_css(filename):
  return static_file(filename, root='./css/', mimetype='text/css')

@route('/img/<filename:re:.*\.png>')
def send_img(filename):
  return static_file(filename, root='./img/', mimetype='image/png')

@route('/img/<filename:re:.*\.jpg>')
def send_img_jpg(filename):
  return static_file(filename, root='./img/', mimetype='image/jpeg')

@route('/css/images/<filename:re:.*\.png>')
def send_css_img(filename):
  return static_file(filename, root='./css/images/', mimetype='image/png')

@route('/js/<filename:re:.*\.js>')
def send_js(filename):
  return static_file(filename, root='./js/', mimetype='text/javascript')

@route('/fonts/<filename>')
def send_font(filename):
  return static_file(filename, root='./fonts/')

def get_file_size(f):
  f.seek(0, 2)  # Seek to the end of the file
  size = f.tell()  # Get the position of EOF
  f.seek(0)  # Reset the file position to the beginning
  return size

def handle_upload(files, verifier):
  results = []
  for name, file_upload in files:
    if type(file_upload) is unicode:
      continue
    result = {}
    result['name'] = re.sub(
      r'^.*\\',
      '',
      file_upload.raw_filename
    )
    result['type'] = file_upload.content_type
    result['size'] = get_file_size(file_upload.file)
    save_path = tempfile.mkstemp(dir='input', prefix='up',
                                 suffix=str(int(random.random()*1000000000)))[1]
    file_upload.save(save_path, overwrite=True)
    if not verifier(save_path):
      os.remove(save_path)
      continue
    os.chmod(save_path, 0770)
    result['deleteType'] = 'DELETE'
    result['deleteUrl'] = 'dummy'
    if not 'url' in result:
      result['url'] = 'dummy'
    result['key'] = os.path.basename(save_path)
    results.append(result)
  return results

conn = sqlite3.connect('databases/results.db')
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS results (id TEXT, result TEXT, '
                                                   'created DATETIME, '
                                                   'protected INT)')
cursor.execute('CREATE INDEX IF NOT EXISTS searcher ON results(id)')
cursor.execute('CREATE INDEX IF NOT EXISTS datesearch ON results(created, '
               'protected)')
os.chmod('databases/results.db', 0664)
conn.close()

session_opts = {
    'session.type': 'file',
    'session.cookie_expires': 60 * 60 * 24 * 30,
    'session.data_dir': './session',
    'session.auto': True
}

application = SessionMiddleware(default_app(), session_opts)

# Can be run using bottles default web server or as a WSGI script.
if len(sys.argv) > 1 and sys.argv[1] == 'local':
  local_run = True

  # Kill previously running celery processes.
  p = subprocess.Popen(['ps', '-ax'], stdout=subprocess.PIPE)
  out, err = p.communicate()
  for line in out.splitlines():
    if 'celery' in line and 'tasks' in line:
      pid = int(line.split(None, 1)[0])
      os.kill(pid, signal.SIGKILL)
      print 'Previous celery process killed.'

  # Kill celery processes at exit.
  def CleanUp():
    if celery_process:
      os.killpg(celery_process.pid, signal.SIGTERM)
      print 'Killed celery process.'

  atexit.register(CleanUp)

  # Starts the celery process in the background.
  celery_process = subprocess.Popen(
    ["celery", "-A", "tasks", "worker", "--loglevel=info"],
    preexec_fn=os.setsid)

  run(app=application, host='0.0.0.0', port=8080, debug=True)

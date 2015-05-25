import sys,os,re,tempfile,time,glob,commands,random,subprocess,traceback
import cStringIO as StringIO
import cPickle as pickle
from collections import defaultdict, Counter
import celery
import heapq
import json
import shutil
import sqlite3

CONCURRENCY = '2'
CONCURRENCY_SPECIFIED = False
OUTPUT_DIR = 'output'
TMP_DIR = 'tmp'

def run_process(args, stdout_file=None, meta=None, task=None):
  stdout_handle = (open(stdout_file, 'w') if stdout_file else
                   tempfile.NamedTemporaryFile(dir=TMP_DIR))
  stderr_handle = tempfile.NamedTemporaryFile(dir=TMP_DIR)
  with stdout_handle as stdout, stderr_handle as stderr:
    the_process = subprocess.Popen(args, stdout=stdout, stderr=stderr)
    if meta and task:
      meta['pid'] = the_process.pid
      meta['stdout'] = os.path.basename(stdout.name)
      meta['stderr'] = os.path.basename(stderr.name)
      os.chmod(stdout.name, 0774)
      os.chmod(stderr.name, 0774)
      task.update_state(meta=meta)
    else:
      print >> sys.stderr, 'Running commands: %s' % ' '.join(args)
    return_code = the_process.wait()
    if meta and task:
      del meta['pid']
      del meta['stdout']
      del meta['stderr']
      task.update_state(meta=meta)
    if return_code != 0:
      stderr.flush()
      with open(stderr.name) as stderr_output:
        print >> sys.stderr, stderr_output.read()
      raise Exception('Command failed: %s', ' '.join(args))

def GetLineage(taxid, parents):
  lineage = []
  current = taxid
  while current != 1 and current in parents:
    lineage.append(current)
    current = parents[current]
  return lineage

def GetLineageNames(taxid, parents, name_dictionary):
  lineage = GetLineage(taxid, parents)
  return [name_dictionary[taxid] for taxid in lineage]

LINEAGE_LEVELS = ('species', 'genus', 'family', 'order', 'class', 'phylum',
                  'superkingdom')
def GetLineageForHomolog(taxid, parents, name_dictionary, ranks):
  lineage = GetLineage(taxid, parents)
  lineage = {ranks[l]:name_dictionary[l] for l in lineage}
  final_lineage = []
  best = 'unclassified'
  for rank in LINEAGE_LEVELS:
    final_lineage.append(lineage[rank] if rank in lineage else best)
    best = final_lineage[-1]
  return final_lineage

def _ChooseRepresentatives(node):
  new_phylogeny = {}
  for rank, counts in node.phylogeny.items():
    new_phylogeny[rank] = counts.most_common(1)[0]
  if len(new_phylogeny) == 0:
    node.phylogeny = {}
    return
  max_count = float(max(common[1] for common in new_phylogeny.values()))
  node.phylogeny = {k:(v[0], v[1]/max_count) for k,v in new_phylogeny.items()}

def UpdateTreeWithPhyloConsistency(node, taxid_dictionary, ranks, parents):
  node.phylogeny = defaultdict(lambda :Counter())
  if node.is_leaf():
    if node.name and node.name.startswith('gi|'):
      gi_num = node.name.split("|")[1]
      taxid = taxid_dictionary[gi_num]
      lineage = GetLineage(taxid, parents)
      for taxid in lineage:
        rank = ranks[taxid]
        node.phylogeny[rank][taxid] = 1
  else:
    for child in node.children:
      UpdateTreeWithPhyloConsistency(child, taxid_dictionary, ranks, parents)
      for rank, counts in child.phylogeny.iteritems():
        node.phylogeny[rank].update(counts)
      _ChooseRepresentatives(child)
  if node.is_root():
    _ChooseRepresentatives(node)

def _MakeTemp(all_temp, make_directory=False, extension=''):
  if make_directory:
    temp_file = tempfile.mkdtemp(dir=TMP_DIR)
  else:
    fd, temp_file = tempfile.mkstemp(dir=TMP_DIR, suffix=extension)
    os.close(fd)
  all_temp.append(temp_file)
  return temp_file

def _SafeReadName(name, description, orf_index=None, coords=None):
  parts = [re.sub(r'[^\w-]+', '_', name).strip('_')]
  if description != '-':
    parts.append(re.sub(r'[^\w-]+', '_', description).strip('_'))
  if orf_index is not None:
    parts.append('ma%s' % orf_index)
  if coords is not None:
    parts.append('%s_to_%s' % coords)
  return '_'.join(parts)

def _TrimSafeReadName(safe_name):
  return safe_name[:safe_name.rindex('_ma')]

def _LengthFromName(safe_name):
  parts = safe_name.split('_')
  return str(int(parts[-1]) - int(parts[-3]) + 1)

app = celery.Celery('tasks', broker='amqp://', backend='amqp://')
app.config_from_object('celeryconfig')

def _CreateKronaCountFile(temp_files, counts, parents, name_dictionary):
  krona_text_file = _MakeTemp(temp_files)
  with open(krona_text_file, 'w') as f:
    for taxid, count in counts.iteritems():
      if not taxid:
        f.write(str(count))
        f.write('\n')
        continue
      lineage = reversed(GetLineageNames(taxid, parents, name_dictionary))
      lineage = list(lineage)
      lineage.insert(0, str(count))
      f.write('\t'.join(lineage))
      f.write('\n')
  return krona_text_file

def _CreateMergedKronaFile(all_count_files, krona_file):
  # Prepare krona chart for HMM.
  to_merge = []
  for dataset_name, clade_counts in all_count_files:
    if clade_counts:
      to_merge.append('%s,%s' % (clade_counts, dataset_name))
  run_process(['ktImportText', '-o', krona_file] + to_merge)

def _CreateMergedKronaAndAssignLinks(dataset_type, krona_name, dataset_names,
                                     main_name, counts, elements, main_element,
                                     temp_files):
  krona_file = MakeOutputFile([krona_name, 'krona'])
  krona_file_base = os.path.basename(krona_file)
  combined_clade_counts = _MakeTemp(temp_files)
  run_process(['cat'] + [count for count in counts if count],
               stdout_file=combined_clade_counts)
  counts.append(combined_clade_counts)
  _CreateMergedKronaFile(zip(dataset_names + [main_name], counts), krona_file)
  dataset_offset = 0
  krona_key = '%s_krona' % dataset_type
  for element_index, element in enumerate(elements):
    if counts[element_index]:
      element[krona_key] = '%s?collapse=false&dataset=%d' % (
        krona_file_base, dataset_offset)
      dataset_offset += 1
  main_element[krona_key] = '%s?collapse=false&dataset=%d' % (
    krona_file_base, dataset_offset)

def _GetHMMInfo(hmm_index, hmm_file, hmm_file_name, temp_files):
  hmm_stat_file = _MakeTemp(temp_files)
  run_process(['hmmstat', hmm_file], stdout_file=hmm_stat_file)
  hmm_family = None
  hmm_length = 1
  with open(hmm_stat_file) as f:
    for l in f:
      if len(l) > 0 and l[0].isdigit():
        parts = l.split()
        hmm_family = parts[1]
        hmm_length = int(parts[5]) if parts[5].isdigit() else hmm_length
        break
  if not hmm_family or len(hmm_family) == 0:
    hmm_family = hmm_file_name or 'unknown_hmm'
  hmm_family_safe = _SafeFileName(hmm_family, hmm_index)

  hmm_description = ''
  with open(hmm_file) as f:
    for l in f:
      if l.startswith('DESC'):
        parts = l.split(None, 1)
        hmm_description = parts[1].strip()
        break

  return hmm_family_safe, hmm_description, hmm_length
  

def _SafeFileName(file_name, file_index):
  safe_name = file_name
  if (file_name.lower().endswith('.fa') or
      file_name.lower().endswith('.faa') or
      file_name.lower().endswith('.txt')):
    safe_name = os.path.splitext(safe_name)[0]
  safe_name = re.sub(r'\W+', '_', safe_name)
  return '%s_%d' % (safe_name, file_index)

def FindOrfHits(orf_files, hmm_evalue, min_alignment, filter_multi, hmm_file,
                hmm_family_safe, temp_files, column, task, meta):
  # Process each metagenome file.
  orf_index = 0
  read_files = []
  hmm_hit_files = []
  safe_orf_names = []
  hmm_hit_evalues = []
  for orf_file_index, (orf_file_name, orf_file) in enumerate(orf_files):
    cell = {}
    column['rows'].append(cell)
    orfs_name_safe = _SafeFileName(orf_file_name, orf_file_index)
    safe_orf_names.append(orfs_name_safe)

    msa_file = _MakeTemp(temp_files)
    converted_msa_file = _MakeTemp(temp_files)
    hmm_out_file = _MakeTemp(temp_files)
    run_process(['hmmsearch', '-o', '/dev/null', '-A', msa_file,
                 '--domtblout', hmm_out_file,
                 '-E' if filter_multi else '--domE', str(hmm_evalue), '--cpu',
                 CONCURRENCY, hmm_file, orf_file], task=task, meta=meta)

    # Parses output to retrieve e-values and ids. Tedious.
    hmm_evalues = {}
    final_hmm_evalues = {}
    identifiers = defaultdict(lambda: defaultdict(dict))
    sequences_hit = {}
    
    with open(hmm_out_file) as f:
      line1 = f.readline()
      line2 = f.readline()
      name_end = line2.index('accession')
      hmm_start = line2.index('tlen') + 4
      hmm_end = line2.rindex('accession')
      if filter_multi:
        eval_start = line2.index('qlen') + 4
        eval_end = line2.index('E-value') + 7
      else:
        eval_start = line2.index('c-Evalue') + 8
        eval_end = line2.index('i-Evalue') + 8
      coords_start = line1.index('hmm coord') + 9
      coords_end = line1.index('ali coord') + 9
      description_start = line2.index('description of target')
      for line in f:
        try:
          if line.startswith('#'):
            continue
          evalue = line[eval_start:eval_end].strip()
          if float(evalue) > hmm_evalue:
            continue
          name = line[:name_end].strip()
          coords = tuple(line[coords_start:coords_end].strip().split())
          if int(coords[1]) - int(coords[0]) + 1 < min_alignment:
            continue
          description = line[description_start:-1]
          safe_name = _SafeReadName(name, description, orf_index, coords)
          if filter_multi and (name, description) in sequences_hit:
            existing = sequences_hit[(name,description)]
            if existing in hmm_evalues:
              del hmm_evalues[existing]
            continue
          elif filter_multi:
            sequences_hit[(name, description)] = safe_name
          hmm_evalues[safe_name] = evalue
          identifiers[name][description][coords] = orf_index
          orf_index += 1
        except Exception as e:
          print >> sys.stderr, 'Warning, problem parsing hmmsearch output: '
          print >> sys.stderr, str(e)
          
    if len(hmm_evalues) == 0:
      hmm_hit_evalues.append({})
      hmm_hit_files.append('')
      cell['sequences_hit'] = 0
      continue

    # Retrieves sequences for matching hits. Avoid SeqIO for speed.
    seqs_file = MakeOutputFile([hmm_family_safe, orfs_name_safe, 'reads'])
    seen = set()
    with open(orf_file) as input_handle:
      with open(seqs_file, 'w') as output_handle:
        seq = False
        for l in input_handle:
          if l.startswith('>'):
            seq = False
            if l[1].isspace():
              parts = l.split(None, 2)
              name = parts[1]
              description = parts[2][:-1] if len(parts) == 3 else '-'
            else:
              parts = l.split(None, 1)
              name = parts[0][1:]
              description = parts[1][:-1] if len(parts) == 2 else '-'
            if name in identifiers and description in identifiers[name]:
              name = _SafeReadName(name, description)
              if name in seen:
                continue
              seen.add(name)
              output_handle.write('>%s\n' % name)
              seq = True
          else:
            if seq:
              output_handle.write(l)
    os.chmod(seqs_file, 0774)
    read_files.append(seqs_file)

    # Retrieves subsequences matching to the HMM that will be used to build
    # the final MSA and tree.
    run_process(['esl-reformat', '-o', converted_msa_file, 'fasta',
                 msa_file])
    hit_file = _MakeTemp(temp_files)
    hit_count = 0
    seen = set()
    with open(converted_msa_file) as input_handle:
      with open(hit_file, 'w') as output_handle:
        ignore = False
        for l in input_handle:
          if l.startswith('>'):
            ignore = False
            parts = l.split(' [subseq from] ')
            part1 = parts[0][1:].lstrip()
            part2 = parts[1][:-1]
            coords = tuple(part1[part1.rindex('/')+1:].split('-'))
            name = part1[:part1.rindex('/')]
            if '|' in name and name[:name.index('|')].isdigit():
              name = name[name.index('|')+1:]
            description = '-' if name == part2 else part2
            try:
              unique_index = identifiers[name][description][coords]
            except KeyError:
              ignore = True
              continue
            name = _SafeReadName(name, description, unique_index, coords)
            if name in seen:
              ignore = True
              continue
            seen.add(name)
            if name in hmm_evalues:
              final_hmm_evalues[name] = hmm_evalues[name]
            output_handle.write('>%s\n' % name)
            hit_count += 1
          elif not ignore:
            output_handle.write(l)
    hmm_hit_evalues.append(final_hmm_evalues)
    hmm_hit_files.append(hit_file)
    cell['reads_file'] = os.path.basename(seqs_file)
    cell['sequences_hit'] = hit_count
  return (read_files, hmm_hit_files, safe_orf_names, hmm_hit_evalues)

def UseReferenceHits(reference_msa, temp_files):
  refseq_seqs_file = _MakeTemp(temp_files)
  refseq_ids = set() # Temp set of gis for gi:taxid dictionary.
  with open(reference_msa) as f:
    with open(refseq_seqs_file, 'w') as out_file:
      for l in f:
        if l.startswith('>'):
          seq_name = l[1:].strip().split(None, 1)[0]
          gi_num = seq_name.split('|', 2)[1]
          refseq_ids.add(gi_num)
          out_file.write('>%s\n' % seq_name)
        else:
          out_file.write('%s\n' % ''.join([c for c in l if c.isupper()]))

  # Build gi_taxid_dictionary.
  gi_taxid_dictionary = {}
  with open('data/gi_taxid_prot.dmp') as prot_dmp_handle:
    for line in prot_dmp_handle:
      parts = line.split()
      if parts[0] in refseq_ids:
        gi_taxid_dictionary[parts[0]] = int(parts[1])
  # Stop prematurealy if none of the refseq gis have taxonomy info.
  if len(gi_taxid_dictionary) == 0:
    return (None, set(), {})

  # Filter refseq genes without taxid.
  filtered_refseq_seqs_file = _MakeTemp(temp_files)
  refseq_hit_ids = set()
  with open(refseq_seqs_file) as in_file:
    with open(filtered_refseq_seqs_file, 'w') as out_file:
      ignore = False
      for l in in_file:
        if l.startswith('>'):
          seq_buffer = []
          ignore = False
          gi_num = l.split('|', 2)[1]
          if gi_num not in gi_taxid_dictionary:
            ignore = True
            continue
          seq_name = l[1:].strip()
          refseq_hit_ids.add(seq_name)
          out_file.write(l)
        elif not ignore:
          out_file.write(l)
  return (filtered_refseq_seqs_file, refseq_hit_ids, gi_taxid_dictionary)

def FindRefseqHits(hmm_evalue, filter_multi, hmm_file, temp_files, task, meta):
  refseq_msa_file = _MakeTemp(temp_files)
  domtblout = _MakeTemp(temp_files)
  converted_refseq_msa_file = _MakeTemp(temp_files)
  run_process(['hmmsearch', '-o', '/dev/null', '-A', refseq_msa_file,
               '-E' if filter_multi else '--domE', str(hmm_evalue),
               '--domtblout', domtblout, '--cpu', CONCURRENCY, hmm_file,
               'data/Refseq.fa'], task=task, meta=meta)
  # Stop prematurealy if no refseq hits.
  if os.stat(refseq_msa_file).st_size == 0:
    return (None, set(), {})
  run_process(['esl-reformat', '-o', converted_refseq_msa_file, 'fasta',
               refseq_msa_file])
  significant = set()
  sequences_hit = {}
  # Parses the domtblout output to find sequences that made the independent
  # cut-off.
  with open(domtblout) as f:
    line1 = f.readline()
    line2 = f.readline()
    name_end = line2.index('accession')
    coords_start = line1.index('hmm coord') + 9
    coords_end = line1.index('ali coord') + 9
    if filter_multi:
      eval_start = line2.index('qlen') + 4
      eval_end = line2.index('E-value') + 7
    else:
      eval_start = line2.index('c-Evalue') + 8
      eval_end = line2.index('i-Evalue') + 8
    for line in f:
      if line.startswith('#'):
        continue
      evalue = line[eval_start:eval_end].strip()
      if float(evalue) > hmm_evalue:
        continue
      coords = tuple(line[coords_start:coords_end].strip().split())
      name = line[:name_end].strip()
      coords_name = '%s/%s-%s' % ((name,) + coords)
      if filter_multi and name in sequences_hit:
        existing = sequences_hit[name]
        if existing in significant:
          significant.remove(existing)
        continue
      elif filter_multi:
        sequences_hit[name] = coords_name
      significant.add(coords_name)

  # Parses MSA file, filtering out sequences that did not meet the cut-off or
  # were multi hits.
  refseq_seqs_file = _MakeTemp(temp_files)
  refseq_ids = set() # Temp set of gis for gi:taxid dictionary.
  ignore = False
  with open(converted_refseq_msa_file) as in_file:
    with open(refseq_seqs_file, 'w') as out_file:
      for l in in_file:
        if l.startswith('>'):
          ignore = False
          seq_name = l[1:].strip().split(None, 1)[0]
          if seq_name not in significant:
            ignore = True
            continue
          gi_num = seq_name.split('|', 2)[1]
          refseq_ids.add(gi_num)
          out_file.write('>%s\n' % seq_name)
        elif not ignore:
          out_file.write(l)

  # Build gi_taxid_dictionary.
  gi_taxid_dictionary = {}
  with open('data/gi_taxid_prot.dmp') as prot_dmp_handle:
    for line in prot_dmp_handle:
      parts = line.split()
      if parts[0] in refseq_ids:
        gi_taxid_dictionary[parts[0]] = int(parts[1])
  # Stop prematurealy if none of the refseq gis have taxonomy info.
  if len(gi_taxid_dictionary) == 0:
    return (None, set(), {})

  # Filter refseq genes without taxid.
  filtered_refseq_seqs_file = _MakeTemp(temp_files)
  refseq_hit_ids = set()
  with open(refseq_seqs_file) as in_file:
    with open(filtered_refseq_seqs_file, 'w') as out_file:
      ignore = False
      for l in in_file:
        if l.startswith('>'):
          seq_buffer = []
          ignore = False
          gi_num = l.split('|', 2)[1]
          if gi_num not in gi_taxid_dictionary:
            ignore = True
            continue
          seq_name = l[1:].strip()
          refseq_hit_ids.add(seq_name)
          out_file.write(l)
        elif not ignore:
          out_file.write(l)
  return (filtered_refseq_seqs_file, refseq_hit_ids, gi_taxid_dictionary)

def MakeOutputFile(parts, extension=''):
  fd, output_file = tempfile.mkstemp(
      dir=OUTPUT_DIR,
      prefix = '%s_' % '_'.join(parts),
      suffix='%s%s' % (str(int(random.random()*1000000000)), extension))
  os.close(fd)
  os.chmod(output_file, 0774)
  return output_file

# Cleans up old files in input or output directories.
MAX_INPUT_HOURS = 5
MAX_OUTPUT_HOURS = 24 * 31
def CleanUp():
  allowed_input_time = time.time() - MAX_INPUT_HOURS * 3600
  for f in os.listdir('input'):
    full = os.path.join('input', f)
    if not f.startswith('.') and os.path.getmtime(full) <= allowed_input_time:
      try:
        os.remove(full)
      except OSError:
        pass

  allowed_output_time = time.time() - MAX_OUTPUT_HOURS * 3600
  for f in os.listdir(OUTPUT_DIR):
    if f.startswith('_sample_'):
      continue
    full = os.path.join(OUTPUT_DIR, f)
    if not f.startswith('.') and os.path.getmtime(full) <= allowed_output_time:
      try:
        os.remove(full)
      except OSError:
        pass

  conn = sqlite3.connect('databases/results.db')
  cursor = conn.cursor()
  cursor.execute('DELETE FROM results WHERE created <= date(\'now\','
                 '\'-%d hour\') AND protected != 1' % MAX_OUTPUT_HOURS)
  conn.commit()
  conn.close()

def _CombineAnnotationFiles(annotation_files, output_file):
  with open(output_file, 'w') as f:
    first_file = True
    for annotations_file in annotation_files:
      with open(os.path.join(OUTPUT_DIR, annotations_file)) as input_handle:
        first_line = True
        for l in input_handle:
          if first_line and not first_file:
            first_line = False
            continue
          f.write(l)
          first_line = False
      first_file = False

def _CombineReadFiles(read_files, output_file):
  seen = set()
  with open(output_file, 'w') as f:
    for reads_file in read_files:
      with open(os.path.join(OUTPUT_DIR, reads_file)) as input_handle:
        ignore = False
        for l in input_handle:
          if l.startswith('>'):
            ignore = l in seen
            seen.add(l)
          if not ignore:
            f.write(l)

@app.task(bind=True)
def RunPipeline(self, orf_files, hmm_files, hmm_evalue, refseq_hmm_evalue,
                usearch_percent_id, do_sequence_classification,
                do_phylogenetic_classification, force_msa, filter_multi_orf,
                filter_multi_refseq, transeq, min_coverage, min_alignment,
                reference_msa, reference_tree, reference_log):
  return RunPipelineReal(
      self, RunPipeline.request.id, orf_files, hmm_files,
      hmm_evalue, refseq_hmm_evalue, usearch_percent_id,
      do_sequence_classification, do_phylogenetic_classification,
      force_msa, filter_multi_orf, filter_multi_refseq, transeq,
      min_coverage, min_alignment, reference_msa, reference_tree,
      reference_log)

def RunPipelineReal(instance, task_id, orf_files, hmm_files, hmm_evalue,
                    refseq_hmm_evalue, usearch_percent_id,
                    do_sequence_classification, do_phylogenetic_classification,
                    force_msa, filter_multi_orf, filter_multi_refseq, transeq,
                    min_coverage, min_alignment, reference_msa, reference_tree,
                    reference_log):
  global CONCURRENCY
  if not CONCURRENCY_SPECIFIED:
    with open('concurrency.txt') as f:
      for l in f:
        CONCURRENCY = l.strip()
        break
  if instance:
    CleanUp()
  # Strange bug: Server hand if this import is at the top of the file. There is
  # likely a cyclic reference problem that is hard to reproduce.
  import ete2
  output = {'columns': {}, 'column_order': []}
  lineage_files = {}
  parameters = [('Number of metagenome files', len(orf_files)),
                ('Number of HMM models', len(hmm_files)),
                ('Always compute MSA', force_msa),
                ('metagenome HMM E-value', hmm_evalue),
                ('RefSeq HMM E-value', refseq_hmm_evalue),
                ('usearch %id', usearch_percent_id),
                ('Minimum HMM coverage for Refseq Hits', min_coverage),
                ('Minimum HMM alignment length for metagenome hits',
                 min_alignment)];
  if filter_multi_orf:
    parameters.append(('ORF reads with multiple HMM hits are filtered out',''));
  if filter_multi_refseq:
    parameters.append(('Refseq reads with multiple HMM hits are filtered out',
                       ''));
  if transeq:
    parameters.append(('DNA input, translated using EMBOSS transeq', ''));
  if reference_msa:
    parameters.append(('Reference MSA+Tree+Log re-used from previous analysis',
                       ''));
  if not do_phylogenetic_classification:
    parameters.append(('usearch-only analysis', ''))
  elif not do_sequence_classification:
    parameters.append(('phylogenetic-only analysis', ''))

  meta = {'sub-analyses':len(hmm_files), 'states':{}, 'parameters':parameters}
  temp_files = []
  analysis_index = 0
  # Unique IDS for reads in uploaded files.
  new_orf_files = []
  for orfs_name, orfs_path in orf_files:
    unique_upload_id = 0
    if orfs_path.startswith('realinput'):
      new_orfs_path = _MakeTemp(temp_files)
      with open(orfs_path) as input_handle:
        with open(new_orfs_path, 'w') as output_handle:
          for l in input_handle:
            if l.startswith('>'):
              l = l[1:].strip()
              output_handle.write('>up_%d_%s\n' % (unique_upload_id, l))
              unique_upload_id += 1
            else:
              output_handle.write(l)
      os.remove(orfs_path)
      orfs_path = new_orfs_path
    new_orf_files.append((orfs_name, orfs_path))
  orf_files = new_orf_files

  # Transeq DNA to protein.
  if transeq:
    meta['states']['TRANSEQ'] = True
    if instance:
      instance.update_state(meta=meta)
    else:
      print >> sys.stderr, 'Running Transeq.'
    new_orf_files = []
    for orfs_name, orfs_path in orf_files:
      new_orfs_path = _MakeTemp(temp_files)
      run_process(['transeq', '-frame', '6', '-sequence', orfs_path,
                   '-outseq', new_orfs_path])
      new_orf_files.append((orfs_name, new_orfs_path))
    orf_files = new_orf_files

  # For each HMM for each ORF.
  for hmm_index, (hmm_file_name, hmm_file) in enumerate(hmm_files):
    meta['states'] = {}
    if transeq:
      meta['states']['TRANSEQ'] = True
    analysis_index += 1
    meta['analysis'] = analysis_index

    hmm_family_safe, hmm_description, hmm_length = _GetHMMInfo(
      hmm_index, hmm_file, hmm_file_name, temp_files)
    meta['hmm'] = hmm_family_safe
    min_length = int(min_coverage * hmm_length)
    
    column = {'description': hmm_description, 'rows': []}
    output['columns'][hmm_family_safe] = column
    output['column_order'].append(hmm_family_safe)
    lineage_files[hmm_family_safe] = [None] * len(orf_files)

    # Runs hmmsearch on orf files.
    meta['states']['HMMSEARCH1'] = True
    if instance:
      instance.update_state(meta=meta)
    else:
      print >> sys.stderr, 'Running hmmsearch on provided sequences.'
    (read_files,hmm_hit_files, safe_orf_names, hmm_hit_evalues) = FindOrfHits(
       orf_files, hmm_evalue, min_alignment, filter_multi_orf, hmm_file,
       hmm_family_safe, temp_files, column, instance, meta)
    meta['total_orfs'] = sum(len(evals) for evals in hmm_hit_evalues)
    if meta['total_orfs'] == 0:
      if not instance:
        print >> sys.stderr, 'No ORF hits to HMM.'
      continue

    if 'rows' not in output:
      rows = []
      output['rows'] = rows
      for orf_file_tuple, safe_orf_name in zip(orf_files, safe_orf_names):
        total_count = 0
        with open(orf_file_tuple[1]) as f:
          for l in f:
            if l.startswith('>'):
              total_count += 1
        rows.append({'total_sequences':total_count, 'name':safe_orf_name})

    if reference_msa:
      (refseq_seqs_file, refseq_hit_ids, gi_taxid_dictionary) = UseReferenceHits(
        reference_msa, temp_files)
    else:
      # Runs hmmsearch on refseq.
      meta['states']['HMMSEARCH2'] = True
      if instance:
        instance.update_state(meta=meta)
      else:
        print >> sys.stderr, 'Running hmmsearch on Reference database.'
      (refseq_seqs_file, refseq_hit_ids, gi_taxid_dictionary) = FindRefseqHits(
        refseq_hmm_evalue, filter_multi_refseq, hmm_file, temp_files, instance,
        meta)
    column['total_reference_sequences'] = len(refseq_hit_ids)
    meta['total_refs'] = len(refseq_hit_ids)
    if len(refseq_hit_ids) == 0:
      continue

    # Combines matching ORF and refseq sequence files.
    combined_orfs_file = _MakeTemp(temp_files)
    run_process(['cat'] + [hf for hf in hmm_hit_files if hf],
                stdout_file=combined_orfs_file)
    combined_reads_file = _MakeTemp(temp_files)
    run_process(['cat'] + read_files, stdout_file=combined_reads_file)
    combined_seqs_file = _MakeTemp(temp_files)
    run_process(['cat', refseq_seqs_file, combined_orfs_file],
                stdout_file=combined_seqs_file)

    refseq_ids_file = _MakeTemp(temp_files)
    already_added = set()
    with open(refseq_ids_file, 'w') as output_file:
      for refseq_hit_id in refseq_hit_ids:
        refseq_hit_id = refseq_hit_id[:refseq_hit_id.rindex('/')]
        if refseq_hit_id not in already_added:
          output_file.write('%s\n' % refseq_hit_id)
          already_added.add(refseq_hit_id)

    full_refseqs_file = _MakeTemp(temp_files)
    run_process(['esl-sfetch', '-o', full_refseqs_file, '-f',
                 'data/Refseq.fa', refseq_ids_file])

    fixed_refseqs_file_full = _MakeTemp(temp_files)
    with open(full_refseqs_file) as input_file:
      with open(fixed_refseqs_file_full, 'w') as output_file:
        for l in input_file:
          if l.startswith('>'):
            l = '%s\n' % l.strip().split(None,1)[0]
          output_file.write(l)

    if do_sequence_classification:
      meta['states']['USEARCH'] = True
      if instance:
        instance.update_state(meta=meta)
      else:
        print >> sys.stderr, 'Running USEARCH'

      # USEARCH for closest neighbours. 
      closest_neighbours = {}
      if meta['total_orfs'] > 0:
        blast_output = _MakeTemp(temp_files)
        run_process(['usearch', '-usearch_global', combined_reads_file, '-db',
                     fixed_refseqs_file_full, '-id', str(usearch_percent_id),
                     '-blast6out', blast_output], task=instance, meta=meta)
        with open(blast_output) as f:
          for l in f:
            parts = l.split('\t')
            query = parts[0]
            target = parts[1]
            percent_id = parts[2]
            if query in closest_neighbours:
              present_tuple = closest_neighbours[query]
              if float(percent_id) < float(present_tuple[1]):
                continue
            closest_neighbours[query] = (target, percent_id)

    if do_phylogenetic_classification or force_msa:
      # Runs hmmalign on matching sequences.
      meta['states']['HMMALIGN'] = True
      if instance:
        instance.update_state(meta=meta)
      else:
        print >> sys.stderr, 'Running hmmalign.'
      alignment_file = _MakeTemp(temp_files)
      run_process(['hmmalign', '-o', alignment_file, hmm_file,
                   combined_seqs_file], task=instance, meta=meta)
      # Converts to FASTA format.
      converted_alignment_file = _MakeTemp(temp_files)
      run_process(['esl-reformat', '-o', converted_alignment_file, 'afa',
                   alignment_file])
      # Removes remaining non-match states (ie. replace lower case letters).
      # Also filters out short refseq sequences.
      fixed_alignment_file = MakeOutputFile([hmm_family_safe, 'msa'],
                                            extension='.fa')
      column['msa'] = os.path.basename(fixed_alignment_file)
      total_refseqs = 0
      with open(converted_alignment_file) as input_handle:
        with open(fixed_alignment_file, 'w') as output_handle:
          current_name = None
          current_length = 0
          output_buffer = []
          for l in input_handle:
            if l.startswith('>'):
              if current_name is not None:
                if (current_name.startswith('gi|') and
                    current_length >= min_length):
                  output_handle.write(''.join(output_buffer))
                  total_refseqs += 1
                else:
                  output_handle.write(''.join(output_buffer))
              current_name = l[1:].strip()
              output_buffer = [l]
            else:
              l = re.sub(r'[a-z\.\*]','-', l)
              if current_name and current_name.startswith('gi|'):
                current_length += sum(1 for c in l if c.isupper())
              output_buffer.append(l)
          # Flush remaining sequence.
          if current_name is not None:
            if (current_name.startswith('gi|') and
                current_length >= min_length):
              output_handle.write(''.join(output_buffer))
              total_refseqs += 1
            else:
              output_handle.write(''.join(output_buffer))
      column['total_reference_sequences'] = total_refseqs
      meta['total_refs'] = total_refseqs
      if total_refseqs == 0:
        continue

    if do_phylogenetic_classification:
      if reference_msa:
        refseq_alignment_file = MakeOutputFile([hmm_family_safe, 'refseq',
                                                'msa'], extension='.fa')
        shutil.move(reference_msa, refseq_alignment_file)
        column['refseq_msa'] = os.path.basename(refseq_alignment_file)
        tree_file = MakeOutputFile([hmm_family_safe, 'refseq', 'tree'])
        shutil.move(reference_tree, tree_file)
        column['refseq_tree'] = os.path.basename(tree_file)
        log_file = MakeOutputFile([hmm_family_safe, 'refseq', 'fastree',
                                   'log'])
        shutil.move(reference_log, log_file)
        column['refseq_log'] = os.path.basename(log_file)
      else:
        refseq_alignment_file = MakeOutputFile([hmm_family_safe, 'refseq',
                                                'msa'], extension='.fa')
        column['refseq_msa'] = os.path.basename(refseq_alignment_file)
        with open(fixed_alignment_file) as input_handle:
          with open(refseq_alignment_file, 'w') as output_handle:
            for l in input_handle:
              if l.startswith('>'):
                keep_sequence = False
                if l.startswith('>gi|'):
                  keep_sequence = True
                  output_handle.write(l)
              elif keep_sequence:
                output_handle.write(l)

        # Runs FastTree given the alignment.
        meta['states']['FASTTREE'] = True
        if instance:
          instance.update_state(meta=meta)
        else:
          print >> sys.stderr, 'Running FastTree.'
        os.environ['OMP_NUM_THREADS'] = CONCURRENCY
        tree_file = MakeOutputFile([hmm_family_safe, 'refseq', 'tree'])
        column['refseq_tree'] = os.path.basename(tree_file)
        log_file = MakeOutputFile([hmm_family_safe, 'refseq', 'fastree',
                                   'log'])
        column['refseq_log'] = os.path.basename(log_file)
        args = ['FastTreeMP','-out', tree_file, '-log', log_file, '-mlnni',
                '4']
        if total_refseqs >= 50000:
          args += ['-fastest']
        args += [refseq_alignment_file]
        run_process(args, task=instance, meta=meta)

      if meta['total_orfs'] > 0:
        # Create RefPackage for pplacer.
        package = _MakeTemp(temp_files, make_directory=True)
        package_loc = os.path.join(package, 'refpkg')
        run_process(['taxit', 'create', '-l', 'custom', '-P', package_loc,
                     '--aln-fasta', refseq_alignment_file, '--tree-stats',
                     log_file, '--tree-file', tree_file])

        # Run pplacer.
        placements_file = _MakeTemp(temp_files, extension='.jplace')
        run_process(['pplacer', '-j', CONCURRENCY, '-c', package_loc, '-o',
                     placements_file, '--groups', '10', fixed_alignment_file],
                     task=instance, meta=meta)

        # Run Guppy to add in the placements to the original tree.
        tree_file = MakeOutputFile([hmm_family_safe, 'tree'])
        column['tree'] = os.path.basename(tree_file)
        run_process(['guppy', 'tog', '-o', tree_file, placements_file],
                    task=instance, meta=meta)

    meta['states']['TAXONOMY'] = True
    if instance:
      instance.update_state(meta=meta)
    else:
      print >> sys.stderr, 'Running taxonomic classification.'
    # Loads precomputed taxonomy name and id mappings.
    with open('data/taxonomy.pickle') as f:
      taxonomy_data = pickle.load(f)
      # Taxid (int): name (string)
      name_dictionary = taxonomy_data['names']
      # Taxid (int): lineage (list of ints, rightmost being root)
      parents = taxonomy_data['parents']
      # Taxid (int): rank (string)
      ranks = taxonomy_data['ranks']

    if do_phylogenetic_classification:
      # Re-root tree at midpoint.
      sys.setrecursionlimit(30000)
      tree = ete2.Tree(tree_file)
      outgroup = tree.get_midpoint_outgroup()
      tree.set_outgroup(outgroup)
      tree.write(outfile=tree_file)
      # Reads tree and determines closest refseq hit to each orf.
      tree = ete2.Tree(tree_file)
      # Determines the phylogentic consistency at each internal node.
      UpdateTreeWithPhyloConsistency(tree, gi_taxid_dictionary, ranks,
                                     parents)

    # Prepares an output list of each ORF and matching target.
    orf_file_index = -1
    for orfs_name_safe, hmm_evalues in zip(safe_orf_names, hmm_hit_evalues):
      orf_file_index += 1
      cell = column['rows'][orf_file_index]
      if len(hmm_evalues) == 0:
        continue
      output_file = MakeOutputFile(
        [hmm_family_safe, orfs_name_safe, 'annotations'])
      cell['annotations'] = os.path.basename(output_file)
      clade_taxid_counts = Counter()
      clade_representatives = {}
      if do_phylogenetic_classification:
        for l in tree:
          if l.name in hmm_evalues:
            node = l
            while node.up and len(node.phylogeny) == 0:
              node = node.up
            clade_representatives[l.name] = node.phylogeny
      # Writes into output file.
      with open(output_file, "w") as f:
        title_row = ['Dataset', 'HMM Family', 'ORF', 'HMM E-val',
                     'Aligned Length']
        if do_sequence_classification:
          title_row += ['Closest Homolog', '%id of Closest Homolog']
          title_row += ['Closest Homolog %s' % rank.capitalize()
                        for rank in LINEAGE_LEVELS]
        if do_phylogenetic_classification:
          title_row += [col for rank in LINEAGE_LEVELS
                        for col in ('Representative %s' % rank.capitalize(),
                                    '%s Proportion' % rank.capitalize())]
          title_row += ['Best Representative', 'Representative Proportion']
        f.write('\t'.join(title_row))
        f.write('\n')
        orfs_reported = set()
        for orf, e_val in hmm_evalues.iteritems():
          full_orf = _TrimSafeReadName(orf)
          aligned_length = _LengthFromName(orf)
          output_row = [orfs_name_safe, hmm_family_safe, orf, e_val,
                        aligned_length]
          if do_sequence_classification:
            if full_orf in closest_neighbours:
              target, percent_id = closest_neighbours[full_orf]
            else:
              target, percent_id = '', ''
            if target:
              gi_num = target.split("|")[1]
              taxid = gi_taxid_dictionary[gi_num]
              lineage = GetLineageForHomolog(taxid, parents, name_dictionary,
                                             ranks)
              if not do_phylogenetic_classification:
                clade_taxid_counts[taxid] += 1
            else:
              lineage = ['unclassified'] * len(LINEAGE_LEVELS)
              if not do_phylogenetic_classification:
                clade_taxid_counts[None] += 1
            output_row += [target, percent_id] + lineage
          if do_phylogenetic_classification:
            best_rank = None
            best_proportion = None
            best_taxid = None
            last_name = ''
            last_proportion = ''
            # Best phyloigentic rank representatives and proportions.
            phylogeny = clade_representatives[orf]
            for rank in LINEAGE_LEVELS:
              if rank in phylogeny and phylogeny[rank][0] in name_dictionary:
                name = name_dictionary[phylogeny[rank][0]]
                proportion = '%.2f' % phylogeny[rank][1]
                last_name = name
                last_proportion = proportion
                if not best_rank and phylogeny[rank][1] >= 0.8:
                  best_rank = name
                  best_proportion = proportion
                  best_taxid = phylogeny[rank][0]
                output_row += [name, proportion]
              else:
                output_row += [last_name, last_proportion]
            # Recommended representative for clade and proportion.
            if best_rank:
              output_row += [best_rank, best_proportion]
            else:
              output_row += [last_name, last_proportion]
            clade_taxid_counts[best_taxid] += 1
          f.write('\t'.join(output_row))
          f.write('\n')
          orfs_reported.add(full_orf)
        # Creates Krona count files.
        lineage_files[hmm_family_safe][orf_file_index] = (
          _CreateKronaCountFile(temp_files, clade_taxid_counts, parents,
                                name_dictionary))
        # Removes eliminated sequences from raw reads file.
        cell['sequences_hit'] = len(orfs_reported)
        reads_file = os.path.join(OUTPUT_DIR, cell['reads_file'])
        old_reads_file = _MakeTemp(temp_files)
        shutil.move(reads_file, old_reads_file)
        with open(old_reads_file) as input_handle:
          with open(reads_file, 'w') as output_handle:
            ignore = False
            for l in input_handle:
              if l.startswith('>'):
                ignore = False
                orf = l[1:].strip()
                if orf not in orfs_reported:
                  ignore = True
                  continue
                output_handle.write(l)
              elif not ignore:
                output_handle.write(l)
        os.chmod(reads_file, 0774)
        run_process(['esl-sfetch', '--index', reads_file])

    # Create merged krona file accross datasets of current HMM analysis.
    if len(orf_files) > 1:
      _CreateMergedKronaAndAssignLinks(
        'hmm', hmm_family_safe, safe_orf_names, 'all_datasets',
        lineage_files[hmm_family_safe], column['rows'], column, temp_files)

    if do_phylogenetic_classification:
      # Fix tree labels:
      tree = ete2.Tree(tree_file)
      for leaf in tree:
        if leaf.name.startswith('gi|'):
          gi_num = leaf.name.split("|")[1]
          coords = leaf.name.split('/')[-1]
          name = 'gi|%s|%s' % (gi_num, coords)
          if gi_num in gi_taxid_dictionary:
            taxid = gi_taxid_dictionary[gi_num]
            if taxid in name_dictionary:
              tax_name = name_dictionary[taxid]
              tax_name = tax_name.replace(' ', '_')
              tax_name = re.sub(r'[^_\w]+', '', tax_name)
              name = 'gi|%s|%s|%s' % (gi_num, tax_name, coords)
          leaf.name = name
      tree.write(outfile=tree_file)

      # Creates a phyloxml version of the tree.
      phyloxml_tree = '%s.phyloxml' % tree_file
      run_process(['java', '-cp', 'scripts/forester_1034.jar',
                   'org.forester.application.phyloxml_converter', '-f=nn',
                   tree_file, phyloxml_tree])
      if os.path.exists(phyloxml_tree):
        os.chmod(phyloxml_tree, 0774)

    # Concat all annotation files together.
    annotation_files = [cell['annotations'] for cell in column['rows']
                        if 'annotations' in cell]
    if len(annotation_files) > 1:
      combined_output_file = MakeOutputFile([hmm_family_safe,
                                             'all_annotations'])
      _CombineAnnotationFiles(annotation_files, combined_output_file)
      column['all_annotations'] = os.path.basename(combined_output_file)

    # Concat all read files together.
    read_files = [cell['reads_file'] for cell in column['rows']
                  if 'reads_file' in cell]
    if len(read_files) > 1:
      combined_read_file = MakeOutputFile([hmm_family_safe, 'all_reads'])
      _CombineReadFiles(read_files, combined_read_file)
      column['all_reads'] = os.path.basename(combined_read_file)

  if len(hmm_files) > 1:
    lineage_files['*all*'] = [('','')] * len(output['rows'])
    for row_index, row in enumerate(output['rows']):
      # Creates krona file for each row of HMM files accross the dataset.
      counts = [lineage_files[col][row_index]
                for col in output['column_order']]
      cells = [output['columns'][col]['rows'][row_index]
               for col in output['column_order']]
      _CreateMergedKronaAndAssignLinks(
        'dataset', row['name'], output['column_order'], 'all_hmms',
        counts, cells, row, temp_files)
      lineage_files['*all*'][row_index] = counts[-1]
      # Creates combined annotations file for all HMMs for this dataset.
      annotation_files = [
        output['columns'][col]['rows'][row_index]['annotations']
        for col in output['column_order']
        if 'annotations' in output['columns'][col]['rows'][row_index]]
      if len(annotation_files) > 1:
        combined_output_file = MakeOutputFile([row['name'],
                                              'all_annotations'])
        _CombineAnnotationFiles(annotation_files, combined_output_file)
        row['all_annotations'] = os.path.basename(combined_output_file)
      # Creates combined reads file for all HMMs for this dataset.
      read_files = [
        output['columns'][col]['rows'][row_index]['reads_file']
        for col in output['column_order']
        if 'reads_file' in output['columns'][col]['rows'][row_index]]
      if len(read_files) > 1:
        combined_read_file = MakeOutputFile([row['name'], 'all_reads'])
        _CombineReadFiles(read_files, combined_read_file)
        row['all_reads'] = os.path.basename(combined_read_file)

    if len(orf_files) > 1:
      # Creates Krona file for combined HMM counts.
      row_names = [row['name'] for row in output['rows']]
      _CreateMergedKronaAndAssignLinks(
        'hmm', 'all_hmms', row_names, 'all_datasets',
        lineage_files['*all*'], output['rows'], output, temp_files)
      # Creates Krona file for combined dataset counts.
      combined_index = len(output['rows'])
      counts = [lineage_files[col][combined_index]
                if combined_index < len(lineage_files[col]) else ('', '')
                for col in output['column_order']]
      _CreateMergedKronaAndAssignLinks(
        'dataset', 'all_datasets', output['column_order'], 'all_hmms',
        counts,
        [output['columns'][col] for col in output['column_order']], output,
        temp_files)
      # Creates combined annotations file for all HMMs for this dataset.
      annotation_files = [
        output['columns'][col]['all_annotations']
        for col in output['column_order']
        if 'all_annotations' in output['columns'][col]]
      if len(annotation_files) > 1:
        combined_output_file = MakeOutputFile(['all_annotations'])
        _CombineAnnotationFiles(annotation_files, combined_output_file)
        output['all_annotations'] = os.path.basename(combined_output_file)
      # Creates combined reads file for all HMMs for this dataset.
      read_files = [
        output['columns'][col]['all_reads']
        for col in output['column_order']
        if 'all_reads' in output['columns'][col]]
      if len(read_files) > 1:
        combined_read_file = MakeOutputFile(['all_reads'])
        _CombineReadFiles(read_files, combined_read_file)
        output['all_reads'] = os.path.basename(combined_read_file)
  elif len(hmm_files) == 1 and len(orf_files) == 1:
    # Create single krona for single HMM + dataset analysis.
    column_name = output['column_order'][0]
    if lineage_files[column_name][0]:
      krona_file = MakeOutputFile(['krona'])
      krona_file_base = os.path.basename(krona_file)
      count = lineage_files[column_name][0]
      _CreateMergedKronaFile([(column_name, count)], krona_file)
      output['columns'][column_name]['rows'][0]['hmm_krona'] = (
        '%s?collapse=false' % krona_file_base)

  output['phylogenetic_classification'] = do_phylogenetic_classification
  output['sequence_classification'] = do_sequence_classification
  output['parameters'] = parameters
  if task_id >= 0:
    conn = sqlite3.connect('databases/results.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO results VALUES(?, ?, CURRENT_TIMESTAMP, 0)',
                 (task_id, json.dumps(dict(output))))
    conn.commit()
    conn.close()

  # Cleanup if no exceptions occured.
  for temp_file in temp_files:
    if os.path.isfile(temp_file):
      os.remove(temp_file)
    else:
      shutil.rmtree(temp_file)
  for orf_file_name, orf_file in orf_files:
    if orf_file.startswith('realinput'):
      os.remove(orf_file)
  for hmm_file_name, hmm_file in hmm_files:
    if hmm_file.startswith('realinput'):
      os.remove(hmm_file)
  if reference_msa and os.path.isfile(reference_msa):
    os.remove(reference_msa)
  if reference_tree and os.path.isfile(reference_tree):
    os.remove(reference_tree)
  if reference_log and os.path.isfile(reference_log):
    os.remove(reference_log)

  return dict(output)

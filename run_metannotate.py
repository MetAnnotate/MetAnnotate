import os
import sys

import gflags

import tasks

FLAGS = gflags.FLAGS

gflags.DEFINE_list('orf_files',
                   [],
                   'A list of complete path names to the ORF sequence files to '
                   'analyze')
gflags.DEFINE_list('hmm_files',
                   [],
                   'A list of complete path names to the HMM files to use.')
gflags.DEFINE_string('reference_msa',
                     None,
                     'Previously computed reference MSA. If used, all 3 flags '
                     'should be provided: reference_msa, reference_tree, '
                     'reference_log. Providing these will allow you to re-use '
                     'alignment and FastTree files from previous jobs, '
                     'speeding up the current job.')
gflags.DEFINE_string('reference_log',
                     None,
                     'Previously computed FastTree log. If used, all 3 flags '
                     'should be provided: reference_msa, reference_tree, '
                     'reference_log. Providing these will allow you to re-use '
                     'alignment and FastTree files from previous jobs, '
                     'speeding up the current job.')
gflags.DEFINE_string('reference_tree',
                     None,
                     'Previously computed tree. If used, all 3 flags '
                     'should be provided: reference_msa, reference_tree, '
                     'reference_log. Providing these will allow you to re-use '
                     'alignment and FastTree files from previous jobs, '
                     'speeding up the current job.')
gflags.DEFINE_bool('filter_multi_orf',
                   False,
                   'Filter ORFS/reads with multiple HMM hits.')
gflags.DEFINE_bool('filter_multi_refseq',
                   False,
                   'Filter Refseq proteins with multiple HMM hits.')
gflags.DEFINE_bool('do_transeq',
                   False,
                   'DNA input. Run EMBOSS Transeq on provided reads.')
gflags.DEFINE_bool('force_msa',
                   False,
                   'Always compute and provide an MSA of metagenome and '
                   'reference database hits, regardless of the run mode.')
gflags.DEFINE_string('run_mode',
                     'sequence',
                     'Run mode which specifies which approach to take for '
                     'taxonomic classification. Default is \'sequence\', which '
                     'uses a sequence similarity approach (USEARCH). Other '
                     'values include \'phylogenetic\' which uses a '
                     'phylogenetic approach (FastTree & pplacer), and \'both\' '
                     'which shows results for both approaches.')
gflags.DEFINE_float('orfs_hmm_evalue',
                    1e-3,
                    'Metagenome HMM E-value cutoff')
gflags.DEFINE_float('refseq_hmm_evalue',
                    1e-6,
                    'RefSeq HMM E-value cutoff')
gflags.DEFINE_float('usearch_percent_id_cutoff',
                    0.5,
                    '%ID cutoff to use in USEARCH.')
gflags.DEFINE_float('min_refseq_hmm_coverage',
                    0.0,
                    'Minimum HMM coverage for RefSeq hits.')
gflags.DEFINE_integer('min_orfs_hmm_alignment_length',
                      0,
                      'Minimum HMM alignment length for metagenome hits.')
gflags.DEFINE_string('output_dir',
                     None,
                     'Directory to which to write all pipeline output files '
                     'to. Ideally, this should be unique to the current '
                     'analysis being run. If the directory does not exist, an '
                     'attempt will be made to create the directory.')
gflags.DEFINE_string('tmp_dir',
                     '/tmp',
                     'Directory to which to write temporary files during the '
                     'pipeline run. This is useful for debugging in the case '
                     'of a pipeline failure. If the directory does not exist, '
                     'an attempt will be made to create the directory.')

def main(argv):
  try:
    argv = FLAGS(argv)
  except gflags.FlagsError, e:
    print '%s\\nUsage: %s ARGS\\n%s' % (e, sys.argv[0], FLAGS)
    sys.exit(1)

  # Indexes and validates input HMM and orf files.
  hmm_files = [(os.path.splitext(os.path.basename(f))[0], f)
               for f in FLAGS.hmm_files]
  orf_files = [(os.path.splitext(os.path.basename(f))[0], f)
               for f in FLAGS.orf_files]
  print orf_files

  for _, hmm_file in hmm_files:
    if not os.path.isfile(hmm_file):
      print >> sys.stderr, '%s is not a file.' % hmm_file
  hmm_files = [p for p in hmm_files if os.path.isfile(p[1])]

  for _, orf_file in orf_files:
    if not os.path.isfile(orf_file):
      print >> sys.stderr, '%s is not a file' % orf_file
  orf_files = [p for p in orf_files if os.path.isfile(p[1])]

  if not hmm_files:
    print >> sys.stderr, 'No valid HMM files provided. Exiting.'
    sys.exit(1)

  if not orf_files:
    print >> sys.stderr, 'No valid ORF files provided. Exiting.'
    sys.exit(1)

  # Validates reference files.
  reference_msa = FLAGS.reference_msa
  if reference_msa and not os.path.isfile(reference_msa):
    reference_msa = None
    print >> sys.stderr, 'reference_msa path invalid. Ignoring.'
  reference_log = FLAGS.reference_log
  if reference_log and not os.path.isfile(reference_log):
    reference_log = None
    print >> sys.stderr, 'reference_log path invalid. Ignoring.'
  reference_tree = FLAGS.reference_tree
  if reference_tree and not os.path.isfile(reference_tree):
    reference_tree = None
    print >> sys.stderr, 'reference_tree path invalid. Ignoring.'
  if not reference_tree or not reference_log or not reference_msa:
    reference_tree = None
    reference_log = None
    reference_msa = None


  filter_multi_orf = FLAGS.filter_multi_orf
  filter_multi_refseq = FLAGS.filter_multi_refseq
  transeq = FLAGS.do_transeq
  force_msa = FLAGS.force_msa

  
  mode = FLAGS.run_mode
  if mode not in ('sequence', 'phylogenetic', 'both'):
    print >> sys.stderr, 'Given run_mode \'%s\' is invalid. Exiting.' % mode
    sys.exit(1)

  do_sequence_classification = mode in ('sequence', 'both')
  do_phylogenetic_classification = mode in ('phylogenetic', 'both')

  hmm_evalue = abs(FLAGS.orfs_hmm_evalue)
  refseq_hmm_evalue = abs(FLAGS.refseq_hmm_evalue)
  usearch_percent_id = min(abs(FLAGS.usearch_percent_id_cutoff), 1.0)
  min_coverage = min(abs(FLAGS.min_refseq_hmm_coverage), 1.0)
  min_alignment = abs(FLAGS.min_orfs_hmm_alignment_length)

  output = FLAGS.output_dir
  if not output:
    print >> sys.stderr, 'No output_dir given. Exiting.'
    sys.exit(1)
  elif not os.path.isdir(output):
    try:
      os.mkdir(output)
    except:
      print >> sys.stderr, 'Cannot create output dir \'%s\'. Exiting.' % output
      sys.exit(1)

  tmp = FLAGS.tmp_dir
  if not tmp:
    tmp = '/tmp'
  elif not os.path.isdir(tmp):
    try:
      os.mkdir(tmp)
    except:
      print >> sys.stderr, 'Cannot create tmp dir \'%s\'. Exiting.' % tmp
      sys.exit(1)
      
  tasks.OUTPUT_DIR = output
  tasks.TMP_DIR = tmp
  tasks.RunPipelineReal(
      None, -1, orf_files, hmm_files, hmm_evalue, refseq_hmm_evalue,
      usearch_percent_id, do_sequence_classification,
      do_phylogenetic_classification, force_msa, filter_multi_orf,
      filter_multi_refseq, transeq, min_coverage, min_alignment, reference_msa,
      reference_tree, reference_log)

if __name__ == '__main__':
  main(sys.argv)

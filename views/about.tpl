% rebase('base.tpl', js='default')

<h4>What does MetAnnotate do?</h4>
<p>
MetAnnotate is a tool and web application for taxonomic profiling of shotgun metagenomes.
<p>
<p>Here are some of MetAnnotate's features:</p>
<ul>
<li>Taxonomic profiling of metagenomes using protein species markers</li>
<li>Taxonomic profiling of metagenomes using custom proteins</li>
<li>Taxonomic profiling of pathways and GO functions</li>
<li>Comparative analysis of microbial communities</li>
<li>Phylogenetic analysis of metagenomes</li>
<li>Metagenome homology search</li>
</ul>
<br>

<h4>Installation</h4>
<p>
MetAnnotate is designed for Linux systems.
<p>
For full installation instructions, see the MetAnnotate <a href="https://bitbucket.org/pavs/metagenome">bitbucket repository</a>
<p>
<br>

<h4>How do I load my metagenome datasets?</h4>
<p>
The most recommended way to load datasets is to add them to a local directory. The directory location is specified in the <code>metagenome_directories_root.txt</code> and <code>metagenome_directories.txt</code> files.
Because MetAnnotate works with metaproteomics (protein) fasta files, you must convert the nucleotide reads to amino acids using a program like transeq or FragGeneScan (recommended).

<p>
Alternatively, metagenomes can be processed directly within the html interface. Metaproteomes can be loaded as amino acid fasta files, and metagenomes (nucleotide) can be loaded as fasta files which are then converted to open reading frames (protein) using transeq.

<p>
<br>

<h4>Which taxonomic classification approach should I use?</h4>
<p>
We suggest doing a quicker initial analysis using the best-hit (usearch) approach. If there are a significant number of unassigned sequences, we recommend using the phylogenetic (pplacer) approach. Ideally, results from both methods should be compared.
<p>
<br>

<h4>How do I perform community profiling?</h4>
<p>
In step 1 (choose profile HMMs), choose <b>Select Taxonomic Markers</b>. This will load five taxonomic markers from the PhyEco (bacteria + archaea) dataset (<a href="http://www.plosone.org/article/info%3Adoi%2F10.1371%2Fjournal.pone.0077033">Wu et al., 2013</a>)
<p>
<br>

<h4>E-value cutoffs</h4>
<p>
An hmmsearch E-value cutoff of 0.001 is used by default, but this may be raised (e.g., 0.01 or 0.05) to raise sensitivity. This will increase the number of homologs detected in the dataset at the expense of lower accuracy.
<p>
<br>

<h4>Does metannotate work with assembled metagenomes?</h4>
<p>
Currently, no.
<p>
<br>


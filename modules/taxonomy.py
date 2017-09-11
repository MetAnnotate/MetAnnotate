# ======================================================================================================================
# Created by: Metannotate Team (2017)
#
# Description: A module containing taxonomy related functions
# ======================================================================================================================

from modules import tasks


LINEAGE_LEVELS = ('species', 'genus', 'family', 'order', 'class', 'phylum',
                  'superkingdom')


def get_lineage(taxid, parents):
    lineage = []
    current = taxid
    while current != 1 and current in parents:
        lineage.append(current)
        current = parents[current]
    return lineage


def get_lineage_names(taxid, parents, name_dictionary):
    lineage = get_lineage(taxid, parents)
    return [name_dictionary[taxid] for taxid in lineage]


def get_lineage_for_homolog(taxid, parents, name_dictionary, ranks):
    lineage = get_lineage(taxid, parents)
    lineage = {ranks[l]: name_dictionary[l] for l in lineage}
    final_lineage = []
    best = 'unclassified'
    for rank in LINEAGE_LEVELS:
        final_lineage.append(lineage[rank] if rank in lineage else best)
        best = final_lineage[-1]
    return final_lineage


def choose_representatives(node):
    new_phylogeny = {}
    for rank, counts in node.phylogeny.items():
        new_phylogeny[rank] = counts.most_common(1)[0]
    if len(new_phylogeny) == 0:
        node.phylogeny = {}
        return
    max_count = float(max(common[1] for common in new_phylogeny.values()))
    node.phylogeny = {k: (v[0], v[1] / max_count) for k, v in new_phylogeny.items()}


def update_tree_with_phylo_consistency(node, taxid_dictionary, ranks, parents):
    node.phylogeny = tasks.defaultdict(lambda: tasks.Counter())
    if node.is_leaf():
        if node.name and node.name.startswith('gi|'):
            gi_num = node.name.split("|")[1]
            taxid = taxid_dictionary[gi_num]
            lineage = get_lineage(taxid, parents)
            for taxid in lineage:
                rank = ranks[taxid]
                node.phylogeny[rank][taxid] = 1
    else:
        for child in node.children:
            update_tree_with_phylo_consistency(child, taxid_dictionary, ranks, parents)
            for rank, counts in child.phylogeny.iteritems():
                node.phylogeny[rank].update(counts)
            choose_representatives(child)
    if node.is_root():
        choose_representatives(node)
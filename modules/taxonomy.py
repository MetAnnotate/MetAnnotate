#!/usr/bin/env python

"""
Created by: Metannotate Team 2017

Description: Contains functions and code for dealing with taxonomy information.
             Can be called to parse NCBI taxonomy dumps

Requirements: - NCBI nodes.dmp file and names.dmp file are required.
"""

from collections import defaultdict, Counter
import cPickle as pickle
from utils import sanitize_cli_path
import argparse

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
    node.phylogeny = defaultdict(lambda: Counter())
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


# Code for getting precomputed taxonomy information
def get_taxonomy_names_id():
    with open('data/taxonomy.pickle') as f:
        taxonomy_data = pickle.load(f)
        # Taxid (int): name (string)
        name_dictionary = taxonomy_data['names']
        # Taxid (int): lineage (list of ints, rightmost being root)
        parents = taxonomy_data['parents']
        # Taxid (int): rank (string)
        ranks = taxonomy_data['ranks']
        return {"name_dictionary": name_dictionary, "parents": parents, "ranks": ranks}


def parse_taxonomy_names(names_dmp_path):
    """
    Takes an NCBI taxonomy names dump file and parses the scientific names of each taxa_id.
    :param names_dmp_path: The path to the dump file.
    :return: A dictionary containing taxa_id to name mappings.
    """
    names = {}
    with open(names_dmp_path) as taxonomy_names_file:
        for line in taxonomy_names_file:
            if 'scientific name' in line:
                column = line.split('|')
                taxa_id = int(column[0].strip())
                name = column[1].strip()
                names[taxa_id] = name
    return names


def parse_taxa_nodes(nodes_dmp_path):
    """
    Takes an NCBI taxonomy nodes dump file and parses the scientific names of each taxa_id.
    :param nodes_dmp_path: The path to the dump file.
    :return 1: A dictionary containing taxa_id to parent mappings.
    :return 2: A dictionary containing taxa_id to rank mappings.
    """
    parents = {}
    ranks = {}
    with open(nodes_dmp_path) as taxonomy_nodes_file:
        for line in taxonomy_nodes_file:
            column = line.split('|')
            taxa_id = int(column[0].strip())
            parent = int(column[1].strip())
            rank = column[2].strip()
            parents[taxa_id] = parent
            ranks[taxa_id] = rank
    return parents, ranks


def pickle_taxonomy(pickle_path, taxonomy_names_dict, taxonomy_parents_dict, taxonomy_ranks_dict):
    """
    Takes the parsed NCBI taxonomy information and creates a pickle object dump of it.
    :param pickle_path: The path where the pickle file should be written.
    :param taxonomy_names_dict: A dictionary containing taxa_id to name mappings.
    :param taxonomy_parents_dict: A dictionary containing taxa_id to parent mappings.
    :param taxonomy_ranks_dict: A dictionary containing taxa_id to rank mappings.
    """
    with open(pickle_path, 'w') as pickle_file:
        pickle.dump({'names': taxonomy_names_dict, 'parents': taxonomy_parents_dict, 'ranks': taxonomy_ranks_dict},
                    pickle_file)


def main(args):
    """
    When called as a CLI application this script creates parses an NCBI taxonomy dump consisting of a nodes.dmp file
    and names.dmp file and creates a taxonomy pickle consisting of a series of taxa_id indexed dictionaries.
    :param args:
        - names_dmp_file: Path to the nodes dump file.
        - nodes_dmp_file: Path to the names dump file.
    """
    ncbi_taxonomy_names_dmp_path = sanitize_cli_path(args.names_dmp_file)
    ncbi_taxonomy_nodes_dmp_path = sanitize_cli_path(args.nodes_dmp_file)
    pickle_path = sanitize_cli_path(args.output_path)

    names = parse_taxonomy_names(ncbi_taxonomy_names_dmp_path)
    parents, ranks = parse_taxa_nodes(ncbi_taxonomy_nodes_dmp_path)
    pickle_taxonomy(pickle_path, taxonomy_names_dict=names, taxonomy_parents_dict=parents,
                    taxonomy_ranks_dict=ranks)


if __name__ == '__main__':
    cli_title = """Creates a pickle file containing taxonomy information to be used by Metannotate"""

    parser = argparse.ArgumentParser(description=cli_title)
    parser.add_argument('-n', '--names_dmp_file', metavar='FILE', required=True,
                        help='The path to NCBI names.dmp file.')
    parser.add_argument('-x', '--nodes_dmp_file', metavar='FILE', required=True,
                        help='The path to NCBI nodes.dmp file.')
    parser.add_argument('-o', '--output_path', metavar='PATH', required=True,
                        help='The path to where the pickle file should be written.')

    cli_args = parser.parse_args()
    main(cli_args)

#!/usr/bin/env python

"""
Created by: Metannotate Team 2017

Description: Parses taxonomy information from NCBI taxonomy dump files.

Requirements: - NCBI nodes.dmp file and names.dmp file are required.
"""

import argparse
from modules.taxonomy import parse_taxonomy_names, parse_taxa_nodes, pickle_taxonomy
from modules.utils import sanitize_cli_path


def main(args):
    ncbi_taxonomy_names_dmp_path = sanitize_cli_path(args.names_dmp_file)
    ncbi_taxonomy_nodes_dmp_path = sanitize_cli_path(args.nodes_dmp_file)
    pickle_path = sanitize_cli_path(args.output_path)

    names = parse_taxonomy_names(ncbi_taxonomy_names_dmp_path)
    parents, ranks = parse_taxa_nodes(ncbi_taxonomy_nodes_dmp_path)
    pickle_taxonomy(pickle_path, taxonomy_names_dict=names, taxonomy_parents_dict=parents,
                    taxonomy_ranks_dict=ranks)


if __name__ == '__main__':
    cli_title = """Creates a pickle file containing taxonomy information to be used by """

    parser = argparse.ArgumentParser(description=cli_title)
    parser.add_argument('-n', '--names_dmp_file', metavar='FILE', required=True,
                        help='The path to NCBI names.dmp file.')
    parser.add_argument('-x', '--nodes_dmp_file', metavar='FILE', required=True,
                        help='The path to NCBI nodes.dmp file.')
    parser.add_argument('-o', '--output_path', metavar='PATH', required=True,
                        help='The path to where the pickle file should be written.')

    cli_args = parser.parse_args()


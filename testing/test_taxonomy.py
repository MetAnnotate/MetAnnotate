#!/usr/bin/env python

"""
Created by: Metannotate Team (2017)

Description: A simple unittest for testing the taxonomy module
"""

import os
import unittest
from modules.taxonomy import parse_taxonomy_names, parse_taxa_nodes, pickle_taxonomy
from modules.hash import md5hash


class TestTaxonomy(unittest.TestCase):
    """A unit testing class for testing the taxonomy.py module. To be called by nosetests."""

    @classmethod
    def setUpClass(cls):
        """Sets up class for later test cases."""
        cls.test_name_dmp_path = './test_constants/test_names.dmp'
        cls.test_node_dmp_path = './test_constants/test_nodes.dmp'
        cls.test_pickle_path = './test.pickle'
        cls.test_pickle_hash = '7ea175dca95b67c90c0c2bed7190ef0b'

    def test_parse_taxonomy_names(self):
        """Test if there is proper parsing of names from taxa name dumps."""
        names = parse_taxonomy_names(self.test_name_dmp_path)
        self.assertEqual('root', names[1])
        self.assertEqual('Buchnera aphidicola', names[9])
        self.assertEqual('Methylophilus', names[16])

    def test_parse_taxa_ranks(self):
        """Test if there is proper parsing of ranks from taxa node dumps."""
        parents, ranks = parse_taxa_nodes(self.test_node_dmp_path)
        self.assertEqual('no rank', ranks[1])
        self.assertEqual('species', ranks[9])
        self.assertEqual('genus', ranks[16])

    def test_parse_taxa_parents(self):
        """Test if there is proper parsing of parents from taxa node dumps."""
        parents, ranks = parse_taxa_nodes(self.test_node_dmp_path)
        self.assertEqual(1, parents[1])
        self.assertEqual(32199, parents[9])
        self.assertEqual(32011, parents[16])

    def test_pickle_taxonomy(self):
        """Test if the test pickle can be written properly."""
        names = parse_taxonomy_names(self.test_name_dmp_path)
        parents, ranks = parse_taxa_nodes(self.test_node_dmp_path)

        pickle_taxonomy(self.test_pickle_path, taxonomy_names_dict=names, taxonomy_ranks_dict=ranks,
                        taxonomy_parents_dict=parents)
        self.assertTrue(os.path.isfile(self.test_pickle_path))
        md5_hash = md5hash(self.test_pickle_path)
        self.assertEqual(self.test_pickle_hash, md5_hash)

    @classmethod
    def tearDownClass(cls):
        """Remove the pickle file generated during testing."""
        os.remove(cls.test_pickle_path)


if __name__ == '__main__':
    unittest.main()

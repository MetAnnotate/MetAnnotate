import ete2
import sys

tree_file = sys.argv[1]
try:
    ete2.Tree(tree_file)
except ete2.parser.newick.NewickError:
    sys.exit(1)

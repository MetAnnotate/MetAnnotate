import ete2
import os
import sys
import xml.etree.ElementTree as ET
import StringIO


def fix_bad_names(node):
    try:
        float(node.name)
        node.name = ''
        for subnode in node.children:
            fix_bad_names(subnode)
    except ValueError:
        pass

tree_file = sys.argv[1]
node_name = sys.argv[2]
homolog_gi = 'gi|%s|' % sys.argv[3]
project = ete2.Phyloxml()
project.build_from_file(os.path.join('output', '%s.phyloxml' % tree_file))
tree = project.get_phylogeny()[0]
homolog_name = [leaf.name for leaf in tree
                if leaf.name.startswith(homolog_gi)][0]
node = tree.get_common_ancestor(node_name, homolog_name)
root = node

while root and len(root) < 5:
    root = root.up

new_tree = ete2.PhyloxmlTree(phyloxml_clade=root.phyloxml_clade)
new_tree.phyloxml_clade.name = ''

for tree_node in new_tree.children:
    fix_bad_names(tree_node)

new_project = ete2.Phyloxml()
new_project.add_phylogeny(new_tree)
subtree_output = StringIO.StringIO()
new_project.export(subtree_output)

root = ET.fromstring(subtree_output.getvalue())
phylo = root[0]
clade = phylo[0]
phylo.remove(clade)
render = ET.SubElement(phylo, 'ns0:render')
styles = ET.SubElement(render, 'ns0:styles')
orf = ET.SubElement(styles, 'ns0:orf')
orf.attrib = {'fill': '#FF0000', 'font-weight': 'bold'}
homolog = ET.SubElement(styles, 'ns0:homolog')
homolog.attrib = {'fill': '#0000FF', 'font-weight': 'bold'}
gi = ET.SubElement(styles, 'ns0:gi')
gi.attrib = {'fill': '#9999FF', 'font-weight': 'bold'}
phylo.append(clade)

node = [n for n in
        clade.iter('{http://www.phyloxml.org/1.10/phyloxml.xsd}name')
        if n.text == node_name][0]

node.attrib['style'] = 'orf'

refseq_nodes = [n for n in
                clade.iter('{http://www.phyloxml.org/1.10/phyloxml.xsd}name')
                if n.text and n.text.startswith('gi|')]

for node in refseq_nodes:
    node.attrib['style'] = 'gi'

homolog_node = [n for n in
                clade.iter('{http://www.phyloxml.org/1.10/phyloxml.xsd}name')
                if n.text == homolog_name][0]
homolog_node.attrib['style'] = 'homolog'
colored_tree = ET.ElementTree(root)
subtree_output = StringIO.StringIO()
colored_tree.write(subtree_output)

print subtree_output.getvalue()

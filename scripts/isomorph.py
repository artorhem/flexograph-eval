#!/usr/bin/python
import random
from graph_utils import edges, sizeof_graph

def pack_graph(filename):
	'''Packs the graph s.t. there are no 0-vertices.
	Makes no guarantees about the resulting isomorphism;
	therefore, in practice it is not that useful.'''
	iso = dict()
	for src,tar in edges(filename):
		src = iso.setdefault(src,len(iso))
		tar = iso.setdefault(tar,len(iso))
		print(src,tar)

def stable_pack_graph(filename):
	'''Packs the graph s.t. there are no 0-vertices,
	and guarantees that the resulting isomorphism
	sorts in the same order as the original graph.'''
	vertices = set()
	for src,tar in edges(filename):
		vertices.add(src)
		vertices.add(tar)
	seq = sorted(vertices)	
	iso = {seq[new]:new for new in range(len(seq))}

	for src,tar in edges(filename):
		print(iso[src],iso[tar])

def degree_sort_graph(filename, rev=False):
	'''Isomorphs the graph s.t. the vertices are degree-sorted.
	This implicitly packs the graph; it might be more proper
	to put all the 0-vertices at the beginning,
	which is as simple as finding the sizeof_graph(filename).'''
	degree = dict()
	for src,tar in edges(filename):
		degree[src] = degree.setdefault(src,0) + 1
		degree[tar] = degree.setdefault(tar,0) + 1
	seq = sorted(degree, key=degree.get, reverse=rev)
	iso = {seq[new]:new for new in range(len(seq))}

	for src,tar in edges(filename):
		print(iso[src],iso[tar])

def randomize_graph(filename):
    iso = list(range(sizeof_graph(filename)))
    random.seed()
    random.shuffle(iso)

    for src,tar in edges(filename):
        print(iso[src],iso[tar])

def unpack_graph(filename, new_size = None):
	'''PREREQ: sizeof_graph(filename) < new_size
	Unpacks the graph s.t. sizeof_graph(filename) == new_size.
	Furthermore, the isomorphism is guaranteed to be random.
        TODO: This could support sizeof_packed_graph(filename) < new_size'''
	new_size = int(new_size) if new_size != None else sizeof_graph(filename)

	iso = list(range(new_size))
	random.seed()
	random.shuffle(iso)

	for src,tar in edges(filename):
		print(iso[src],iso[tar])
	
def stable_unpack_graph(filename, new_size = None):
	'''PREREQ: filename is packed
	Unpacks the graph s.t. sizeof_graph(filename) == new_size.
	Furthermore, the isomorphism is both guaranteed to be random
	and to sort in the same order as the original graph.
	TODO: This could support unpacked graphs with some alterations.'''
	old_size = sizeof_graph(filename)
	new_size = int(new_size) if new_size != None else old_size

	iso = list(range(new_size))
	random.seed()
	random.shuffle(iso)
	iso = sorted(iso[:old_size])
	# This is statistically sound only for packed graphs.

	for src,tar in edges(filename):
		print(iso[src],iso[tar])

def randomize_weight_graph(filename):
	for src,tar in edges(filename):
		# Generate a random edge weight between [1,10000]
		edge_weight = random.randint(0,10000) + 1
		print(src, tar, edge_weight)

import sys
if __name__ == '__main__':
	command = sys.argv[1]
	if   command == 'pack':		pack_graph(sys.argv[2])
	elif command == 'spack':	stable_pack_graph(sys.argv[2])
	elif command == 'degreesort':	degree_sort_graph(sys.argv[2])
	elif command == 'revdegree':	degree_sort_graph(sys.argv[2], rev=True)
	elif command == 'unpack':	unpack_graph(*sys.argv[2:])
	elif command == 'sunpack':	stable_unpack_graph(*sys.argv[2:])
	elif command == 'random':   randomize_graph(sys.argv[2])
	elif command == 'weighted': randomize_weight_graph(sys.argv[2])
	else: sys.exit(1)

#!/usr/bin/python
import math
import random
import sys

def edges(filename):
	with open(filename) as f:
		for line in f:
			line = line.strip()
			if line[0] == '#': continue
			#check if the split returns 3 values
			if len(line.split()) == 3:
				src,tar,_ = line.split()
			else:
				src,tar = line.split()
			yield(int(src),int(tar))

def sizeof_graph(filename):
	return 1 + max((max(src,tar) for src,tar in edges(filename)))

def graph_info(filename):
	maxv = 0
	minv = float('inf')
	vertices = set()
	edge_count = 0

	print("Processing edges")
	for (src,tar) in edges(filename):
		maxv = max(maxv,src,tar)
		minv = min(minv,src,tar)
		vertices.add(src)
		vertices.add(tar)
		edge_count += 1
		#if edge_count % 100000 == 0:
			#print("Checked %d edges" % edge_count)

	print('MAX_VERTEX=%d' % maxv)
	print('MIN_VERTEX=%d' % minv)
	print('VERTEX_COUNT=%d' % len(vertices))
	print('EDGE_COUNT=%d' % edge_count)
	print('ISOLATED_VERTICES=%d' % (maxv - len(vertices)))
	print('Percentage of Isolated Vertices=%f' % (float(maxv - len(vertices)) / maxv))

	s = int(math.floor(math.log(len(vertices), 2)))
	e = int(round(float(edge_count)/(2**s)))
	print('RMATSMALL_S=%d' % s)
	print('RMATSMALL_E=%d' % e)

	s = int(math.ceil(math.log(len(vertices), 2)))
	e = int(round(float(edge_count)/(2**s)))
	print('RMATBIG_S=%d' % s)
	print('RMATBIG_E=%d' % e)

def isolated_vertices(filename):
	maxv = 0
	vertices = set()
	for src,tar in edges(filename):
		maxv = max(maxv,src,tar)
		vertices.add(src)
		vertices.add(tar)

	print("Zero_Vertices")
	for i in range(maxv):
		if i not in vertices:
			print(i)	

def degrees(filename):
	edge_degrees = dict()
	for src,tar in edges(filename):
		edge_degrees[src] = edge_degrees.setdefault(src,0) + 1
		edge_degrees[tar] = edge_degrees.setdefault(tar,0) + 1

	degrees = dict()
	for k,v in edge_degrees.items():
		degrees[v] = degrees.setdefault(v, 0) + 1

	max_degree = 0
	for k,v in degrees.items():
		if k > max_degree:
			max_degree = k

#	print("Max degree is", k, file=sys.stderr)
	for i in range(max_degree+1):
		if i not in degrees:
#			print(i, file=sys.stderr)
			degrees[i] = 0

	print("Degree,Count")
	for k in sorted(degrees):
		print(k, ",", degrees[k])

def edge_degrees(filename):
    degs = dict()
    max_id = 0
    for src,tar in edges(filename):
        degs[src] = degs.setdefault(src,0) + 1
        degs[tar] = degs.setdefault(tar,0) + 1
        if src > max_id:
            max_id = src
        elif tar > max_id:
            max_id = tar

    for i in range(max_id+1):
        if i not in degs:
            degs[i] = 0

    print("Ids,Degree")
    for k in sorted(degs):
        print(k, ",", degs[k])

def max_deg_vertex(filename):
	degs = dict()
	for src,tar in edges(filename):
		degs[src] = degs.setdefault(src,0) + 1
	max_vertex = -1
	max_value = 0
	for k,v in degs.items():
		if v >= max_value:
			max_value = v
			max_vertex = k
	print("Max out degree vertex is",max_vertex,"with value",max_value) 

def duplicate_edges(filename):
	all_edges = dict()
	num_edges = 0
	for src, tar in edges(filename):
		num_edges += 1
		id = str(src) + "-" + str(tar)
		all_edges[id] = all_edges.setdefault(id,0) + 1

	counter = 0
	for k, v in all_edges.items():
		if v > 1:
			counter += v - 1
			#print(k, " " , v)
	print(counter, num_edges)

def bfs_random_starts(infile, outfile):
	degs = dict()
	for src,tar in edges(infile):
		degs[src] = degs.setdefault(src,0) + 1 #set out degree of src to 0 if it doesn't exist, increment if it does
	max_vertex = -1
	max_value = 0
	for k,v in degs.items():
		if v >= max_value:
			max_value = v
			max_vertex = k
	bfs_random_start_nodes = [0, max_vertex]
	for i in range(1,len(degs)): # Check if there are any zero degree nodes
		if i not in degs:
			print("Zero degree node found", i)
			bfs_random_start_nodes += [i] # Add a zero degree node for representation
			break

	for i in range(20):
		choice = random.choice(list(degs))
		bfs_random_start_nodes += [choice] # Select a random start node from one of the nodes that has at least 1 outgoing edge
	with open(outfile, 'w') as outf:
		for node in bfs_random_start_nodes:
			outf.write(str(node) + "\n")

def get_intersection_count(A, B):
	count = 0
	for a in A:
		if a in B:
			count += 1
	return count

if __name__ == '__main__':
	if len(sys.argv) < 3:
		print("Usage: python graph_utils.py [info|degree|zero|edgedeg|maxver|bfsver|dup_edges] <filename> <optional: bfsver output file>")
		sys.exit(1)
	option = sys.argv[1]
	if option == 'info':
		graph_info(sys.argv[2])
	elif option == 'degree':
		degrees(sys.argv[2])
	elif option == 'zero':
		isolated_vertices(sys.argv[2])
	elif option == 'edgedeg':
		edge_degrees(sys.argv[2])
	elif option == 'maxver':
		max_deg_vertex(sys.argv[2])
	elif option == 'bfsver':
		bfs_random_starts(sys.argv[2], sys.argv[3])
	elif option == 'dup_edges':
		duplicate_edges(sys.argv[2])
	else:
		print("Usage: python graph_utils.py [info|degree|zero|edgedeg|maxver|bfsver|dup_edges] <filename> <optional: bfsver output file>")
		sys.exit(1)


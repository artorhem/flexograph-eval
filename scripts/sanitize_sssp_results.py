import os
import sys

def write_sanitized_file(outfile, lines):
    with open(outfile, 'w+') as outf:
        for line in lines:
            outf.write(line)

def get_sanitized_lines(infile):
    lines = []
    lines += ["Real,User,Sys,Algorithm,Dataset,Iteration,Unvisited\n"]
    with open(infile, 'r+') as inf:
        line_counter = 0
        unvisited_nodes = 0
        for line in inf:
            if line_counter % 2 == 0:
                pieces = line.split(' ')
                unvisited_nodes = int(pieces[0])
            elif line_counter % 2 == 1: 
                new_line = line.strip() + "," + str(unvisited_nodes) + "\n"
                lines += [new_line]
            line_counter += 1
    return lines

def main():
    if len(sys.argv) != 3:
        print("Usage: python sanitize_bfs_results.py <input_file> <output_file>")
        sys.exit(1)

    infile = sys.argv[1]
    outfile = sys.argv[2]
    lines = get_sanitized_lines(infile)
    write_sanitized_file(outfile, lines)

if __name__ == '__main__':
    main()

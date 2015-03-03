'''
    Performs reservoir sampling on a file of arbitrary size (but assumed to be large, or this would be unnecessary), for an arbitrary number of samples, printing the eventual selection to stdout.

'''

from argparse import ArgumentParser
import fileinput
import random

parser = ArgumentParser()
parser.add_argument('files', nargs='*', help='specify input files')
parser.add_argument('n', help='number of lines to sample', type=int)
args = parser.parse_args()

reservoir = []
elements_seen = 0

for line in fileinput.input(args.files):

    elements_seen += 1 

    if elements_seen <= args.n:
        reservoir.append(line.strip())

    else:

        j = random.randint(1, elements_seen)

        if j <= args.n:
            reservoir[j - 1] = line.strip()

for element in reservoir:
    print element

# -*- encoding: utf-8 -*-

'''

    Given a text file containing a set of decks to categorize, compute a hierarchical clustering and display the resulting dendrogram.

'''

import argparse
import numpy as np

#from scipy.spatial.distance import jaccard

parser = argparse.ArgumentParser(description='perform hierarchical clustering on a set of M:tG decks')
parser.add_argument('input', help='input file of decks')
args = parser.parse_args()

def jaccard(seq1, seq2):

    seq1 = set(seq1)
    seq2 = set(seq2)

    return 1 - len(seq1 & seq2) / float(len(seq1 | seq2))

def jaccardify(coord):
    i, j = coord

    # Surely there's a way to do this without
    # relying on ugly global variables?
    return jaccard(decks[i], decks[j])

decks = []

# Read in deck data
for line in open(args.input):
    # Ignore header
    if not line.startswith('i'):
       decks.append(line.strip().split('\t')[1].split('$'))

# Get indices to apply distance to
idx = np.triu_indices(len(decks), 1)

# Annnd calculate those distances!
distance = np.apply_along_axis(jaccardify, 0, idx)

print distance

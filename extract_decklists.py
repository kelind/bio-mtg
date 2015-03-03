#!/home/kelsi/.virtualenvs/mtg/bin/python
# -*- encoding: utf-8 -*-
'''
    Given a metagame to look up (e.g. "THS Block Constructed"), extract all decklists from that metagame and format them in such a way that they can easily be processed for distance metrics in the future.

'''

import sqlite3
import argparse
from collections import defaultdict

parser = argparse.ArgumentParser(description='Extract all decks from a given metagame from a SQLite database.')

parser.add_argument('metagame', help='The name of the metagame to extract, e.g. "THS Block Constructed"')

args = parser.parse_args()

con = sqlite3.connect('mtg.db')
con.row_factory = sqlite3.Row
cursor = con.cursor()

f = open('{}_decks.txt'.format(args.metagame.replace(' ', '_').lower()), 'w')

decks = defaultdict(lambda: {'main': [], 'sideboard': []})

cursor.execute('''select decks.id as id, decklists.card as card, decklists.quantity as quantity, decklists.sideboard as sideboard from tourneys left join decks on tourneys.id = decks.tourney_id left join decklists on decks.id = decklists.deck_id where metagame=?''', (args.metagame,))

for row in cursor.fetchall():
    if row['sideboard']:
        for i in xrange(row['quantity']):
            decks[row['id']]['sideboard'].append('{}{}'.format(row['card'], i))
    else:
        for i in xrange(row['quantity']):
            decks[row['id']]['main'].append('{}{}'.format(row['card'], i))

f.write('id\tmain_deck\tsideboard\n')
for deck in decks:
    f.write('{}\t{}\t{}\n'.format(deck, '$'.join(decks[deck]['main']), '$'.join(decks[deck]['sideboard'])))

f.close()

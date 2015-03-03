'''
    Given deck lists in three-column format (deck ID, card quantity, card ID), reformat into a file with a format that better facilitates clustering (card occurrence vectors).
'''

from collections import defaultdict

card_ids = {line.strip().split('\t')[1]: int(line.split()[0]) for line in open('individual_cards_numbered.txt')}
decks = defaultdict(lambda: [0] * len(card_ids.keys()))

input = open('isd_for_deck_construction.txt')
output = open('isd_formatted_decks.txt', 'w')

for line in input:

    splitline = line.strip().split('\t')

    decks[splitline[0]][int(splitline[2]) - 1] += int(splitline[1])

# Now write out the sorted lists
for deck in decks:

    output.write('{}\t{}\n'.format(deck, '\t'.join(map(str, decks[deck]))))

output.close()

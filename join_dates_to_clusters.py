from collections import defaultdict

group_dict = open('initial_clustering_groups.txt')

# Throw out first line
group_dict.readline()

group_assignments = {line.split()[0].strip('"'): line.strip().split()[1] for line in group_dict}

datedict = defaultdict(lambda: defaultdict(int))
# Now iterate through dates, adding to different clusters as necessary

for line in open('decks_by_date.txt'):

    splitline = line.strip().split()

    if splitline[0] in group_assignments:
        # Deck is in our subset!
        datedict[splitline[1]][group_assignments[splitline[0]]] += 1

# Annnd write back out...
outfile = open('groups_by_date.txt', 'w')

for date in datedict:
    for group in datedict[date]:
        outfile.write('{}\t{}\t{}\t{}\n'.format(date, group, datedict[date][group], sum(map(int, datedict[date].values()))))

outfile.close()

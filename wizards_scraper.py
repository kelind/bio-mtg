#!/home/kelsi/.virtualenvs/mtg/bin/python
# -*- coding: utf-8 -*-
'''
    Scraper for gathering decklist data from Wizards' official MTGO tournament reports.

'''

def extract_bracket_info(tree):
    '''
        Takes the LXML tree of a tournament page and, if it's a "premier" tournament with a recorded bracket, parses out the matchups and game wins/losses for each player.
    '''

    import re
    from collections import OrderedDict

    final_bracket = {}

    # We need to be able to look up seed from player name
    # As well as player name from seed
    final_bracket['participants'] = {}
    inverse_bracket = {}

    # First, get the seeds for all players
    seeds = tree[0].xpath('./tr//td[contains(@class, "seed")]')

    for seed in seeds:
        seednum = seed.xpath('./@class')
        username = seed.xpath('.//text()')
        clean_seed = int(seednum[0][seednum[0].rfind('-') + 1 : ])

        final_bracket['participants'][username[0]] = clean_seed
        inverse_bracket[clean_seed] = username[0]

    # Now, figure out the matchups and their results
    matchups = tree[0].xpath('./tr//td[contains(@class, "winner")]')

    final_bracket['matchups'] = {}

    for match in matchups:
        winner_data = match.xpath('.//text()')[0]

        record = extract_win_loss(winner_data)
        winner = winner_data[ : winner_data.rfind(',')]

        # As far as I'm aware, only the top eight are ever shown in the bracket
        # (please please please don't let this assumption be wrong)
        # We can then handle this case-switch style
        match_pairing = match.xpath('./@class')[0]

        if '1v8' in match_pairing:
            # Who won?
            if final_bracket['participants'][winner] == 1:
                final_bracket['matchups']['1v8'] = [inverse_bracket[1], inverse_bracket[8], int(record[0]), int(record[1])]
            else:
                final_bracket['matchups']['1v8'] = [inverse_bracket[8], inverse_bracket[1], int(record[0]), int(record[1])]

        elif '4v5' in match_pairing:
            if final_bracket['participants'][winner] == 4:
                final_bracket['matchups']['4v5'] = [inverse_bracket[4], inverse_bracket[5], int(record[0]), int(record[1])]
            else:
                final_bracket['matchups']['4v5'] = [inverse_bracket[5], inverse_bracket[4], int(record[0]), int(record[1])]

        elif '3v6' in match_pairing:
            if final_bracket['participants'][winner] == 3:
                final_bracket['matchups']['3v6'] = [inverse_bracket[3], inverse_bracket[6], int(record[0]), int(record[1])]
            else:
                final_bracket['matchups']['3v6'] = [inverse_bracket[6], inverse_bracket[3], int(record[0]), int(record[1])]

        elif '2v7' in match_pairing:
            if final_bracket['participants'][winner] == 2:
                final_bracket['matchups']['2v7'] = [inverse_bracket[2], inverse_bracket[7], int(record[0]), int(record[1])]
            else:
                final_bracket['matchups']['2v7'] = [inverse_bracket[7], inverse_bracket[2], int(record[0]), int(record[1])]

        # Below this point, pairings are AMBIGUOUS
        # due to the order of the code
        elif '8v4' in match_pairing:
            final_bracket['matchups']['18v45'] = [inverse_bracket[final_bracket['participants'][winner]], 0, int(record[0]), int(record[1])]

        elif '7v3' in match_pairing:
            final_bracket['matchups']['27v36'] = [inverse_bracket[final_bracket['participants'][winner]], 0, int(record[0]), int(record[1])]

        elif 'champion' in match_pairing:
            final_bracket['matchups']['champion'] = [inverse_bracket[final_bracket['participants'][winner]], 0, int(record[0]), int(record[1])]

    # Now that we've gone through the whole tree
    # assign the results of ambiguous matchups
    if final_bracket['participants'][final_bracket['matchups']['18v45'][0]] in (1, 8):
        final_bracket['matchups']['18v45'][1] = final_bracket['matchups']['4v5'][0]
    else:
        final_bracket['matchups']['18v45'][1] = final_bracket['matchups']['1v8'][0]

    if final_bracket['participants'][final_bracket['matchups']['27v36'][0]] in (2, 7):
        final_bracket['matchups']['27v36'][1] = final_bracket['matchups']['3v6'][0]
    else:
        final_bracket['matchups']['27v36'][1] = final_bracket['matchups']['2v7'][0]

    if final_bracket['participants'][final_bracket['matchups']['champion'][0]] in (1, 4, 5, 8):
        final_bracket['matchups']['champion'][1] = final_bracket['matchups']['27v36'][0]
    else:
        final_bracket['matchups']['champion'][1] = final_bracket['matchups']['18v45'][0]

    return final_bracket

def extract_event_info(tree):
    '''
        Takes the LXML tree for a MTG Online event and extracts all relevant event info, decklists, etc., and returns it as a dictionary.
    '''

    import re
    import datetime

    event_data = {}

    #winlossre = re.compile(r'\((\d+)-(\d+)\)')
    geninfore = re.compile(r'(?P<format>.+?) (?P<metagame>.+?) #(?P<eventid>\d+) on (?P<date>.+)')

    decks = tree.xpath('id("content-detail-page-of-an-article")//div[@class="deck-group"]')
    
    # Get overall tourney information
    cleaned_byline = decks[0].xpath('span/h5/text()')[0].strip()
    raw_infomatch = geninfore.match(cleaned_byline)

    event_data['format'] = raw_infomatch.group('format')
    event_data['metagame'] = raw_infomatch.group('metagame')
    event_data['eventid'] = int(raw_infomatch.group('eventid'))
    event_data['eventdate'] = datetime.datetime.strptime(raw_infomatch.group('date'), '%m/%d/%Y')

    # If this is a "premier" event, extract bracket info
    #bracket = extract_bracket_info(tree)

    event_data['players'] = {}

    # Now info on individual decks
    for deck in decks:

        # Get pilot and win/loss info
        maininfo = deck.xpath('span/h4/text()')

        username = maininfo[0][ : maininfo[0].rfind('(') - 1]
        event_data['players'][username] = {}

        # To prevent problems with a person who has characters
        # in their name that could set off the regex,
        # find all matches and take the rightmost one
        try:
            wins, losses = extract_win_loss(maininfo[0])

            event_data['players'][username]['wins'] = int(wins)
            event_data['players'][username]['losses'] = int(losses)
        except TypeError:
            # Either this is a tournament with bracket information
            # or one of those weird ones with no w/l info at all.
            # To prevent problems with the latter, initialize
            # win and loss to zero.
            event_data['players'][username]['wins'] = 0
            event_data['players'][username]['losses'] = 0

        # Get maindeck info
        main_cards = deck.xpath('.//div[@class="sorted-by-overview-container sortedContainer"]//span[@class="card-name"]/a/text()')
        main_quantities = deck.xpath('.//div[@class="sorted-by-overview-container sortedContainer"]//span[@class="card-count"]/text()')
        main_deckinfo = [(card, quantity, 0) for card, quantity in zip(main_cards, main_quantities)]

        # Get sideboard
        sideboard_cards = deck.xpath('.//div[@class="sorted-by-sideboard-container  clearfix element"]//span[@class="card-name"]/a/text()')
        sideboard_quantities = deck.xpath('.//div[@class="sorted-by-sideboard-container  clearfix element"]//span[@class="card-count"]/text()')
        sideboard_deckinfo = [(card, quantity, 1) for card, quantity in zip(sideboard_cards, sideboard_quantities)]

        event_data['players'][username]['deck'] = main_deckinfo + sideboard_deckinfo

    # Get player ranking data
    standings = tree.xpath('.//table[@class="sticky-enabled"]/tbody/tr')

    # Get bracket data if present
    bracket = tree.xpath('id("content-detail-page-of-an-article")//div[@class="wiz-bracket"]/table/tbody')

    if bracket:
        event_data['bracket'] = extract_bracket_info(bracket)
        total_rounds = 0

    for entry in standings:
        player = entry.xpath('.//td/text()')

        try:
            if 'bracket' in event_data:
                # Win/loss records are not posted!
                # Determine from standings instead
                # As far as I can tell there's no way to draw
                # so this is fairly straightforward...
                player_points = int(player[2])

                if not total_rounds:
                    # Thankfully, standings are always ordered
                    # so the first place is on top!
                    # Number of rounds = winner's points / 3
                    total_rounds = player_points / 3

                event_data['players'][player[1]]['wins'] = player_points / 3
                event_data['players'][player[1]]['losses'] = total_rounds - player_points / 3

            event_data['players'][player[1]]['rank'] = int(player[0])
            event_data['players'][player[1]]['points'] = int(player[2])
            event_data['players'][player[1]]['omwp'] = float(player[3])
            event_data['players'][player[1]]['gwp'] = float(player[4])
            event_data['players'][player[1]]['ogwp'] = float(player[5])

        except ValueError:
            # I don't remember why this is in here
            continue

        except KeyError:
            if len(standings) != len(event_data['players']):
                # For whatever reason, not all players have decks listed
                # We only want to store data for players where we have decklists
                continue
            else:
                print 'Unrecognized player data in standings'
                break

    return event_data

def extract_win_loss(str):
    '''
        Little function that gets wins and losses out of strings formatted in standard wins-losses fashion. Returns two values: wins, then losses, as ints.
    '''

    import re

    winlossre = re.compile(r'(\d+)-(\d+)')

    # To prevent problems with a person who has characters
    # in their name that could set off the regex,
    # find all matches and take the rightmost one
    winloss = winlossre.findall(str)

    try:
        wins, losses = winloss[-1]
    except IndexError:
        return False

    return wins, losses

if __name__ == '__main__':

    from lxml import etree
    import requests
    from sys import argv

    html_parser = etree.HTMLParser(encoding='UTF-8')

    r = requests.get(argv[1])

    tree = etree.fromstring(r.text, html_parser)

    event_data = extract_event_info(tree)

    print event_data

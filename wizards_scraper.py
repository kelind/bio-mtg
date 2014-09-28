#!/home/kelsi/.virtualenvs/mtg/bin/python
# -*- coding: utf-8 -*-
'''
    Scraper for gathering decklist data from Wizards' official MTGO tournament reports.

'''

def determine_sideboard(quantities, sideboard, sideboard_total):
    '''
        Figures out which cards are in the sideboard rather than the main deck. Takes a list of sideboard indicators and marks a "1" on each card slot that belongs on the sideboard, then returns the newly marked list.
    '''

    card_total = 0

    for index, count in enumerate(reversed(quantities)):
        sideboard[index] = 1
        card_total += count

        if card_total == sideboard_total:
            break
        elif card_total > sideboard_total:
            print card_total, sideboard_total
            print quantities
            print 'Error: sideboard number incorrect.'
            break
        
    return reversed(sideboard)

def extract_bracket_info(tree):
    '''
        Takes the LXML tree of a tournament page and, if it's a "premier" tournament with a recorded bracket, parses out the matchups and game wins/losses for each player.
    '''

    import re
    from collections import OrderedDict

    seeds = [node.tag for node in tree.xpath('id("content")//td[@class="small"]/*')]
    records = tree.xpath('id("content")//td[@class="small"]/*[1]/text()')

    bracket = zip(seeds, records)

    final_bracket = {}

    # Now undergo the heinous process of untangling this mess
    for tag, data in bracket:
        if 'seed' in tag:
            # New user to add to the dict
            final_bracket[data] = {'seed': int(tag[-1]), 'wins': []}
        else:
            # It's matchup data!
            if tag[-2] == 'v':
                # This is a simple semifinal match
                player1 = int(tag[-3])
                player2 = int(tag[-1])

                # Extract win/loss info
                wins, losses = extract_win_loss(data)

                # Get the username by chopping off win/loss stuff
                username = data[:data.rfind(',')]

                # Now just add the win data to the appropriate player
                final_bracket[username]['wins'].append((player2, int(wins), int(losses)))

            if tag[-3] == 'v':
                # Quarterfinal match, harder to parse...
                match1 = [int(tag[-5]), int(tag[-4])]
                match2 = [int(tag[-2]), int(tag[-1])]

                # Extract win/loss info
                wins, losses = extract_win_loss(data)

                # Get the username by chopping off win/loss stuff
                username = data[:data.rfind(',')]

                # Now, what seed is this username?
                if final_bracket[username]['seed'] in match1:
                    final_bracket[username]['wins'].append((match2, int(wins), int(losses)))
                else:
                    final_bracket[username]['wins'].append((match1, int(wins), int(losses)))

            if tag == 'champion':
                # Okay, it's the "champion" tag
                # Extract win/loss info
                wins, losses = extract_win_loss(data)

                # Get the username by chopping off win/loss stuff
                username = data[:data.rfind(',')]

                final_bracket[username]['wins'].append(('champion', int(wins), int(losses)))

    # Now, finally, go through and resolve outstanding matchups
    #temp_bracket = {player: (final_bracket[player]['seed'], len(final_bracket[player]['wins'])) for player in final_bracket}
    temp_bracket = {final_bracket[player]['seed']: len(final_bracket[player]['wins']) for player in final_bracket}
    temp_bracket = OrderedDict(sorted(temp_bracket.items(), key=lambda t: t[1]))

    for seed in final_bracket:
        for index, match in enumerate(final_bracket[seed]['wins']):
            if type(match[0]) != type(1):
                if len(match[0]) == 2:
                    # Okay, need to resolve an ambiguous match outcome
                    if temp_bracket[match[0][0]] > temp_bracket[match[0][1]]:
                        final_winner = match[0][0]
                    else:
                        final_winner = match[0][1]
                else:
                    # Okay, we need to determine who the second-place winner was
                    # TODO: Can this cause problems for champions appearing early in the order, destroying data used later?
                    # Don't think so, but...
                    final_winner = temp_bracket.popitem()[0]
                    final_winner = temp_bracket.popitem()[0]

                # Now write over old value with final winner
                final_bracket[seed]['wins'][index] = (final_winner, match[1], match[2])

    return final_bracket

def extract_event_info(tree):
    '''
        Takes the LXML tree for a MTG Online event and extracts all relevant event info, decklists, etc., and returns it as a dictionary.
    '''

    import re

    event_data = {}

    #winlossre = re.compile(r'\((\d+)-(\d+)\)')
    geninfore = re.compile(r'(?P<format>.+?) (?P<metagame>.+?) Event #(?P<eventid>\d+) on (?P<date>.+?) in')


    # Get overall tourney information
    raw_info = tree.xpath('id("centerColumn")//div[@class="body regular"]/p/text()')
    raw_infomatch = geninfore.match(raw_info[0])

    event_data['format'] = raw_infomatch.group('format')
    event_data['metagame'] = raw_infomatch.group('metagame')
    event_data['eventid'] = raw_infomatch.group('eventid')
    event_data['eventdate'] = raw_infomatch.group('date')

    event_data['players'] = {}
    decks = tree.xpath('id("centerColumn")//div[@class="deck"]')

    # If this is a "premier" event, extract bracket info
    #bracket = extract_bracket_info(tree)

    for deck in decks:

        # Get pilot and win/loss info
        maininfo = deck.xpath('.//heading/text()')

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
            # Get bracket info instead
            event_data['bracket'] = extract_bracket_info(tree)

        event_data['players'][username]['deck'] = []

        # Get card content info
        cards = deck.xpath('.//a[@class="nodec"]/text()')

        quantities = deck.xpath('.//table//td[@valign="top"]/text()[normalize-space()]')

        quantities = [int(num.strip()) for num in quantities]

        # Generate a list of sideboard markers
        sideboard = [0] * len(cards)

        # The last X cards are in the sideboard
        totaltext = deck.xpath('.//table//td[@valign="top"]//span[@class="decktotals"]/text()')
        sideboard_text = totaltext[-1]
        sideboard_count = int(sideboard_text.split()[0])

        #print username
        if len(cards) != len(quantities):
            # This may be one of those weird decks
            # Where the sideboard is off by itself...
            # ...in a broken div. =/
            sideboard_check = deck.xpath('.//table//td[@valign="top"]/div/text()[normalize-space()]')
            if len(sideboard_check) + len(quantities) == len(cards):
                # Problem solved!
                quantities = quantities + [int(num.strip()) for num in sideboard_check]
            else:
                print 'Houston, we have a problem...'

        sideboard = determine_sideboard(quantities, sideboard, sideboard_count)

        event_data['players'][username]['deck'] = zip(cards, quantities, sideboard)

    # Get player win/loss and rank data
    standings = tree.xpath('id("centerColumn")//table[@width="90%"]/tr')

    for entry in standings:
        player = entry.xpath('td/text()')

        try:
            event_data['players'][player[1]]['rank'] = int(player[0])
            event_data['players'][player[1]]['points'] = int(player[2])
            event_data['players'][player[1]]['omwp'] = float(player[3])
            event_data['players'][player[1]]['gwp'] = float(player[4])
            event_data['players'][player[1]]['ogwp'] = float(player[5])

        except ValueError:
            continue

        except KeyError:
            if len(standings) != len(event_data['players']):
                # For whatever reason, not all players have decks listed
                continue
            else:
                print 'Houston, we have a problem in the standings area'
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

    html_parser = etree.HTMLParser(encoding='UTF-8')

    #r = requests.get('http://www.wizards.com/Magic/Digital/MagicOnlineTourn.aspx?x=mtg/digital/magiconline/tourn/6683928')
    r = requests.get('http://www.wizards.com/Magic/Digital/MagicOnlineTourn.aspx?x=mtg/digital/magiconline/tourn/6683856')
    #r = requests.get('http://www.wizards.com/Magic/Digital/MagicOnlineTourn.aspx?x=mtg/digital/magiconline/tourn/6800507')

    tree = etree.fromstring(r.text, html_parser)

    event_data = extract_event_info(tree)

    print event_data

    '''
    r = requests.get('http://www.wizards.com/handlers/XMLListService.ashx?dir=mtgo&type=XMLFileInfo&start=7')

    tourney_list = r.json()

    for tourney in tourney_list:

        print tourney['Hyperlink']
    '''

#!/home/kelsi/.virtualenvs/mtg/bin/python
# -*- coding: utf-8 -*-

from bottle import route, run, template, view
from datetime import date

import sqlite3

con = sqlite3.connect('mtg.db')
con.row_factory = sqlite3.Row
cursor = con.cursor()

@route('/hello/<name>')
@view('sample')
def hello(name):
    return dict(name=name)

@route('/index')
@view('index')
def index():
    return dict(date=date.today())

@route('/tournaments/<date>')
@view('tournament_index')
def tournament_index(date):

    import datetime

    pretty_date = datetime.date.fromtimestamp(float(date))
    #pretty_date = pretty_date.strftime('%B %d, %Y')

    cursor.execute('''select * from tourneys where date=?''', (date,))
    return dict(date=pretty_date.strftime('%B %d, %Y'), cursor=cursor)

@route('/events/<eventid>')
@view('event_index')
def event_index(eventid):

    import datetime

    # Get generic tournament info
    cursor.execute('''select * from tourneys where id=?''', (eventid,))
    tourney_info = cursor.fetchone()

    date = datetime.date.fromtimestamp(float(tourney_info['date']))

    # Eventually want to show results, bracket
    # For now, participants and their basic win/losses and deck

    cursor.execute('''select participants.*, users.name, users.id as userid from participants left join users on participants.user_id = users.id where participants.tourney_id=? order by participants.rank''', (eventid,))
    return dict(eventid=eventid, cursor=cursor, date=date.strftime('%d/%m/%y'), info=tourney_info)

@route('/users/<userid>')
@view('user_index')
def user_index(eventid):
    # Want a view of users
    # With links to tourneys played in and decks used

    return dict(eventid=eventid, cursor=cursor, date=date.strftime('%d/%m/%y'), info=tourney_info)

@route('/cards/<cardid>')
@view('card_stats')
def user_index(cardid):
    # Want a view of individual cards
    # Tracking usage over time
    # Want to be able to visualize multiple cards on same graph
    # To compare usage...

    cursor.execute('''select count(*) as decks, sum(quantity) as total from decklists where card=?''', (cardid,))
    stats = cursor.fetchone()

    return dict(cardid=cardid, stats=stats)

# Want a view of decks
# Need to be able to identify decks first!
# Want to be able to see deck usage over time
# Want to be able to compare to other decks over same time period

run(host='localhost', port=8000)
con.close()

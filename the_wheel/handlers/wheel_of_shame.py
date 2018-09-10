import datetime
import json
import random

from mongoengine.queryset.visitor import Q
from mongoengine import Document, DateTimeField, StringField, DictField

from the_wheel.handlers import yahoo

league_keys = {'baseball': 'mlb.l.23144',
               'football': 'nfl.l.116671',
               'hockey': 'nhl.l.34409',
               'basketball': 'nba.l.28664'}

class Spins(Document):
    meta = {'collection': 'spins'}
    date = DateTimeField()
    shame = StringField()
    info = StringField()
    loser = StringField(max_length=30, default='')

class Losers(Document):
    meta = {'collection': 'losers'}
    sport = StringField()
    week_end = DateTimeField()
    loser = StringField()
    scores = DictField()
    punishment = StringField(default='')

class WheelOfShame():
    def __init__(self):
        with open('the_wheel/data/shame.json') as f:
            self.data = json.load(f)

    def chopping_block(self):
        today = datetime.datetime.now().date()
        weeks_loser = Losers.objects(Q(week_end__gte=today)).first()
        last_loser = Losers.objects(Q(week_end__lt=today)).first()

        ret = {'the_loser': ''}
        if weeks_loser:
            ret['next_victim'] = weeks_loser.loser
            ret['the_block'] = weeks_loser.scores
        else:
            ret['next_victim'] = ''
            ret['the_block'] = {}

        if last_loser and last_loser.punishment == '':
            start = last_loser.week_end - datetime.timedelta(days=6)
            last_week = Spins.objects(Q(date__gte=start) & Q(date__lte=last_loser.week_end))
            losers_shame = list(filter(lambda x: x['loser'] == last_loser.loser, last_week))[0]
            last_loser.punishment = "{} {}".format(losers_shame['shame'], losers_shame['info'])
            last_loser.save()
            ret['the_loser'] = "{}: {}".format(last_loser.loser, last_loser.punishment)
        elif last_loser:
            ret['the_loser'] = "{}: {}".format(last_loser.loser, last_loser.punishment)


        return ret

    def check_spins(self):
        output = {}
        # Get the spins for this week and make sure that user hasn't spun already this week...
        today = datetime.datetime.now()
        start = today - datetime.timedelta(days=today.weekday())
        end = start + datetime.timedelta(days=6)

        this_week = Spins.objects(Q(date__gte=start) & Q(date__lte=end))
        for shame in this_week:
            output[shame['loser']] = "{} {}".format(shame['shame'], shame['info'])

        return output

    def update_losers(self, user_override=None):
        # Get the scoreboards for each sport and return a list of scores for each matchup within it
        football, week_start, week_end = yahoo.get_scoreboard(league_keys['football'], user_override)

        week_start = datetime.datetime.strptime(week_start, "%Y-%m-%d")
        week_end = datetime.datetime.strptime(week_end, "%Y-%m-%d")

        loser, scores = self.calculate_loser(football)
        weeks_loser = Losers.objects(week_end=week_end).first()
        if not weeks_loser:
            # We've got a new week! Create the new object and go finalize last weeks
            Losers(sport='football', week_end=week_end, loser=loser, scores=scores).save()
        else:
            weeks_loser.loser = loser
            weeks_loser.scores = scores
            weeks_loser.save()

        return str(weeks_loser)

    def calculate_loser(self, football):
        data = {}
        for match in football:
            data.setdefault(match['team0_name'], 0)
            data[match['team0_name']] += round(match['team0_score'] - match['team1_score'], 2)
            data.setdefault(match['team0_name'] + '_projected', 0)
            data[match['team0_name'] + '_projected'] += round(match['team0_projected'] - match['team1_projected'], 2)
            data.setdefault(match['team1_name'], 0)
            data[match['team1_name']] += round(match['team1_score'] - match['team0_score'], 2)
            data.setdefault(match['team1_name'] + '_projected', 0)
            data[match['team1_name'] + '_projected'] += round(match['team1_projected'] - match['team0_projected'], 2)

        loser = False
        for key in data:
            if 'projected' not in key:
                if not loser:
                    loser = (key, data[key])
                elif data[key] < loser[1]:
                    loser = (key, data[key])

        return (loser[0], data)

    def spin_wheel(self, username):
        # Enumerate out the options, ~10% of them are power rankings
        shames = list(self.data['wheel_of_shame'])
        total_shames = len(shames) + int(len(shames) * .1) + 1

        # Pick a random number
        wheels_will = random.randint(0, total_shames - 1)
        if wheels_will >= len(shames):
            # TODO: We need to check if there is another power ranker this week
            shame_name = "Power Rankings!"
            shame_info = "Your turn to do the power rankings for the week!"
        else:
            shame_name = shames[wheels_will]
            shame_info = self.data['wheel_of_shame'][shames[wheels_will]]
            # Check conditions to see if th  is is a valid pick, if not pick a new number
            if 'start_date' in shame_info:
                # need to check that this one is active
                today = datetime.date.today()
                start = datetime.datetime.strptime(shame_info['start_date'] + ' ' + str(today.year), "%b %d %Y").date()
                end = datetime.datetime.strptime(shame_info['end_date'] + ' ' + str(today.year), "%b %d %Y").date()
                if start <= today <= end:
                    # It's active you can do this one
                    pass
                else:
                    # Pick a new one
                    return self.spin_wheel(username)

            if 'all_others' in shame_info:
                # This is a bit hacky, but oh well
                # Basically T-Rex already rolled this the first time... so from now on show the other option.
                # Would be cleaner to use a database or something but fuck it... we're doing it live
                shame_info = shame_info['all_others']

        # Store the result
        self.store_spin(shame_name, shame_info, username)
        return("{} {}".format(shame_name, shame_info))

    def store_spin(self, shame_name, shame_info, username):
        spin = Spins(date=datetime.datetime.now(),
                     shame=shame_name,
                     info=shame_info,
                     loser=username)

        spin.save()

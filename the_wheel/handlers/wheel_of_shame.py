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

    @staticmethod
    def chopping_block():
        date = datetime.datetime.now().date()

        f_loser = Losers.objects(week_end__gte=date, sport='football').first()
        h_loser = Losers.objects(week_end__gte=date - datetime.timedelta(days=1), sport='hockey').first()
        b_loser = Losers.objects(week_end__gte=date - datetime.timedelta(days=1), sport='basketball').first()
        o_loser = Losers.objects(week_end__gte=date, sport='overall').first()
        last_loser = Losers.objects(week_end__lt=date, sport='overall').order_by('-week_end').first()

        ret = {'the_loser': '',
               'the_block': {},
               'next_victim': ''}
        if o_loser:
            ret['next_victim'] = o_loser.loser if o_loser.scores[o_loser.loser] != 0 else ''
            for key in o_loser.scores:
                ret['the_block'][key] = {'football': f_loser.scores[key] if f_loser is not None else 0,
                                         'hockey': h_loser.scores[key] if h_loser is not None else 0,
                                         'basketball': b_loser.scores[key] if b_loser is not None else 0,
                                         'overall': o_loser.scores[key]}
            print(ret['the_block'])

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

    @staticmethod
    def get_history(week):
        # Week can either be 'last' or a DateTime.date() object
        if week == 'last':
            end = datetime.datetime.now().date()
            start = end  - datetime.timedelta(days=7)
            alt_start = start - datetime.timedelta(days=1)
        else:
            end = week
            start = week - datetime.timedelta(days=1)
            alt_start = start - datetime.timedelta(days=1)

        # Get all the loser objects within that weeks timeframe
        f_loser = Losers.objects(Q(week_end__gte=start) & Q(week_end__lt=end), sport='football').first()
        h_loser = Losers.objects(Q(week_end__gte=alt_start) & Q(week_end__lt=end), sport='hockey').first()
        b_loser = Losers.objects(Q(week_end__gte=alt_start) & Q(week_end__lt=end), sport='basketball').first()
        o_loser = Losers.objects(Q(week_end__gte=start) & Q(week_end__lt=end), sport='overall').first()

        ret = {'the_loser': o_loser.loser,
               'the_block': {},
               'the_punishment': o_loser.punishment}
        for key in o_loser.scores:
            ret['the_block'][key] = {'football': f_loser.scores[key] if f_loser is not None else 0,
                                     'hockey': h_loser.scores[key] if h_loser is not None else 0,
                                     'basketball': b_loser.scores[key] if b_loser is not None else 0,
                                     'overall': o_loser.scores[key]}

        return ret

    @staticmethod
    def get_weeks():
        # Find and return a list of previous weeks that can be looked at from a historical perspective.
        weeks = []
        o_loser = Losers.objects(sport='overall')

        for loser in o_loser:
            if loser.week_end.date() < datetime.datetime.now().date():
                # this week has already ended and is valid for history
                weeks.append(loser.week_end)

        return weeks

    @staticmethod
    def check_spins():
        output = {}
        # Get the spins for this week and make sure that user hasn't spun already this week...
        today = datetime.datetime.now().date()
        adj = today.weekday() if today.weekday() != 0 else 6
        start = today - datetime.timedelta(days=adj)
        end = start + datetime.timedelta(days=6)

        this_week = Spins.objects(Q(date__gte=start) & Q(date__lte=end))
        for shame in this_week:
            output[shame['loser']] = "{} {}".format(shame['shame'], shame['info'])

        return output

    def update_losers(self, user_override=None):
        # Get the scoreboards for each sport and return a list of scores for each matchup within it
        football, f_week_start, f_week_end = yahoo.get_scoreboard(league_keys['football'], user_override)
        hockey, h_week_start, h_week_end = yahoo.get_scoreboard(league_keys['hockey'], user_override)
        basketball, b_week_start, b_week_end = yahoo.get_scoreboard(league_keys['basketball'], user_override)

        dates = {'football': {'week_start': datetime.datetime.strptime(f_week_start, "%Y-%m-%d"),
                              'week_end': datetime.datetime.strptime(f_week_end, "%Y-%m-%d")},
                 'hockey': {'week_start': datetime.datetime.strptime(h_week_start, "%Y-%m-%d"),
                            'week_end': datetime.datetime.strptime(h_week_end, "%Y-%m-%d")},
                 'basketball': {'week_start': datetime.datetime.strptime(b_week_start, '%Y-%m-%d'),
                                'week_end': datetime.datetime.strptime(b_week_end, '%Y-%m-%d')}}

        scores = self.calculate_sports(football, hockey, basketball)
        for key in scores:
            self.record_loser(dates[key]['week_end'], key, scores[key])

        # Now figure out the overall winner taking into consideration the way that weeks end for different sports.
        the_week = Losers.objects(Q(week_end__gt=dates['football']['week_start']) & Q(week_end__lte=dates['football']['week_end']))
        overall = {}
        for loser in the_week:
            if loser.sport != 'overall':
                for key in loser.scores:
                    overall.setdefault(key, 0)
                    overall[key] += loser.scores[key]

        overall = {k: round(v, 2) for k, v in overall.items()}
        overall_loser = min(overall, key=overall.get)

        record = Losers.objects(week_end=dates['football']['week_end'], sport='overall').first()
        if not record:
            Losers(sport='overall', week_end=dates['football']['week_end'], loser=overall_loser, scores=overall).save()
        else:
            record.loser = overall_loser
            record.scores = overall
            record.save()

        return "{} \n {}".format(overall_loser, overall)

    @staticmethod
    def record_loser(week_end, sport, scores):
        loser = Losers.objects(week_end=week_end, sport=sport).first()
        if not loser:
            # We've got a new week! Create the new object and go finalize last weeks
            Losers(sport=sport, week_end=week_end, loser=min(scores, key=scores.get), scores=scores).save()
        else:
            loser.loser = min(scores, key=scores.get)
            loser.scores = scores
            loser.save()

    @staticmethod
    def sum_sport(sport, modifier=1):
        data = {}
        for match in sport:
            data.setdefault(match['team0_name'], 0)
            data[match['team0_name']] += round((match['team0_score'] - match['team1_score']) * modifier, 2)
            # data.setdefault(match['team0_name'] + '_projected', 0)
            # data[match['team0_name'] + '_projected'] += round(match['team0_projected'] - match['team1_projected'], 2)
            data.setdefault(match['team1_name'], 0)
            data[match['team1_name']] += round((match['team1_score'] - match['team0_score']) * modifier, 2)
            # data.setdefault(match['team1_name'] + '_projected', 0)
            # data[match['team1_name'] + '_projected'] += round(match['team1_projected'] - match['team0_projected'], 2)

        return data

    def calculate_sports(self, football, hockey, basketball):
        football = self.sum_sport(football)
        hockey = self.sum_sport(hockey)
        basketball = self.sum_sport(basketball, modifier=.1)

        data = {'football': football,
                'hockey': hockey,
                'basketball': basketball}
        return data

    def spin_wheel(self, username):
        # Enumerate out the options, ~10% of them are power rankings
        shames = list(self.data['wheel_of_shame'])
        total_shames = len(shames) + int(len(shames) * .1) + 1

        # Pick a random number
        wheels_will = random.randint(0, total_shames - 1)
        if wheels_will >= len(shames):
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
        return "{} {}".format(shame_name, shame_info)

    @staticmethod
    def store_spin(shame_name, shame_info, username):
        spin = Spins(date=datetime.datetime.now(),
                     shame=shame_name,
                     info=shame_info,
                     loser=username)

        spin.save()

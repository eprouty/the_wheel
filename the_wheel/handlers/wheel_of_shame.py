import datetime
import json
import random

from mongoengine.queryset.visitor import Q
from mongoengine import Document, DateTimeField, StringField

class Spins(Document):
    meta = {'collection': 'spins'}
    date = DateTimeField()
    shame = StringField()
    info = StringField()
    loser = StringField(max_length=30)

class WheelOfShame():
    def __init__(self, db):
        self.db = db
        with open('the_wheel/data/shame.json') as f:
            self.data = json.load(f)

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

    def spin_wheel(self, username):
        # Get the spins for this week and make sure that user hasn't spun already this week...
        today = datetime.datetime.now()
        start = today - datetime.timedelta(days=today.weekday())
        end = start + datetime.timedelta(days=6)

        this_week = Spins.objects(Q(date__gte=start) & Q(date__lte=end))
        for shame in this_week:
            if username == shame['loser']:
                # This loser has already spun!
                return ""

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
                    return self.spin_wheel()

            if 'first_time' in shame_info:
                shame_info = shame_info['first_time']
            else:
                #TODO Need to change to the second message and check the DB so we actually get here
                pass

        # Store the result
        self.store_spin(shame_name, shame_info, username)
        return("{} {}".format(shame_name, shame_info))

    def store_spin(self, shame_name, shame_info, username):
        spin = Spins(date=datetime.datetime.now(),
                     shame=shame_name,
                     info=shame_info,
                     loser=username)

        spin.save()

import datetime
import json
import random

class WheelOfShame():
    def __init__(self):
        with open('the_wheel/data/shame.json') as f:
            self.data = json.load(f)

    def spin_wheel(self):
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
        return("{} {}".format(shame_name, shame_info))

import pandas

from the_wheel.handlers.wheel_of_shame import Spins

class Stats():
    def spins_stats(self):
        spins_df = pandas.DataFrame(list(Spins.objects()))

        return spins_df.head()

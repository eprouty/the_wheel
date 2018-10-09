import pandas

from the_wheel.handlers.wheel_of_shame import Spins

class Stats():
    def spin_stats(self):
        spins_df = pandas.DataFrame(list(Spins.objects()))

        return spins_df.head()

    def setup_stats(self, app):
        @app.route('/stats/spins')
        def spins_page():
            return self.spin_stats().to_html()

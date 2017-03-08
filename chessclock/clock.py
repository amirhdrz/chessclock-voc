""" clock.py - contains everything related to the clock

Functions associated with the UI:
Pause
Restart
WhiteClicked
BlackCliked
"""
from android.os import SystemClock
from android.os import Handler
# from collections import namedtuple

# delay in milliseconds for time handler
time_task_handler_delay = 20


# Timer = namedtuple('Timer', 'time, delay')

def sub2(t, d, tick):
    diff = d - tick
    if diff < 0:
        return (t + diff, 0)
    else:
        return (t, diff)


class TimeUpdateTask(implements=java.lang.Runnable):

    def __init__(self, clock: 'Clock', handler: Handler):
        self.clock = clock
        self.handler = handler

    def run(self) -> void:
        uptime_millis = SystemClock.uptimeMillis()
        elapsed_millis = uptime_millis - self.clock.start_time_millis
        self.clock.start_time_millis = uptime_millis

        self.handler.postDelayed(self, time_task_handler_delay)
        self.clock.on_tick(elapsed_millis)


class Clock:
    """
    on top of the base clock we also have HourGlass, DelayClock
    """

    def __init__(self, application):
        """
        state: ['active', 'inactive', 'finished']
        """
        self.debug_time = 0

        self._application = application

        self.state = 'inactive'
        self.time_control = None
        self.turn = None  # if inactive: means the player who's turn it is to play
                          # if active: means the player, who is currently playing
                          # if none: means the game has not been started yet
        self.start_time_millis = None
        # self.time_handler = Handler()
        # self.time_update_task = TimeUpdateTask(self, self.time_handler)


    def pause(self):
        self.time_handler.removeCallbacks(self.time_update_task)
        self.clock_status = 'inactive'

    def restart(self):
        # TODO: set timer values to their original
        self.turn = None
        self.time_handler.removeCallbacks(self.time_update_task)
        self.state = 'inactive'

    def _start_timer(self):
        """
        Starts the timer
        """
        self.start_time_millis = SystemClock.uptimeMillis()
        self.time_handler.removeCallbacks(self.time_update_task)
        self.time_handler.postDelayed(self.time_update_task, time_task_handler_delay)

    def on_tick(self, ms):
        """
        callback called every tick
        TODO: should this function handle updating the UI?
        """
        self.debug_time = self.debug_time + ms
        self._application.update_ui()

    def on_black_click(self):
        if self.turn is None:
            self.turn = 'b'

        if self.turn == 'b':
            if self.state == 'inactive':
                self._start_timer()
            elif self.state == 'active':
                # switch the active clock
                self.turn = 'w'

    def on_white_click(self):
        if self.turn is None:
            self.turn = 'w'

        if self.turn == 'w':
            if self.state == 'inactive':
                self._start_timer()
            elif self.state == 'active':
                # switch the players
                self.turn = 'b'


class TimeControl:

    def __init__(self, turn: str, w_timer: Timer, b_timer: Timer):
        # constants
        self.delay = 0
        self.turn = 'w'
        self._w_timer = w_timer
        self.b_timer = b_timer



    def tick(self, ms):
        "clock tick in milliseconds"
        # TODO: define protocol of this function
        if self.turn == 'w':
            self._w_timer = self.ticker(self._w_timer, ms)
        else:
            self._b_timer = self.ticker(self._b_timer, ms)

    def ticker(self, timer, ms) -> Timer:
        """
        Args:
            timer (Timer): timer of the player whose clock is active
            ms (float): tick length in milliseconds
        Returns:
            An updated timer
        """
        pass


# class SuddenDeath(TimeControl):
#
#     def ticker(self, timer: Timer, tick):
#         timer[0] -= tick
#         return timer
#
#
# class SimpleDelay(TimeControl):
#
#     def ticker(self, timer, tick):
#         timer = sub2(timer[0], timer[1], tick)
#         return timer
#
#
# class Bronstein(SimpleDelay):
#     # TODO: only presentation differs
#     pass
#
#
#
# class HourGlass(TimeControl):
#
#     def tick(self, ms):
#         if self.turn == 'w':
#             self.w_timer[0] -= ms
#             self.b_timer[0] += ms
#         else:
#             self.b_timer[0] -= ms
#             self.w_timer[0] += ms

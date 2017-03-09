import android
import android.view
from android.widget import LinearLayout
from android.widget import TextView
from android.widget import Button

from android.os import SystemClock
from android.os import Handler

from android.util import Log

# delay in milliseconds for time handler
TIMER_DELAY = 50


def millis_to_hmsd(ms):
    if ms > 0:
        deci = ms // 100
        s, deci = divmod(deci, 10)
        m, _ = divmod(s, 60)
        h, _ = divmod(m, 60)
        return (h, m, s, deci)
    return (0, 0, 0, 0)


def format_time(ms):
    if ms is not None:
        h, m, s, deci = millis_to_hmsd(ms)
        if h >= 1:
            return "%d:%02d" % (h, m)
        elif m >= 1:
            return "%02d:%02d" % (m, s)
        else:
            return "%02d:%02d:%d" % (m, s, deci)
    else:
        return ""


class TimeUpdateTask(implements=java.lang.Runnable):

    def __init__(self, clock, handler):
        """
        on_tick: function called per tick
        handler: Android os Handler, tied to application's main thread.
        """
        self.clock = clock
        self.handler = handler
        Log.i('TimeUpdateTask', 'initialized')

    def run(self) -> void:
        uptime_millis = SystemClock.uptimeMillis()
        elapsed_millis = uptime_millis - self.clock.start_time_millis
        self.clock.start_time_millis = uptime_millis

        self.handler.postDelayed(self, TIMER_DELAY)
        self.clock._on_handler_tick(elapsed_millis)


class BaseClock:
    """
    on top of the base clock we also have HourGlass, DelayClock
    """

    def __init__(self, application):

        # call for updating ui
        self._application = application

        # possible values of state = ['new', 'active', 'paused', 'finished']
        self.state = 'new'

        self.turn = None

        # time control
        self.time = [None, None]
        self.delay = [None, None]

        # timer task
        self.start_time_millis = None
        self.time_handler = Handler()
        self.time_update_task = TimeUpdateTask(self, self.time_handler)

        Log.i('BaseClock', 'initialized')

    def set_timers(self, init_times, init_delays):
        """
        Sets initial value of the clock time and delay.
        For each tuple, tuple[0] is 'w' time and tuple[1] is 'b' time.
        :param init_times: a tuple of clock time initial values.
        :param init_delays: a tuple of clock delay initial values.
        """
        self._init_times = init_times
        self._init_delays = init_delays
        # Set start times to timers too
        self._reset_timers()

        # Update UI
        self._application.update_timers()

    def _reset_timers(self):
        """
        Resets time and delay to their original values.
        """
        if self._init_times:
            self.time = list(self._init_times)
        if self._init_delays:
            self.delay = list(self._init_delays)

    def pause_or_resume(self):
        """
        Pauses the clock if its already 'active',
        resumes the clock if 'paused'.
        """
        if self.state == 'active':
            self.state = 'paused'
            self.time_handler.removeCallbacks(self.time_update_task)

            # Update UI
            self._application.update_ui_state()

        elif self.state == 'paused':
            self.state = 'active'
            self._start_timer()

            # Update UI
            self._application.update_ui_state()

    def restart(self):
        Log.i('BaseClock', 'called restart()')
        self.time_handler.removeCallbacks(self.time_update_task)
        self.state = 'new'
        self.turn = None
        self._reset_timers()

        # Update UI
        self._application.update_ui_state()

    def _start_timer(self):
        """
        Starts the timer
        """
        Log.i('BaseClock', 'called _start_timer()')
        self.start_time_millis = SystemClock.uptimeMillis()
        self.time_handler.removeCallbacks(self.time_update_task)
        self.time_handler.postDelayed(self.time_update_task, TIMER_DELAY)

    def _on_handler_tick(self, ms):
        """
        Callback called by Handler every tick
        """

        i = self._turn_ind()
        self._on_tick(ms, i)

        # updating ui
        self._application.update_timers()

    def on_switch_click(self, player):
        Log.i('BaseClock', 'called on_switch_player(%s), self.state:%s, self.turn:%s'
              % (player, self.state, self.turn))
        # Starts the clock if game hasn't started yet.
        if self.state == 'new':
            self.turn = 'w' if player == 'b' else 'b'
            self.state = 'active'
            self._start_timer()
            self._turn_switch(-1, self._turn_ind())

            # Update UI
            self._application.update_ui_state()

        # Switches the active clock
        elif self.state == 'active':
            Log.i('BaseClock', 'in active branch')
            if player == 'w' and self.turn == 'w':
                Log.i('BaseClock', 'switching to black')
                self.turn = 'b'
                self._turn_switch(1 - self._turn_ind(), self._turn_ind())
            elif player == 'b' and self.turn == 'b':
                Log.i('BaseClock', 'switching to white')
                self.turn = 'w'
                self._turn_switch(1 - self._turn_ind(), self._turn_ind())

            # Update UI
            self._application.update_ui_state()

    def _turn_ind(self):
        """
        Returns index of the current player.
        :returns: 0 for 'w' and 1 for 'b'
        """
        if self.turn == 'w':
            return 0
        elif self.turn == 'b':
            return 1
        else:
            raise Exception('self.turn is None')

    def _on_tick(self, ms, i):
        """
        :param ms: tick length in milliseconds
        :param i: index of the current player (0 for 'w', 1 for 'b')
        """
        pass

    def _turn_switch(self, o, i):
        """
        Called when player turn has been switched, or when clock starts.
        :param o: Index of the old player, or -1 if it is first round
        :param new_turn: Index of the player whose turn it is.
        """
        pass


class CounterupTimer(BaseClock):

    def _on_tick(self, ms, i):
        self.time[i] = self.time[i] + ms


class SuddenDeathClock(BaseClock):

    def _on_handler_tick(self, ms):
        i = self._turn_ind()
        self._on_tick(ms, i)

        # Checks if the timers have run out.
        if self.time[0] <= 0 or self.time[1] <= 0:
            self.time_handler.removeCallbacks(self.time_update_task)
            self.state = 'finished'
            self.turn = None

        # updating ui
        self._application.update_timers()

    def _on_tick(self, ms, i):
        self.time[i] = self.time[i] - ms


class HourGlassClock(SuddenDeathClock):

    def _on_tick(self, ms, i):
        self.time[i] = self.time[i] - ms
        self.time[1 - i] = self.time[1 - i] - ms


class TimerPerMove(SuddenDeathClock):

    def _turn_switch(self, o, i):
        if o != -1:
            self.time[o] = self._init_times[o]


class SimpleDelay(SuddenDeathClock):

    def _on_tick(self, ms, i):
        t, d = self.time[i], self.delay[i]

        diff = d - ms
        if diff < 0:
            self.time[i], self.delay[i] = t + diff, 0
        else:
            self.time[i], self.delay[i] = t, diff


class BronsteinDelay(SuddenDeathClock):

    def _on_tick(self, ms, i):
        t, d = self.time[i], self.delay[i]

        #TODO: max function not available
        diff = d - ms
        if diff < 0:
            self.time[i], self.delay[i] = t - ms, 0
        else:
            self.time[i], self.delay[i] = t - ms, diff

    def _turn_switch(self, o, i):
        # Checks if it's not the first turn
        if o != -1:
            if self.delay[o] >= 0:
                time_spent = self._init_delays[o] - self.delay[o]
                self.time[o] = self.time[o] + time_spent

            self.delay[o] = self._init_delays[o]


class FischerDelay(BronsteinDelay):

    def _turn_switch(self, o, i):
        self.time[i] = self.time[i] + self._init_delays[i]
        self.delay[i] = self._init_delays[i]


class ButtonClick(implements=android.view.View[OnClickListener]):
    """
    Python wrapper for the Java interface OnClickListener
    """

    def __init__(self, callback, *args, **kwargs):
        self.callback = callback
        self.args = args
        self.kwargs = kwargs

    def onClick(self, view: android.view.View) -> void:
        self.callback(*self.args, **self.kwargs)


class MyApplication:

    def __init__(self):
        self.activity = None

    def link(self, activity):
        self.activity = activity

    def onCreate(self):
        # Building the UI
        vlayout = LinearLayout(self.activity)
        vlayout.setOrientation(LinearLayout.VERTICAL)

        # Top clock
        top_vlayout = LinearLayout(self.activity)

        self.top_clock = TextView(self.activity)
        self.top_clock.setTextSize(50)

        self.top_delay = TextView(self.activity)
        self.top_delay.setTextSize(15)

        top_vlayout.setOnClickListener(ButtonClick(self.top_player_touched))
        top_vlayout.addView(self.top_clock)
        top_vlayout.addView(self.top_delay)
        vlayout.addView(top_vlayout)

        # Button row
        button_layout = LinearLayout(self.activity)
        button_layout.setOrientation(LinearLayout.HORIZONTAL)
        vlayout.addView(button_layout)

        self.pause_button = Button(self.activity)
        self.pause_button.setText('Pause')
        self.pause_button.setOnClickListener(ButtonClick(self.pause_or_resume_clicked))
        button_layout.addView(self.pause_button)

        self.restart_button = Button(self.activity)
        self.restart_button.setText('Restart')
        self.restart_button.setOnClickListener(ButtonClick(self.restart_clicked))
        button_layout.addView(self.restart_button)

        # Bottom clock
        bot_vlayout = LinearLayout(self.activity)

        self.bot_clock = TextView(self.activity)
        self.bot_clock.setTextSize(50)

        self.bot_delay = TextView(self.activity)
        self.bot_delay.setTextSize(15)

        bot_vlayout.setOnClickListener(ButtonClick(self.bottom_player_touched))
        bot_vlayout.addView(self.bot_clock)
        bot_vlayout.addView(self.bot_delay)
        vlayout.addView(bot_vlayout)

        self.activity.setContentView(vlayout)

        # Clock should be create after setContentView
        self.clock = CounterupTimer(self)
        self.clock.set_timers((0, 0), None)
        # self.clock = TimerPerMove(self)
        # self.clock.set_timers((10000, 10000), None)
        # self.clock.set_timers((10000, 10000), (2000, 2000))

    def top_player_touched(self):
        self.clock.on_switch_click('w')
        return True

    def bottom_player_touched(self):
        self.clock.on_switch_click('b')
        return True

    def pause_or_resume_clicked(self):
        Log.i('MyApplication', 'called pause_clicked()')
        self.clock.pause_or_resume()

    def restart_clicked(self):
        Log.i('MyApplication', 'called restart_clicked()')
        self.clock.restart()

    def update_ui_state(self):
        state = self.clock.state
        turn = self.clock.turn

        if state == 'new':
            self.top_clock.setAlpha(1.0)
            self.bot_clock.setAlpha(1.0)
            self.update_timers()

        elif state == 'active':
            self.pause_button.setText('Pause')
            if turn == 'w':
                self.bot_clock.setAlpha(0.2)
                self.top_clock.setAlpha(1.0)
            else:
                self.top_clock.setAlpha(0.2)
                self.bot_clock.setAlpha(1.0)

        elif state == 'paused':
            self.pause_button.setText('Resume')

        elif state == 'finished':
            self.top_clock.setAlpha(1.0)
            self.bot_clock.setAlpha(1.0)

    def update_timers(self):
        self.top_clock.setText(format_time(self.clock.time[0]))
        self.bot_clock.setText(format_time(self.clock.time[1]))

        self.top_delay.setText(format_time(self.clock.delay[0]))
        self.bot_delay.setText(format_time(self.clock.delay[1]))


# Binds Python code to main Android activity (PythonActivity).
app = MyApplication()
python_activity = android.PythonActivity.setListener(app)
app.link(python_activity)
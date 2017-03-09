import android
import android.view
from android.widget import LinearLayout
from android.widget import TextView
from android.widget import Button

from android.os import SystemClock
from android.os import Handler

from android.util import Log

# delay in milliseconds for time handler
time_task_handler_delay = 20



def sub2(t, d, tick):
    diff = d - tick
    if diff < 0:
        return (t + diff, 0)
    else:
        return (t, diff)


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

        self.handler.postDelayed(self, time_task_handler_delay)
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
        self.w_time = None
        self.w_delay = None
        self.b_time = None
        self.b_delay = None

        # timer task
        self.start_time_millis = None
        self.time_handler = Handler()
        self.time_update_task = TimeUpdateTask(self, self.time_handler)

        Log.i('BaseClock', 'initialized')

    def pause_or_resume(self):
        if self.state == 'active':
            self.state = 'paused'
            self.time_handler.removeCallbacks(self.time_update_task)
            self._application.pause_button.setText('Resume')
        elif self.state == 'paused':
            self.state = 'active'
            self._start_timer()
            self._application.pause_button.setText('Pause')

    def restart(self):
        Log.i('BaseClock', 'called restart()')
        self.time_handler.removeCallbacks(self.time_update_task)
        self.state = 'new'
        self.turn = None
        self._reset_timers()

    def _start_timer(self):
        """
        Starts the timer
        """
        Log.i('BaseClock', 'called _start_timer()')
        self.start_time_millis = SystemClock.uptimeMillis()
        self.time_handler.removeCallbacks(self.time_update_task)
        self.time_handler.postDelayed(self.time_update_task, time_task_handler_delay)

    def _on_handler_tick(self, ms):
        """
        callback called every tick
        TODO: should this function handle updating the UI?
        """

        self._on_tick(ms)

        # Checks if the timers have run out.
        if self.b_time <= 0 or self.w_time <= 0:
            self.time_handler.removeCallbacks(self.time_update_task)
            self.state = 'finished'
            self.turn = None

        self._application.update_ui()

    def on_switch_click(self, player):
        Log.i('BaseClock', 'called on_switch_player(%s), self.state:%s, self.turn:%s'
              % (player, self.state, self.turn))
        # Starts the clock if game hasn't started yet.
        if self.state == 'new':
            self.turn = 'w' if player == 'b' else 'b'
            self.state = 'active'
            self._start_timer()

        # Switches the active clock
        elif self.state == 'active':
            Log.i('BaseClock', 'in active branch')
            if player == 'w' and self.turn == 'w':
                Log.i('BaseClock', 'switching to black')
                self.turn = 'b'
            elif player == 'b' and self.turn == 'b':
                self.turn = 'w'
                Log.i('BaseClock', 'switching to white')

    def _reset_timers(self):
        pass

    def _on_tick(self, ms):
        pass


class SuddenDeathClock(BaseClock):

    def __init__(self, application, w_start_time, b_start_time):
        super().__init__(application)
        self.w_start_time = w_start_time
        self.b_start_time = b_start_time
        self._reset_timers()

    def _reset_timers(self):
        self.w_time = self.w_start_time
        self.b_time = self.b_start_time

    def _on_tick(self, ms):
        if self.turn == 'w':
            self.w_time = self.w_time - ms
        else:
            self.b_time = self.b_time - ms


class HourGlassClock(SuddenDeathClock):

    def __init__(self, application, w_start_time, b_start_time):
        super().__init__(application, w_start_time, b_start_time)

    def _on_tick(self, ms):
        if self.turn == 'w':
            self.w_time = self.w_time - ms
            self.b_time = self.b_time + ms
        else:
            self.b_time = self.b_time - ms
            self.w_time = self.w_time + ms


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
        # self.clock = BaseClock(self.update_ui)
        self.clock = HourGlassClock(self, 10000, 10000)
        # self.clock = None

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

    def onStart(self):
        self.top_clock.setText("I'm top")
        self.bot_clock.setText("I'm bottom")

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

    def update_ui(self):
        self.top_clock.setText(str(self.clock.w_time))
        self.bot_clock.setText(str(self.clock.b_time))


# Binds Python code to main Android activity (PythonActivity).
app = MyApplication()
python_activity = android.PythonActivity.setListener(app)
app.link(python_activity)
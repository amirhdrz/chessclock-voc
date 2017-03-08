import android
import android.view
from android.widget import LinearLayout
from android.widget import TextView
from android.widget import Button

from android.os import SystemClock
from android.os import Handler

from collections import namedtuple

# delay in milliseconds for time handler
time_task_handler_delay = 20


Timer = namedtuple('Timer', 'time, delay')


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
        self.turn = None  # if inactive: means the player who's turn it is to play
        # if active: means the player, who is currently playing
        # if none: means the game has not been started yet

        # time control
        self.time_control = None

        # timer task
        self.start_time_millis = None
        self.time_handler = Handler()
        self.time_update_task = TimeUpdateTask(self, self.time_handler)

    def resume(self):
        if self.state == 'inactive' and self.turn is not None:
            self.state = 'active'
            self._start_timer()

    def pause(self):
        self.time_handler.removeCallbacks(self.time_update_task)
        self.state = 'inactive'

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
        self.time_control.tick(ms)
        self._application.update_ui()

    def on_switch_click(self, player):
        if self.turn is None:
            self.turn = player
            self._start_timer()
        elif self.turn == 'w' and self.state == 'active':
            self.turn = 'b'


class BaseTimeControl:

    def __init__(self):
        self.w_timer = Timer(0, None)
        self.b_timer = Timer(0, None)

    def tick(self, ms):
        pass



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
        self.clock = Clock(self)
        # self.clock = None

    def link(self, activity):
        self.activity = activity

    def onCreate(self):
        # Building the UI
        vlayout = LinearLayout(self.activity)
        vlayout.setOrientation(LinearLayout.VERTICAL)

        self.top_clock = TextView(self.activity)
        self.top_clock.setTextSize(50)
        self.top_clock.setOnClickListener(ButtonClick(self.top_player_touched))
        vlayout.addView(self.top_clock)

        button_layout = LinearLayout(self.activity)
        button_layout.setOrientation(LinearLayout.HORIZONTAL)
        vlayout.addView(button_layout)

        self.pause_button = Button(self.activity)
        self.pause_button.setText('Pause')
        self.pause_button.setOnClickListener(ButtonClick(self.pause_clicked))
        button_layout.addView(self.pause_button)

        self.restart_button = Button(self.activity)
        self.restart_button.setText('Restart')
        self.pause_button.setOnClickListener(ButtonClick(self.restart_clicked))
        button_layout.addView(self.restart_button)

        self.bottom_clock = TextView(self.activity)
        self.bottom_clock.setTextSize(50)
        self.bottom_clock.setOnClickListener(ButtonClick(self.bottom_player_touched))
        vlayout.addView(self.bottom_clock)

        self.activity.setContentView(vlayout)

    def onStart(self):
        self.top_clock.setText("I'm top")
        self.bottom_clock.setText("I'm bottom")

    def top_player_touched(self):
        self.clock.on_switch_click('w')
        return True

    def bottom_player_touched(self):
        self.clock.on_switch_click('b')
        return True

    def pause_clicked(self):
        self.clock.pause()
        pass

    def restart_clicked(self):
        self.clock.restart()
        pass

    def update_ui(self):
        self.top_clock.setText(str(self.clock.time_control.w_timer[0]))
        self.bottom_clock.setText(str(self.clock.time_control.b_timer[0]))



app = MyApplication()
python_activity = android.PythonActivity.setListener(app)
app.link(python_activity)
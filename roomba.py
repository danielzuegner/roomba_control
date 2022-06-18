from pyPS4Controller.controller import Controller
from pyroombaadapter import PyRoombaAdapter
import threading
import math
import songs
from time import sleep

# this may be different for you
PORT = "/dev/ttyACM0"
adapter = PyRoombaAdapter(PORT)

class MyController(Controller):

    def play_song(self, song: songs.Song):

        def chunks(lst, n):
            """Yield successive n-sized chunks from lst."""
            for i in range(0, len(lst), n):
                yield lst[i:i + n]
        if self.song_playing != 0:
            while self.song_playing != 0:
                self.song_playing = 'abort'
                sleep(0.05)
            sleep(0.05)
        self.song_playing = song.name
        num_notes = 16
        for ix, chunk in enumerate(chunks(list(zip(song.notes, song.durations)), num_notes)):
            _notes, _durations = list(zip(*chunk))
            adapter.send_song_cmd(ix % 4, len(_notes), _notes, _durations)
            len_seconds = sum(_durations) / 64
            sleep(0.02)
            adapter.send_play_cmd(ix % 4)
            sleep(len_seconds)
            if self.song_playing != song.name:
                print("aborting", self.song_playing)
                self.song_playing = 0
                return
        self.song_playing = 0


    def __init__(self, queue=None, **kwargs):
        Controller.__init__(self, **kwargs)
        self.queue = queue
        self.l3x = 0
        self.l3y = 0
        self.speed = 0
        self.dir = 0
        self.sidebrush = 0
        self.mainbrush = 0
        self.vacuum = 0
        self.song_playing = 0
        self.song_thred = None

    def drive(self):
        self.speed = min(math.sqrt(self.l3y*self.l3y + self.l3x*self.l3x), 1)
        self.dir = (math.pi/-2 + math.atan2(self.l3y, self.l3x)) % (2*math.pi)
        if self.dir < math.pi/2:
            ratio = self.dir/(math.pi/2)
            right = 1
            left = 1 - ratio * 2
        elif self.dir < math.pi:
            ratio = (self.dir - math.pi/2)/(math.pi/2)
            left = -1
            right = 1 - ratio * 2
        elif self.dir < math.pi * 1.5:
            ratio = (self.dir - math.pi)/(math.pi/2)
            right = -1
            left = -1 + ratio *2
        else:
            ratio = (self.dir - math.pi*1.5)/(math.pi/2)
            left = 1
            right = -1 + 2 * ratio
        maxSpeed = 500
        print(self.speed, left, right)
        adapter.send_drive_direct(maxSpeed*left*self.speed, maxSpeed*right*self.speed)

    def brushes(self):
        adapter.send_pwm_moters(self.mainbrush*64, self.sidebrush*127, self.vacuum*127)

    def on_L3_up(self, value):
        self.l3y = -(value / 32767.0)
        self.drive()

    def on_L3_down(self, value):
        self.l3y = -(value / 32767.0)
        self.drive()

    def on_L3_left(self, value):
        self.l3x = -(value / 32767.0)
        self.drive()

    def on_L3_right(self, value):
        self.l3x = -(value / 32767.0)
        self.drive()

    def on_L3_x_at_rest(self):
        self.l3x = 0
        self.drive()

    def on_L3_y_at_rest(self):
        self.l3y = 0
        self.drive()

    def on_triangle_press(self):
        song = songs.SONGS_PER_BUTTON['triangle']
        if self.song_playing == song.name:
            self.song_playing = "abort"
            return
        th = threading.Thread(target=self.play_song, args=(song,))
        th.start()

    def on_x_press(self):
        song = songs.SONGS_PER_BUTTON.get('x', None)
        if song is None: 
            return 
        if self.song_playing == song.name:
            self.song_playing = "abort"
            return
        th = threading.Thread(target=self.play_song, args=(song,))
        th.start()

    def on_square_press(self):
        song = songs.SONGS_PER_BUTTON.get('square', None)
        if song is None: 
            return 
        if self.song_playing == song.name:
            self.song_playing = "abort"
            return
        th = threading.Thread(target=self.play_song, args=(song,))
        th.start()

    def on_circle_press(self):
        song = songs.SONGS_PER_BUTTON.get('circle', None)
        if song is None: 
            return 
        if self.song_playing == song.name:
            self.song_playing = "abort"
            return
        th = threading.Thread(target=self.play_song, args=(song,))
        th.start()

    def on_up_arrow_press(self):
        song = songs.SONGS_PER_BUTTON.get('up_arrow', None)
        if song is None: 
            return 
        if self.song_playing == song.name:
            self.song_playing = "abort"
            return
        th = threading.Thread(target=self.play_song, args=(song,))
        th.start()

    def on_down_arrow_press(self):
        song = songs.SONGS_PER_BUTTON.get('down_arrow', None)
        if song is None: 
            return 
        if self.song_playing == song.name:
            self.song_playing = "abort"
            return
        th = threading.Thread(target=self.play_song, args=(song,))
        th.start()

    def on_L1_press(self):
        adapter.change_mode_to_safe()

    def on_R3_up(self, value):
        self.mainbrush = -(value / 32767.0)
        self.brushes()

    def on_R3_down(self, value):
        self.mainbrush = -(value / 32767.0)
        self.brushes()

    def on_R3_left(self, value):
        self.sidebrush = -(value / 32767.0)
        self.brushes()

    def on_R3_right(self, value):
        self.sidebrush = -(value / 32767.0)
        self.brushes()

    def on_R3_x_at_rest(self):
        self.sidebrush = 0
        self.brushes()

    def on_R3_y_at_rest(self):
        self.mainbrush = 0
        self.brushes()

    def on_R2_press(self, value):
        self.vacuum = (value + 32767.0) / (2*32767.0)
        self.sidebrush = (value + 32767.0) / (2*32767.0)
        self.mainbrush = (value + 32767.0) / (2*32767.0)
        self.brushes()

    def on_R2_release(self):
        self.vacuum = 0
        self.sidebrush = 0
        self.mainbrush = 0
        self.brushes()

controller = MyController(interface="/dev/input/js0", connecting_using_ds4drv=False)
controller.listen(timeout=60)
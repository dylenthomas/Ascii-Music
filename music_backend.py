import os
import pyaudio
import wave
import numpy as np
from mutagen import id3
from pydub import AudioSegment

class create_music_backend:
    def __init__(self):
        self.p = pyaudio.PyAudio()

    def get_song_name_from_path(self, path):
        path = path.split('/')
        song_file = path[len(path) - 1]
        song_file = song_file.split('.')

        return song_file[0]

    def convert_artist(self, artist_list):
       artist = ''
       for i in range(len(artist_list)):
           if i == len(artist_list) - 1:
               artist += artist_list[i]
           else:
               artist += artist_list[i] + ', '

       return artist

    def get_song_metadata(self):
       metadata = id3.ID3(self.file_name)
       found_metadata = {'Artist': (False,), 'Album': (False,), 'Genre': (False,), 'Image Data': (False,)}
       try:
           artist_list = metadata['TPE1'].text
           found_metadata['Artist'] = (True, self.convert_artist(artist_list))
       except KeyError:
           pass

       try:
           album = metadata['TALB'].text
           found_metadata['Album'] = (True, album)
       except KeyError:
           pass

       try:
           genre = metadata['TCON'].text
           found_metadata['Genre'] = (True, genre)
       except KeyError:
           pass

       try:
           image_bytes = metadata['APIC:'].data
           found_metadata['Image Data'] = (True, image_bytes)
       except KeyError:
           pass

       out = {}
       for key in list(found_metadata.keys()):
           out[key] = found_metadata[key][1] if found_metadata[key][0] else 'Not Found'

       return out

    def init_song(self, playlist=None, song_name=None, path=None, open_stream=True):
        self.is_callback = False

        if path is not None:
            self.file_name = path
            self.song_name = self.get_song_name_from_path(path)
        else:
            assert playlist is not None and song_name is not None
            self.file_name = os.path.join('.', playlist, song_name + '.mp3')
            self.song_name = song_name

        mp3_data = AudioSegment.from_mp3(self.file_name)
        self.wav_file = os.path.join('.', '.temp', self.song_name + '.wav')

        mp3_data.export(self.wav_file, format='wav')
        self.sf = wave.open(self.wav_file, 'rb')

        self.total_frames = self.sf.getnframes()
        self.channels = self.sf.getnchannels()
        self.byte_depth = self.sf.getsampwidth()
        self.file_size = self.get_file_size()
        self.frame_rate = self.sf.getframerate()
        self.song_len_seconds = self.total_frames / self.frame_rate

        if open_stream:
            self.stream = self.p.open(format=self.p.get_format_from_width(self.byte_depth), channels=self.channels, rate=self.sf.getframerate(), frames_per_buffer = 1024, output=True, stream_callback=self.callback)

    def get_file_size(self):
        temp = open(self.wav_file, 'rb')
        temp.seek(0, 2)
        bytes = temp.tell()
        temp.close()

        return bytes

    def seconds_to_mins(self, seconds):
        if seconds >= 60:
            mins = str(seconds // 60)
            seconds = seconds % 60

            if seconds < 10:
                seconds = '0' + str(seconds)
            else:
                seconds = str(seconds)
        else:
            mins = '0'

            if seconds < 10:
                seconds = '0' + str(seconds)
            else:
                seconds = str(seconds)

        return mins + ':' + seconds

    def restart_song(self):
        self.pause_song()
        self.sf.rewind()
        self.play_song()

    def pause_song(self):
        self.stream.stop_stream()
        self.is_paused = True

    def stop_song_playback(self):
        self.stream.stop_stream()
        self.stream.close()
        self.sf.close()
        os.remove(self.wav_file)

    def play_song(self):
        self.stream.start_stream()
        self.is_paused = False

    def callback(self, in_data, frame_count, time_info, status):
        self.is_callback = True
        self.sound_data = self.sf.readframes(frame_count)
        self.pointer = self.sf.tell()

        return (self.sound_data, pyaudio.paContinue)

    def close_backend(self):
        self.stream.close()
        self.p.terminate()
        self.sf.close()

    def delete_temp_file(self):
        os.remove(self.wav_file)

if __name__ == '__main__':
    import time
    player = create_music_backend(path = './music/This Is ZZ Top/Sharp Dressed Man.mp3')
    player.init_song()
    player.play_song()
    time.sleep(2)

    i = 0
    while i < 100000:
        print(player.pointer / player.total_frames)
        i += 1

    player.stop_song_playback()

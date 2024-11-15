import curses
import math
import time
import numpy as np
#import fastgoertzel as G
from music_backend import create_music_backend
from image_to_ascii import convert_image_to_ascii

class player_ui:
    def __init__(self, banner_logo:str, que:list):
        self.que = que
        self.banner_logo = banner_logo
        self.block = '\u2588'
        self.font_conversion_matrix = ' !"#$%&' + "'" + '()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[' + '\\' + ']^_`abcdefghijklmnopqrstuvwxyz{|}~' + chr(196) + chr(214) + chr(220) + chr(228) + chr(246) + chr(252) + chr(223)
        self.chunky_path = './.fonts/Chunky.flf'
        self.paused = ' ' + self.block * 2 + ' ' + self.block * 2 + ' '

        self.goatz_freqs = [60, 105, 150, 275, 400, 700, 1000, 1700, 2400, 4200, 6000, 10500, 15000] #all are in Hz

        self.music_backend = create_music_backend()

        curses.wrapper(self.main)

    def main(self, stdscr):
        stdscr.clear()
        stdscr.nodelay(1)
        curses.curs_set(0)

        self.screen_rows, self.screen_cols = stdscr.getmaxyx()
        self.empty_rows = self.screen_rows - 10
        self.album_cover_width = (self.empty_rows - 2) * 2

        #Create pad to house the progress bar
        self.progress_bar_width = self.screen_cols - self.album_cover_width - 10 #minus 10 for right and left padding of progress bar
        progress_pad = curses.newpad(3, self.progress_bar_width)

        #Create pad to house the fft_display
        self.num_fft_bars = len(self.goatz_freqs)
        self.tallest_fft_bar = 20
        fft_pad = curses.newpad(self.num_fft_bars * 2, self.tallest_fft_bar + 1)

        for song_path in self.que:
           self.music_backend.init_song(path=song_path)
           self.cur_metadata = self.music_backend.get_song_metadata()
           split_path = song_path.split('/')
           self.song_title = split_path[len(split_path) - 1].split('.')[0]

           self.create_screen(stdscr)

           while not self.music_backend.is_callback: #wait for the callback function to start
               pass

           self.bytes_per_frame = self.music_backend.channels * self.music_backend.byte_depth

           opt = self.song_player(stdscr, progress_pad, fft_pad)
           if opt == 'q':
               break

        self.music_backend.close_backend()

    def song_player(self, stdscr, progress_pad, fft_pad):
        self.music_backend.play_song()
        total_len_sec = int(self.music_backend.song_len_seconds)
        total_len = self.music_backend.seconds_to_mins(total_len_sec)

        while True:
            bytes_read = self.music_backend.pointer * self.music_backend.channels * self.music_backend.byte_depth
            progress = bytes_read / self.music_backend.file_size
            progress_sec = self.music_backend.pointer // self.music_backend.frame_rate
            key = stdscr.getch()

            match key:
                case 32: #'space'
                    if self.music_backend.is_paused:
                        self.music_backend.play_song()
                    else:
                        self.music_backend.pause_song()

                case 114: #'r'
                    if progress > 0: #preven spam
                        self.music_backend.restart_song()
                        progress_pad.erase()

                case 115: #'s'
                    if progress > 0: #prevent spam
                        self.music_backend.stop_song_playback()
                        return 's'

                case 113: #'q'
                    self.music_backend.stop_song_playback()
                    return 'q'

                case curses.KEY_RIGHT: #TODO Implement these two
                    pass
                case curses.KEY_LEFT:
                    pass

            progress_pad.addstr(0, 0, self.music_backend.seconds_to_mins(progress_sec))

            if self.music_backend.is_paused:
                progress_pad.addstr(0, self.progress_bar_width // 2 - 4, self.paused)
                progress_pad.addstr(2, self.progress_bar_width // 2 - 4, self.paused)
            else:
                progress_pad.addstr(0, self.progress_bar_width // 2 - 4, ' ' * len(self.paused))
                progress_pad.addstr(2, self.progress_bar_width // 2 - 4, ' ' * len(self.paused))

            progress_pad.addstr(0, self.progress_bar_width - 5 - len(total_len), total_len)

            num_bars = round(progress * (self.progress_bar_width - 2 - 5))
            progress_pad.addstr(1, 0, self.make_bar(num_bars))
            progress_pad.refresh(0, 0, self.empty_rows - 2, self.album_cover_width + 5, self.empty_rows, self.screen_cols - 5) #first two values are relative to pad coords last four are relative to screen


            np_temp = np.frombuffer(self.music_backend.sound_data, dtype=np.int16) #for some reason going directly from bytes to float64 fucks up the data
            amp_list = []



            sel_freq_ampts = self.goertzel()
            upper = self.tallest_fft_bar * 10000






            for ind in range(self.num_fft_bars):
                val = sel_freq_ampts[ind]
                val *= self.tallest_fft_bar

                if val > float(self.tallest_fft_bar):
                    val = self.tallest_fft_bar
                elif val < 0.0:
                    val = 0
                elif math.isnan(val):
                    val = 0
                else:
                    val = round(val)

                bar = '|' + '-' * (self.tallest_fft_bar - val - 1) + str(val)

                fft_pad.addstr(ind * 2, 0, bar)
            fft_pad.refresh(0, 0, 20, self.screen_cols - self.tallest_fft_bar - 4, 20 + self.num_fft_bars * 2, self.screen_cols - 2)

            if num_bars == self.progress_bar_width - 2 - 5: #song is done
                self.music_backend.stop_song_playback()
                return 'd'

    def division(self, a, b):
        if a == 0:
            return 0
        elif b == 0:
            return 0
        else:
            return a / b

    def goertzel(self, data, freq):
        #TODO find equivalent functions
        n = len(np.temp)
        k = freq * n

        w = 2.0 * math.pi * k / n
        cw = math.cos(w)
        c = 2.0 * cw
        sw = math.sin(w)
        z1 = 0.0
        z2 = 0.0

        for i in range(n):
            z0 = data[i] + c * z1 - z2
            z2 = z1
            z1 = z0

        ip = cw * z1 - z2
        qp = sw * z1

        amp = (ip.powi(2) + qp.powi(2)).sqrt() / n / 2.0
        return amp


        return amp_list

    def make_bar(self, scaler):
        if self.music_backend.is_paused:
            start_of_pause = self.progress_bar_width // 2 - 5
            pause_width = len(self.paused)

            if scaler <= start_of_pause:
                bar_solid = self.block * scaler
                bar_dash_1 = '-' * (start_of_pause - scaler)
                bar_dash_2 = '-' * (self.progress_bar_width - start_of_pause - 5 - pause_width - 2) #minus 2 is for the []'s on the ends
                whole_bar = '[' + bar_solid + bar_dash_1 + self.paused + bar_dash_2 + ']'

            elif start_of_pause - scaler <= 0 and start_of_pause - scaler >= -pause_width:
                bar_solid = self.block * start_of_pause
                bar_dash = '-' * (self.progress_bar_width - start_of_pause - 5 - pause_width - 2) #minus 2 is for the []'s on the ends 
                whole_bar = '[' + bar_solid + self.paused + bar_dash + ']'

            else:
                bar_solid_1 = self.block * start_of_pause
                bar_solid_2 = self.block * (scaler - start_of_pause - pause_width)
                bar_dash = '-' * (self.progress_bar_width - scaler - 5 - 2) #minus 2 is for the []'s on the ends 
                whole_bar = '[' + bar_solid_1 + self.paused + bar_solid_2 + bar_dash + ']'

        else:
            bar_solid = self.block * scaler
            bar_dash = '-' * (self.progress_bar_width - 2 - scaler - 5) #minus 2 is for the []'s on the ends
            whole_bar = '[' + bar_solid + bar_dash + ']'

        return whole_bar

    def create_screen(self, stdscr):
        album_ascii = convert_image_to_ascii(self.cur_metadata['Image Data'], self.album_cover_width, 0.5) 

        stdscr.erase()
        stdscr.addstr(0, 0, self.banner_logo)
        stdscr.addstr(7, 0, '=' * self.screen_cols)

        #Album cover
        stdscr.addstr(8, 0, album_ascii)

        #Song title
        song_title_ascii, tallest_char = self.convert_str_to_ascii(self.song_title, self.chunky_path, '@@', 7, True)

        row = 10
        ind = 0
        for block in song_title_ascii:
            for line in block:
                stdscr.addstr(row, self.album_cover_width + 5, line, curses.A_BOLD)
                row += 1
            if ind == 0:
                row = 10 + tallest_char
                ind += 1

        #Artist
        artist, tallest_char = self.convert_str_to_ascii('By: ' + self.cur_metadata['Artist'], self.chunky_path, '@@', 7)

        for block in artist:
            for line in block:
                stdscr.addstr(row, self.album_cover_width + 5, line, curses.A_BOLD)
                row += 1
        row += 2
        stdscr.addstr(row, self.album_cover_width + 5, 'Album: ' + self.cur_metadata['Album'][0], curses.A_BOLD)
        row += 2
        stdscr.addstr(row, self.album_cover_width + 5, 'Genre: ' + self.cur_metadata['Genre'][0], curses.A_BOLD)

        stdscr.refresh()

    def convert_str_to_ascii(self, text, file_path, file_line_sep, num_header_lines, is_underline:bool=False):
        #any $ means space
        with open(file_path, 'r') as file:
            un_formated_chars = file.read().split(file_line_sep)

        cleaned_chars = []
        ind = 0
        for char in un_formated_chars:
            new_line_split = char.split('\n')

            #remove header lines
            if ind == 0:
                new_line_split = new_line_split[num_header_lines:]
                ind += 1

            frmtd_new_line_split = []
            for line in new_line_split:
                line = line.split(file_line_sep[0])[0]
                if line == '':
                    continue

                line = line.replace('$', ' ')
                frmtd_new_line_split.append(line)

            cleaned_chars.append(frmtd_new_line_split)

        converted_chars = []
        for char in text:
            text_loc = self.font_conversion_matrix.find(char)
            converted_chars.append(cleaned_chars[text_loc])

        tallest = max([len(a) for a in converted_chars])
        total_max_width_list = [] #keep track of how wide the final string will be

        for conv_char in converted_chars:
            widest_row = max([len(a) for a in conv_char])
            total_max_width_list.append(widest_row)

        total_max_width = sum(total_max_width_list)
        printable_cols = self.screen_cols - self.album_cover_width - 10

        if total_max_width >= printable_cols:
            diff = total_max_width - printable_cols
            if diff >= printable_cols:
                converted_chars[:-3]
                for _ in range(3):
                    converted_chars.append(cleaned_chars[self.font_conversion_matrix.find('.')])

            #find the char that makes the title too long
            running_totl = 0
            for i in range(len(total_max_width_list)):
                width = total_max_width_list[i]
                running_totl += width
                if running_totl >= printable_cols:
                    break_point = i
                    break

            #work backwards from break_point to find space where word that breaks screen starts
            converted_chars.reverse()
            converted_chars_cpy = converted_chars[:break_point]
            converted_chars.reverse()

            i = 0
            for char in converted_chars_cpy:
                if all(a == char[0] for a in char):
                    space_of_interest = i
                    break

                i +=1

            space_of_interest = len(converted_chars_cpy) - space_of_interest - 1 #convert index to normal order index
            space_of_interest += len(converted_chars) - break_point

        else:
            #if there is no length issue then this will make the condition always fail in the next loop also makes adding new lines easier to the first row
            space_of_interest = len(text)

        output = ["", ""]
        for r in range(tallest):
            for c in range(len(text)):
                if c > space_of_interest:
                    output[1] += converted_chars[c][r]
                    if c == len(text) - 1:
                        output[1] += '\n'
                elif c < space_of_interest:
                    output[0] += converted_chars[c][r]
                    if c == space_of_interest - 1:
                        output[0] += '\n'
                else: #skip the space for formating purposes
                    continue 
        if is_underline:
            output[1] += '-' * sum(total_max_width_list[:space_of_interest])

        output = [a.split('\n') for a in output]

        return output, tallest

if __name__ == '__main__':
    import glob
    songs = glob.glob('./music/This Is ZZ Top/*.mp3')
    ui = player_ui('logo', songs)

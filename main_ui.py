import glob
import time
import random
import os
import sys
import json
import sqlite3
import keyboard
import curses, curses.panel, curses.textpad
import numpy as np

from PIL import Image
from image_to_ascii import convert_image_to_ascii
from create_music_info_db import create_music_info_db
from player_ui import player_ui

DATABASE_PATH = './music_info_db/music_info_db.db'

class MainMenu:
    def __init__(self):
        self.banner_logo = """
 _______ _______ ______ _______ _______      _______             __      
|   _   |     __|      |_     _|_     _|    |   |   .--.--.-----|__.----.
|       |__     |   ---|_|   |_ _|   |_     |       |  |  |__ --|  |  __|
|___|___|_______|______|_______|_______|    |__|_|__|_____|_____|__|____|
==================================================================================
"""
        curses.wrapper(self.welcome_screen)

    def run_menu(self, menu, *args, **kwargs):
        return menu(*args, **kwargs)

    def run_menu_input(self, option_list:list):
        while True:
            try:
                choice = int(input('Choice:'))

                if choice not in option_list:
                    self.input_error(f'{choice} is not an available option.')
                else:
                    return choice

            except ValueError:
                self.input_error(f'{choice} is not an Int. Please enter a base 10 int.')

    def parse_settings(self, read_key=None, read=True, write_key=None, write_value=None):
        with open('./.config/ascii_music_settings.json', 'r') as settings:
            curr_settings = json.load(settings)

        if read:
            try:
                return curr_settings[read_key]
            except KeyError:
                return 'Value is not set'

        else:
            with open('./.config/ascii_music_settings.json', 'w') as settings:
                curr_settings[write_key] = write_value
                json.dump(curr_settings, settings)

    def welcome_screen(self, stdscr):
        stdscr.clear()
        #stdscr.nodelay(1)

        stdscr.addstr(0, 0, self.banner_logo)
        stdscr.addstr(7, 0, 'Welcome')

        stdscr.refresh()

        self.screen_rows, self.screen_cols = stdscr.getmaxyx()

        self.main_menu(stdscr)

    def main_menu(self, stdscr):
        stdscr.clear()
        curses.curs_set(False)

        stdscr.addstr(0, 0, self.banner_logo)
        stdscr.addstr(7, 0, 'Enter an option:')
        stdscr.addstr(8, 0, '1: Show all songs')
        stdscr.addstr(9, 0, '2: Show all playlists')
        stdscr.addstr(10, 0, '3: Settings')
        stdscr.addstr(11, 0, 'q: quit')

        stdscr.refresh()

        while True:
            choice = stdscr.getch()

            if choice == ord('1'):
                return self.run_menu(self.see_all, stdscr, 'song')
            elif choice == ord('2'):
                return self.run_menu(self.see_all, stdscr, 'playlist')
            elif choice == ord('3'):
                return self.run_menu(self.settings, stdscr)
            elif choice == ord('q'):
                break

    def see_all(self, stdscr, dtype:str):
        scrolling_win = ScrollingWindow(self.banner_logo, dtype)
        que_type, media = scrolling_win.main(stdscr)

        if que_type != 'q':
            q_algo = create_q(que_type, media, 10)
            if que_type == 'r':
                song_ids = q_algo.random()
            elif que_type == 's':
                pass
            elif que_type == 'p':
                pass

            player = player_ui(self.banner_logo, song_ids)

        return self.run_menu(self.main_menu, stdscr)

    def settings(self, stdscr):
        stdscr.clear()

        stdscr.addstr(0, 0, self.banner_logo)
        stdscr.addstr(7, 0, '1: Set root path for music folder')
        stdscr.addstr(8, 0, '2: Ascii Album Image (ON/OFF)')
        stdscr.addstr(9, 0, '3: Music Visualizer (ON/OFF)')
        stdscr.addstr(10, 0, '4: Set outpt device')
        stdscr.addstr(11, 0, """5: Initialize/Recreate music databse
        (should be done anytime files in music path are altered)""")
        stdscr.addstr(13, 0, 'q: <- Return')

        stdscr.refresh()

        while True:
            choice = stdscr.getch()

            if choice == ord('1'):
                return self.run_menu(self.set_music_path, stdscr)
            elif choice == ord('2'):
                return self.run_menu(self.edit_bool_setting, 'ascii album image', stdscr)
            elif choice == ord('3'):
                return self.run_menu(self.edit_bool_setting, 'music visualizer', stdscr)
            elif choice == ord('4'):
                pass
            elif choice == ord('5'):
                return self.run_menu(self.create_init_database, stdscr)
            elif choice == ord('q'):
                return self.run_menu(self.main_menu, stdscr)

    def clear_reg_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def create_init_database(self, stdscr):
        stdscr.clear()

        stdscr.addstr(0, 0, self.banner_logo)
        stdscr.addstr(7, 0, 'This process goes through all files in set root directory and processes them')
        stdscr.addstr(8, 0, 'This should be done if never done before, or if files have been altered')
        stdscr.addstr(9, 0, 'This process may take a while depending on disk speed, and the amount of songs')
        stdscr.addstr(10, 0, '(It took me roughly ___ mins on my M1 Mac with ~6500 songs)') #TODO time this process on my laptop
        stdscr.addstr(12, 0, 'enter: start the process')
        stdscr.addstr(13, 0, 'q: <- Return')

        stdscr.refresh()

        num_enters = 0

        while True:
            choice = stdscr.getch()

            if choice == ord('\n'):
                if num_enters >= 1:
                    #stop curses
                    curses.nocbreak()
                    curses.echo()
                    curses.endwin()

                    self.clear_reg_terminal()
                    root_path = self.parse_settings('music_root_path')
                    create_music_info_db(root_path)
                    print('FINISHED')
                    time.sleep(5)
                    self.clear_reg_terminal()

                    #start curses
                    curses.cbreak()
                    curses.noecho()
                    stdscr = curses.initscr()

                    return self.run_menu(self.main_menu, stdscr)
                else:
                    self.settings_pop_up('Press "enter" again to start', 5, 10 + len('Press "enter" again to start'))
                    num_enters += 1
            elif choice == ord('q'):
                return self.run_menu(self.settings, stdscr)

    def settings_pop_up(self, pop_up, height, width):
        window = curses.newwin(height, width, (self.screen_rows - height) // 2, (self.screen_cols - width) // 2)
        window.box()
        window.addstr(height // 2, (width - len(pop_up)) // 2, pop_up)
        window.refresh()
        time.sleep(2.5)
        window.erase()
        window.refresh()
        del window

    def edit_bool_setting(self, settings_key, stdscr): #TODO Add a pop up window that tells user the setting was changed
        stdscr.clear()

        curr_setting = str(self.parse_settings(read_key=settings_key))

        header_phrase = f'The current setting: "{settings_key}" is set to: '

        stdscr.addstr(0, 0, self.banner_logo)
        stdscr.addstr(7, 0, f'{header_phrase}{curr_setting}')
        stdscr.addstr(8, 0, f'T: to enable the {settings_key} in the player')
        stdscr.addstr(9, 0, f'F: to diable the {settings_key} in the player')
        stdscr.addstr(10, 0, 'q: <- Return')

        stdscr.refresh()

        while True:
            choice = stdscr.getch()

            if choice == ord('T'):
                self.parse_settings(read=False, write_key=settings_key, write_value=True)
                stdscr.addstr(7, len(header_phrase), ' ' * len(curr_setting))
                stdscr.addstr(7, len(header_phrase), 'True')
                stdscr.refresh()
                curr_setting = 'True'

                self.settings_pop_up(f'{settings_key} changed to TRUE', 5, 10 + len(settings_key + 'changed to TRUE'))
            elif choice == ord('F'):
                self.parse_settings(read=False, write_key=settings_key, write_value=False)
                stdscr.addstr(7, len(header_phrase), ' ' * len(curr_setting))
                stdscr.addstr(7, len(header_phrase), 'False')
                stdscr.refresh()
                curr_setting = 'False'

                self.settings_pop_up(f'{settings_key} changed to FALSE', 5, 10 + len(settings_key + 'changed to FALSE'))
            elif choice == ord('q'):
                return self.run_menu(self.settings, stdscr)

    def text_box(self, screen_rows, screen_cols):
        curses.curs_set(True)

        height = screen_rows // 5
        width = screen_cols // 5
        outer_window = curses.newwin(height, width, (screen_rows - height) // 2, (screen_cols - width) // 2)
        text_window = curses.newwin(height - 3, width - 4, (screen_rows - height + 4) // 2, (screen_cols - width + 4) // 2)
        text_box = curses.textpad.Textbox(text_window)

        outer_window.addstr(1, 1, 'Enter path here ("ctrl-G" to finish):', curses.A_BOLD)
        outer_window.box()
        outer_window.refresh()

        text_window.refresh()
        text = text_box.edit()

        while '\n' in text: #remove an enter if it was mistakely pressed
            text = text.replace('\n', '')
        while ' ' in text: #remove any spaces that may cuase issues with file path
            text = text.replace(' ', '')

        outer_window.erase()
        text_window.erase()

        outer_window.refresh()
        text_window.refresh()

        curses.curs_set(False)

        return text

    def set_music_path(self, stdscr):
        settings_key = 'music_root_path'

        stdscr.clear()
        screen_rows, screen_cols = stdscr.getmaxyx()
        curr_path = self.parse_settings(settings_key)

        stdscr.addstr(0, 0, self.banner_logo)
        stdscr.addstr(7, 0, '(the path must be the root directory to all playlist folders and music)')
        stdscr.addstr(8, 0, '(there cannot be any spaces in the target directory name)')
        stdscr.addstr(9, 0,"""
Ex.
    -> music
              -song1
              -song2

              ->Playlist1
                            -song1
              ->Playlist2
              ....
              ('music' would be the directory you enter)
""")
        stdscr.addstr(21, 0, f'Current Working Directory is: {os.getcwd()}')
        stdscr.addstr(22, 0, f'Current path: {curr_path}')
        stdscr.addstr(24, 0, 'enter: open textbox')
        stdscr.addstr(25, 0, 'q: <- Return')

        stdscr.refresh()

        while True:
            choice = stdscr.getch()
            if choice == ord('\n'):
                file_path = self.text_box(screen_rows, screen_cols)
                if os.path.isdir(file_path):
                    self.parse_settings(read=False, write_key=settings_key, write_value=file_path)
                    stdscr.addstr(22, len('Current path: '), ' ' * len(curr_path))
                    stdscr.addstr(22, len('Current path: '), file_path)
                    stdscr.refresh()
                    curr_path = file_path
                else:
                    self.settings_pop_up('No directory found at file path', 5, 10 + len('No directory found at file path'))
            elif choice == ord('q'):
                return self.run_menu(self.settings, stdscr)

class create_q:
    def __init__(self, que_type, media, que_len:int):
        self.que_type = que_type
        self.media = media
        self.que_len = que_len

        self.con = sqlite3.connect(DATABASE_PATH)
        self.cur = self.con.cursor()
        self.table_size = self.get_table_size()

    def station(self):
        pass

    def random(self):
        chosen_ids = []
        for i in range(self.que_len):
            id_ = random.randrange(self.table_size)
            while id_ in chosen_ids: #ensure no duplicates
                id_ = random.randrange(self.table_size)

            chosen_ids.append(id_)

        return chosen_ids

    def get_table_size(self):
        #Get the number of data in the provided database table
        count = 0
        id_ = 1
        while True:
            self.cur.execute('SELECT id, song FROM music WHERE id = ?', (id_,))
            if self.cur.fetchone() is None:
                return count

            count += 1
            id_ += 1

class ScrollingWindow:
    def __init__(self, banner_logo:str, data_type:str):
        self.keyboard_buffer = []

        self.con = sqlite3.connect(DATABASE_PATH)
        self.cur = self.con.cursor()

        self.banner_logo = banner_logo
        self.data_type = data_type

    def main(self, stdscr):
        stdscr.clear()
        stdscr.nodelay(0)
        self.screen_rows, self.screen_cols = stdscr.getmaxyx()
        self.empty_rows = self.screen_rows - 10 #remove space for the top and bottom informatio

        initial_data, self.columns, found_data = self.get_song_data([a for a in range(self.empty_rows)])
        self.columns = ['v'] + self.columns #add the cursor column
        self.num_table_rows = self.get_table_size()
        self.col_sizes = self.create_col_size_dist()

        self.top_id, self.bottom_id = self.update_screen(initial_data, found_data, stdscr)

        curses.curs_set(True) #unhide the cursor

        stdscr.move(8, 1) #move curosr into position

        while True:
            curr_y, _ = stdscr.getyx()
            pressed = self.read_keyboard(curr_y, stdscr)

            if pressed == -ord('q'):
                self.keyboard_buffer = []
                return 'q', None
            elif pressed == -ord('\n'):
                self.keyboard_buffer = []
                user_choice, song_data = self.play_selected(stdscr, curr_y)
                if user_choice[0] != 'q':
                    return user_choice, song_data
                pressed = curr_y
            elif pressed == -ord(' '):
                self.keyboard_buffer = []
                return None, None
            elif pressed is None:
                self.move_screen(curr_y, stdscr)

    def move_screen(self, curr_y, stdscr):
        curr_id = curr_y - 8 + self.top_id
        keyboard_buff_str = ''.join(chr(x) for x in self.keyboard_buffer)
        is_j = 'j' in keyboard_buff_str
        is_k = 'k' in keyboard_buff_str

        if is_j or is_k:
            if is_j:
                direction = 1
                nums = keyboard_buff_str.split('j')
                movement = int(nums[0]) if len(nums[0]) > 0 else 1

            else:
                direction = -1
                nums = keyboard_buff_str.split('k')
                movement = int(nums[0]) if len(nums[0]) > 0 else 1

            self.keyboard_buffer = [] #clear the buffer
            next_y = curr_y + (movement * direction)
        else: #user is still entering numbers
            next_y = curr_y

        if next_y < 8 or next_y > (self.screen_rows - 4): #when the user wants to move off the screen
            new_top_id = self.top_id + (movement * direction)
            new_bottom_id = self.bottom_id + (movement * direction)

            if new_top_id < 1:
                new_top_id = 1
                new_bottom_id = self.screen_rows - 3 - 8
            elif new_bottom_id > self.num_table_rows:
                new_top_id = self.num_table_rows - (self.screen_rows - 4 - 8)
                new_bottom_id = self.num_table_rows

            if self.data_type == 'song':
                data_dict, _, found_data = self.get_song_data(range(new_top_id, new_bottom_id + 1))
            else:
                pass #TODO grab unique columns from the database for the provided data type


            self.top_id, self.bottom_id = self.update_screen(data_dict, found_data, stdscr)

            if new_top_id == 1 and curr_id + (movement * direction) < new_top_id:
                next_y = 8
            elif new_bottom_id == self.num_table_rows and curr_id + (movement * direction) > new_bottom_id:
                next_y = self.screen_rows - 4
            elif movement == 1:
                next_y = curr_y
            else:
                next_y = curr_id + (movement * direction) - self.top_id + 8

        stdscr.move(next_y, 1)
        stdscr.refresh()

    def play_selected(self, stdscr, curr_y):
        height = self.screen_rows // 5 * 3
        width = self.screen_cols // 5 * 3
        window = curses.newwin(height, width, (self.screen_rows - height) // 2, (self.screen_cols - width) // 2)
        window.erase()
        window.box()

        song_panel = curses.panel.new_panel(window)
        _, win_width = window.getmaxyx()

        curr_id = (curr_y - 8) + self.top_id
        try:
            match self.data_type:
                case 'song':
                    song_data = self.get_song_data_by_id(curr_id)
                    title = ' SELECTED SONG '
                    window.addstr(1, (width - len(title)) // 2, f'{title}', curses.A_STANDOUT)

                    r = 3
                    for i, info in enumerate(song_data):
                        data_type = self.columns[i + 1]
                        offset = len(data_type)

                        window.addstr(r, 2, f'{data_type}: ', curses.A_BOLD)

                        if offset + 2 + len(str(info)) >= win_width:
                            slice_len = offset + 10 + len(str(info)) - win_width
                            info = info[:-slice_len] + '...'

                        window.addstr(r, 2 + offset + 2, f'{info}')
                        r += 2

                    hint_quit = ' PRESS "q" to QUIT WINDOW '
                    hint_play_station = ' PRESS "s" TO PLAY THIS SONG AND CREATE STATION '
                    hint_play_rand = ' PRESS "r" TO PLAY THIS SONG AND CREATE A RANDOM QUE '
                    hint_play_single = ' PRESS "p" TO PLAY THIS SONG WITHOUT CREATING QUE '

                    window.addstr(height - 5, 2, f'{hint_quit}', curses.A_STANDOUT)
                    window.addstr(height - 5, width - 2 - len(hint_play_station), f'{hint_play_station}', curses.A_STANDOUT)
                    window.addstr(height - 3, 2, f'{hint_play_rand}', curses.A_STANDOUT)
                    window.addstr(height - 3, width - 2 - len(hint_play_single), f'{hint_play_single}', curses.A_STANDOUT)

                    while True:
                        curses.panel.update_panels(); stdscr.refresh()
                        key = stdscr.getch()

                        if key == ord('q'):
                            return 'q', None
                        elif key == ord('p'):
                            return 'p', song_data[1]
                        elif key == ord('s'):
                            return 's', song_data[1]
                        elif key == ord('r'):
                            return 'r', song_data[1]
        except IndexError:
            return

    def read_keyboard(self, curr_y, stdscr):
        key = stdscr.getch()

        if key >= ord('0') and key <= ord('9'): self.keyboard_buffer.append(key)
        elif key == ord('j'): self.keyboard_buffer.append(key)
        elif key == ord('k'): self.keyboard_buffer.append(key)
        elif key == ord('q'): return -ord('q')
        elif key == ord('\n'): return -ord('\n')
        elif key == ord(' '): return -ord(' ')
        else: return curr_y

    def update_screen(self, initial_data, found_data, stdscr):
        stdscr.erase()

        stdscr.addstr(0, 0, self.banner_logo)
        stdscr.addstr(6, 0, '=' * self.screen_cols, curses.A_BOLD)

        for c in range(len(self.columns)):
            prev_width = [self.col_sizes[a] for a in range(c)]
            current_col = sum(prev_width)

            print_val = self.columns[c]
            if print_val == 'v':
                current_col += 1

            stdscr.addstr(7, current_col, f'{print_val}', curses.A_BOLD)

        for r in range(found_data):
            for c in range(len(self.columns) - 1): #skip the 'v' column
                c += 1
                prev_width = [self.col_sizes[a] for a in range(c)]
                current_col = sum(prev_width)

                print_val = '|' + initial_data[self.columns[c]][r]

                if len(print_val) > (self.col_sizes[c]) - 4:
                    len_diff = len(print_val) - self.col_sizes[c]
                    slice_val = -(len_diff + 4) #replace the last 3 with ...
                    print_val = print_val[:slice_val] + '...'

                stdscr.addstr(r + 8, current_col, f'{print_val}')

        quit_hint = ' PRESS "q" TO EXIT '
        play_hint = ' PRESS "Enter" TO PLAY SELECTION '
        search_hint = ' PRESS "Space" TO SEARCH '
        stdscr.addstr(self.screen_rows - 1, self.screen_cols // 4 - len(quit_hint) // 2, f'{quit_hint}', curses.A_STANDOUT)
        stdscr.addstr(self.screen_rows - 1, self.screen_cols // 2 - len(play_hint) // 2, f'{play_hint}', curses.A_STANDOUT)
        stdscr.addstr(self.screen_rows - 1, self.screen_cols // 4 * 3 - len(search_hint) // 2, f'{search_hint}', curses.A_STANDOUT)

        stdscr.refresh()
        return int(initial_data['id'][0]), int(initial_data['id'][found_data - 1])

    def create_col_size_dist(self):
        """ v id   songs        genre > and so on
            _ 1    poop fart    ass shit
        """
        #column 1 is 3 spaces for the cursor placement and spacing
        #column 2 is 10 spaces for up to 999,999 songs and spacing
        #each column after the first gets four spaces of padding on the right

        remaining_cols = self.screen_cols - 13 - (4 * len(self.columns[2:]))#stated above

        ones_vector = np.ones_like(self.columns[2:], dtype=np.int16) #get a vector containing 1s in each element with the same length as the remaining undefined length columns
        remaining_dist = self.soft_max(ones_vector)
        remaining_dist *= remaining_cols #multiply each probablity by the remaining columns that there is a list n elements long where the sum of all the elements add to remaining_cols
        remaining_dist += 4 #add the 4 spaces into ecah

        remaining_dist = np.insert(remaining_dist, 0, [3, 10])

        return [int(a) for a in remaining_dist]

    def soft_max(self, vector):
        """Turn a list of n elements into a probablity distribution between 0 and 1 based on the magnitude of each element"""
        e_vector = np.exp(vector)
        e_vector_sum = sum(e_vector)
        vector = e_vector / e_vector_sum

        return vector

    def get_table_size(self):
        #Get the number of data in the provided database table
        count = 0
        id_ = 1
        while True:
            self.cur.execute('SELECT id, song FROM music WHERE id = ?', (id_,))
            if self.cur.fetchone() is None:
                return count

            count += 1
            id_ += 1

    def get_song_data_by_id(self, id_):
        self.cur.execute('SELECT id, song, playlist, artist, album, genre FROM music WHERE id = ?', (id_,))
        return self.cur.fetchone()

    def get_playlist_data_by_id(self, id_):
        self.cur.execute('SELECT id, playlist FROM music WHERE id = ?', (id_,))
        return self.cur.fetchone()

    def get_song_data(self, id_list:list):
        query = []
        columns = []
        for id_ in id_list:
            cur_fetch = self.get_song_data_by_id(id_)
            if cur_fetch is not None:
                query.append(cur_fetch)
                if not columns:
                    columns = [desc[0] for desc in self.cur.description] #Get the columns from the last query when we know that data was found

        query_dict = {}
        for col in columns:
            query_dict[col] = []

        for tuple_ in query:
            for c, obj in enumerate(tuple_):
                if type(obj) is not str: obj = str(obj)
                key = columns[c]
                query_dict[key].append(obj)

        return query_dict, columns, len(query)

if __name__ == '__main__':
    ui = MainMenu()

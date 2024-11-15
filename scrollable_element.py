import curses, curses.panel
import random
import sqlite3
import math
import json
import numpy as np
import time

class scrolling_window:
    def __init__(self, banner_logo:str, data_tage:str, curses_window):
        """Create a scrollable element in curses for viewing database song entries."""

        #TODO fix data resizing algorithim since it only works when terminal is full screen

        self.con = sqlite3.connect('./music_info_db/music_info_db.db')
        self.cur = self.con.cursor()

        self.banner_logo = banner_logo
        self.main(curses_window)
        #curses.wrapper(self.main)

    def main(self, stdscr):
        #Clear screen and get size data
        stdscr.clear()
        stdscr.nodelay(1)

        screen_rows, screen_cols = stdscr.getmaxyx()
        self.screen_cols = screen_cols
        self.screen_rows = screen_rows
        empty_rows = screen_rows - 10 #for the top and bottom borders

        initial_songs, self.columns, found_songs = self.get_data([a for a in range(empty_rows)]) #try and get as many songs from db that will fit on the screen
        self.columns = ['v'] + self.columns #add the marker for the cursor selector

        self.num_table_rows = self.get_table_size()

        self.longest_str_per_col = []

        for c in range(len(self.columns)):
            if self.columns[c] is not 'v':
                data_col = initial_songs[self.columns[c]]
                len_list = [len(obj) for obj in data_col]
                longest = max(len_list)
            else:
                longest = 1

            self.longest_str_per_col.append(longest)

        longest_row = sum(self.longest_str_per_col) + (6 * 4) #add 4 spaces per column to data
        if longest_row > screen_cols:
            self.longest_str_per_col = self.adjust_data_len(longest_row - screen_cols)

        self.top_id, self.bottom_id = self.update_screen(initial_songs, found_songs, stdscr)

        stdscr.move(8, 1) #place cursor on the first data line

        while True:
           curr_y, _ = stdscr.getyx()
           next_y = self.get_next_direction(curr_y, stdscr)

           if next_y == -113:
               return 'q'
           elif next_y == -115:
               user_choice = self.play_selected_song(stdscr, curr_y)

               if user_choice[0] != 'q':
                   return user_choice

               next_y = curr_y
           elif next_y > (screen_rows - 4):
               self.check_down(found_songs, stdscr)
               next_y = curr_y
           elif next_y < 8: #The row containing first data line on screen
               self.check_up(stdscr)
               next_y = curr_y

           stdscr.move(next_y, 1)
           stdscr.refresh()

    def check_up(self, stdscr):
        if self.top_id > 1:
            song_dict, _, found_songs = self.get_data(range(self.top_id - 1, self.bottom_id))
            self.top_id, self.bottom_id = self.update_screen(song_dict, found_songs, stdscr)

    def check_down(self, found_songs, stdscr):
        if self.bottom_id < self.num_table_rows:
            song_dict, _, found_songs = self.get_data(range(self.top_id + 1, self.bottom_id + 2))
            self.top_id, self.bottom_id = self.update_screen(song_dict, found_songs, stdscr)

    def get_table_size(self):
        count = 0
        id = 1

        while True:
            self.cur.execute('SELECT id, song FROM music WHERE id = ?', (id,))
            if self.cur.fetchone() is None:
                 return count

            count += 1
            id += 1

    def get_data(self, ids_list:list):
        query = []
        columns = []
        for id in ids_list:
            cur_fetch = self.get_song_data_by_id(id)

            if cur_fetch is not None:
               query.append(cur_fetch)
               if not columns:
                  columns = [desc[0] for desc in self.cur.description]

        songs_found = len(query)
        query_dict = {'id': [], 'song': [], 'playlist': [], 'artist': [], 'album': [], 'genre': []}

        for tuple in query:
           for c, obj in enumerate(tuple):
              if type(obj) is not str: obj = str(obj)
              key = columns[c]
              query_dict[key].append(obj)

        return query_dict, columns, len(query)

    def update_screen(self, song_dict, found_songs, stdscr):
        stdscr.erase()

        stdscr.addstr(0, 0, self.banner_logo) #6 rows tall
        stdscr.addstr(6, 0, '=' * self.screen_cols, curses.A_BOLD) #1 row tall

        for c in range(len(self.columns)):
            prev_col_widths = [self.longest_str_per_col[a] for a in range(c)]
            current_col = sum(prev_col_widths) + (c * 4) + 4

            print_val = self.columns[c]

            stdscr.addstr(7, current_col, f'{print_val}', curses.A_BOLD)

        for r in range(found_songs):
            for c in range(len(self.columns) - 1): #Skip the 'v' at the begining
                c += 1
                prev_col_widths = [self.longest_str_per_col[a] for a in range(c)]
                current_col = sum(prev_col_widths) + (c * 4) + 4
                print_val = song_dict[self.columns[c]][r]

                if len(print_val) > (self.longest_str_per_col[c]) and c > 0:
                   len_diff = len(print_val) - self.longest_str_per_col[c]
                   slice_val = -(len_diff + 4)
                   print_val = print_val[:slice_val] + '...'

                if c > 0:
                   print_val = '|' + print_val

                stdscr.addstr(r + 8, current_col, f'{print_val}')

        quit_hint = ' PRESS "q" TO EXIT '
        play_hint = ' PRESS "Enter" TO PLAY SELECTION '
        search_hint = ' PRESS "Space" TO SEARCH '
        stdscr.addstr(self.screen_rows - 1, int(self.screen_cols / 4) - int(len(quit_hint) / 2), f'{quit_hint}', curses.A_STANDOUT)
        stdscr.addstr(self.screen_rows - 1, int(self.screen_cols / 2) - int(len(play_hint) / 2), f'{play_hint}', curses.A_STANDOUT)
        stdscr.addstr(self.screen_rows - 1, int(self.screen_cols / 4 * 3) - int(len(search_hint) / 2), f'{search_hint}', curses.A_STANDOUT)

        stdscr.refresh()
        return int(song_dict['id'][0]), int(song_dict['id'][found_songs - 1])

    def play_selected_song(self, stdscr, curr_y):
      height = self.screen_rows // 3
      width = self.screen_cols // 3
      song_win = curses.newwin(height, width, height, width)
      song_win.erase()
      song_win.box()

      song_panel = curses.panel.new_panel(song_win)
      _, win_width = song_win.getmaxyx()


      curr_id = (curr_y - 8) + self.top_id
      try:
          song_data = self.get_song_data_by_id(curr_id)
      except IndexError:
          return

      title = ' SELECTED SONG: '
      song_win.addstr(1, (width - len(title)) // 2, f'{title}', curses.A_STANDOUT)

      #Print the information and the titles
      r = 3
      for i, info in enumerate(song_data):
          data_type = self.columns[i]
          offset = len(data_type)

          song_win.addstr(r, 2, f'{data_type}: ', curses.A_BOLD)

          if offset + 2 + len(str(info)) >= win_width:
              new_len = offset + 10 + len(str(info)) - win_width
              info = info[:-new_len] + '...'

          song_win.addstr(r, 2 + offset + 2, f'{info}')
          r += 2
      #

      hint_quit = ' PRESS "q" TO QUIT WINDOW '
      hint_play_station = ' PRESS "s" TO PLAY THIS SONG AND CREATE STATION '
      hint_play_rand = ' PRESS "r" TO PLAY THIS SONG AND CREATE A RANDOM Q '
      hint_play_single = ' PRESS "p" TO PLAY THIS SONG WIHTOUT CREATING Q '

      song_win.addstr(height - 5, 2, f'{hint_quit}', curses.A_STANDOUT)
      song_win.addstr(height - 5, width - 2 - len(hint_play_station), f'{hint_play_station}', curses.A_STANDOUT)
      song_win.addstr(height - 3, 2, f'{hint_play_rand}', curses.A_STANDOUT)
      song_win.addstr(height - 3, width - 2 - len(hint_play_single), f'{hint_play_single}', curses.A_STANDOUT)


      while True:
          curses.panel.update_panels(); stdscr.refresh()
          char = stdscr.getch()

          if char == 113: #q
              return 'q', ' '
          elif char == 112: #p
              return 'p', song_data[1]
          elif char == 115: #s
              return 's', song_data[1]
          elif char == 114: #r
              return 'r', song_data[1]

    def get_song_data_by_id(self, song_id):
        self.cur.execute('SELECT id, song, playlist, artist, album, genre FROM music WHERE id = ?', (song_id,))

        return self.cur.fetchone()

    def get_next_direction(self, curr_y, stdscr):
        char = stdscr.getch()
        if char == curses.KEY_UP: return curr_y - 1
        elif char == curses.KEY_DOWN: return curr_y + 1
        elif char == 113: return -113 #q
        elif char == curses.KEY_ENTER or char == 10 or char == 13: return -115
        else: return curr_y

    def adjust_data_len(self, len_diff:int):
        data_range = max(self.longest_str_per_col) - min(self.longest_str_per_col)
        mean = sum(self.longest_str_per_col) / len(self.longest_str_per_col)
        normalized_lengths = []

        for length in self.longest_str_per_col:
            norm = (length - mean)/data_range
            if norm < 0: norm = 0
            normalized_lengths.append(norm)

        non_zero_weights = []
        non_zero_indexs = []
        for i in range(len(normalized_lengths)):
            if normalized_lengths[i] > 0:
                non_zero_weights.append(normalized_lengths[i])
                non_zero_indexs.append(i)

        non_zero_weights = self.soft_max(non_zero_weights, (self.screen_cols / 10))
        for i in range(len(non_zero_indexs)):
            normalized_lengths[non_zero_indexs[i]] = non_zero_weights[i]

        new_list = []

        for i in range(len(self.longest_str_per_col)):
            val = self.longest_str_per_col[i]
            weight = normalized_lengths[i]
            new_val = int(val - (len_diff * weight))
            new_list.append(new_val)

        return new_list

    def soft_max(self, weights, b):
        weights = [w * math.log(b) for w in weights]
        e_weights = np.exp(weights)
        e_weights_sum = sum(e_weights)
        return e_weights / e_weights_sum
                longest = 1

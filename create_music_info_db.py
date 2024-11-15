import os
import glob
import sqlite3
import time
from music_backend import create_music_backend

class create_music_info_db:
    """Create tables in a db per playlist with each song listed and its info"""
    def __init__(self, music_root_path:str):
        print('IF YOU NEED TO STOP THE PROCESS PRESS CTRL-C AND WAIT FOR IT TO SAFELY SHUTDOWN')
        time.sleep(5)
        print('Starting...')
        time.sleep(1)

        all_songs = self.create_song_list(music_root_path) #TODO change to allow songs not in playlist files but also just in root dir

        con = sqlite3.connect('./music_info_db/music_info_db.db') #TODO change to .music_info_db
        cur = con.cursor()
        cur.execute(f'CREATE TABLE IF NOT EXISTS music (id INTEGER PRIMARY KEY AUTOINCREMENT, song STRING UNIQUE, artist STRING, album STRING, playlist STRING, genre STRING, path STRING)')

        #Create database containing all of the the info on the songs.
        for playlist in all_songs.keys():
            print('Getting playlist information...')
            playlist_title = self.get_playlist_title_from_path(playlist)
            print(f'Gathering songs from {playlist_title}')

            metadata_list = self.create_metadata_list_by_playlist(all_songs[playlist])
            print('Inserting data into database...\n')
            for song in metadata_list.keys():
                artist = metadata_list[song][0]
                album = metadata_list[song][1][0]
                genre = metadata_list[song][2][0]
                path = metadata_list[song][3]

                try:
                    cur.execute(f'INSERT INTO music (song, artist, album, playlist, genre, path) VALUES(?, ?, ?, ?, ?, ?)', (song, artist, album, playlist_title, genre, path))
                    con.commit()
                except sqlite3.IntegrityError:
                    print(f'{song} is already present in databse, skipping..')
            print('=' * 50)

        con.close()

    def get_playlist_title_from_path(self, path):
        path = path.split('/')
        title = path[len(path) - 1]

        return title

    def create_song_list(self, root_path:str):
        """Create a dict of all songs in each playlist with each key as the playlist"""
        root_path = os.path.join(root_path, '*')
        playlist_list = glob.glob(root_path)

        if len(playlist_list) == 0:
            raise RuntimeError(f"No playlist files found at {root_path}")
        else:
            print('=' * 50)
            print('Files Found:')
            for file in playlist_list:
                playlist_name = file.split('/')
                file_name = playlist_name[len(playlist_name) - 1]
                print(file_name)
            print('=' * 50)

        song_list = {}
        for playlist in playlist_list:
            song_list[playlist] = glob.glob(os.path.join(playlist, '*.mp3'))

        return song_list

    def create_metadata_list_by_playlist(self, song_list:list):
        """Create a dict of all songs and their genre"""
        genre_list = {}

        for song in song_list:
            backend = create_music_backend()
            backend.init_song(path=song, open_stream=False)
            metadata = backend.get_song_metadata()
            song_name = backend.song_name
            genre_list[song_name] = [metadata['Artist'], metadata['Album'], metadata['Genre'], backend.file_name]
            backend.delete_temp_file()

        return genre_list

if __name__ == '__main__':
    create_music_info_db('/Users/dylenthomas/Documents/VISUALSTUDIOCODE/SPOTIFYCLI/downloads')

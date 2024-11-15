import sqlite3
from gensim.models import KeyedVectors

def similarity_que():

    con = sqlite3.connect('./music_info_db/music_info_db.db')
    cur = con.cursor()
    #Grab the songs that have a genre tag contianing a genre from the current song

    genre = 'australian rock_hard rock_rock_'
    genre_list = genre.split('_')
    genre_list = genre_list[0:len(genre_list) - 1]  
    for genre in genre_list:
        cur.execute('SELECT song FROM "This Is ZZ Top" WHERE genre LIKE ?', ('%'+genre+'%',))

    #Then compute cosine similarity between the current song and the songs collected and then choose the next song based on that similarity.

    wv = KeyedVectors.load('word2vec.wordvectors', mmap='r')
    similar = wv.most_similar(genre_list[1], topn=5)
    print(wv.index_to_key)
    print(similar)
        
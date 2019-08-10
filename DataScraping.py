import re
import json
import spotipy
import twitter
import pandas as pd
from os import chdir
from urllib import request
import lyricsgenius as genius
from googlesearch import search
from bs4 import BeautifulSoup as soup
from spotipy.oauth2 import SpotifyClientCredentials


chdir('/Users/justinpimentel/Desktop/Projects/Lizzo/Data')
client_credentials_manager = SpotifyClientCredentials(client_id="6c06af78e6d34ceabbe8dcd0249ce2af",
                                                      client_secret="24bd3827b5e24e5cb06794b867fb3252")
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

lizzoSpotifyID = sp.search(q = 'Lizzo', type = 'artist', limit = 1)['artists']['items'][0]['id']
lizzoSpotify = sp.artist(lizzoSpotifyID)

########################
## ALBUMS DATASET ######
########################
album_ids = [sp.artist_albums(lizzoSpotify['id'])['items'][i]['id'] for i in [0,3,4,11]]
albumsInfo = pd.DataFrame()

for album in album_ids:
    tempInfo = sp.album(album)
    temp = pd.DataFrame({'Album Name': [tempInfo['name']],
                         'Release Date': [tempInfo['release_date']],
                         'Popularity': [tempInfo['popularity']],
                         'Num Tracks': [tempInfo['total_tracks']],
                         'Album Cover': [tempInfo['images'][0]['url']],
                         'Label': [tempInfo['label']],
                         'ID':[tempInfo['id']]
            })
    albumsInfo = pd.concat([albumsInfo, temp])

albumsInfo.reset_index(drop = True).to_csv('Albums.csv',index = False)

########################
## SONGS DATASET #######
########################
api = genius.Genius("yqcXyNyQu8674pRrP9gHnoeVo2INGemYkhMDwpft5L3mvDfAoy76kafw8XmWz-kH", 
                    verbose = False, remove_section_headers = True)

songsInfo = pd.DataFrame()
for albumName in albumsInfo['Album Name']:
    album = sp.album(albumsInfo.loc[albumsInfo['Album Name'] == albumName,'ID'][0])
    for song in range(album['total_tracks']):
        audioFeatures = sp.audio_features(album['tracks']['items'][song]['id'])[0]
        temp = pd.DataFrame({'Album': albumName,
                             'Track Num': [album['tracks']['items'][song]['track_number']],
                             'Song': [album['tracks']['items'][song]['name']],
                             'Popularity': [sp.track(album['tracks']['items'][song]['id'])['popularity']],
                             'Lyrics': [api.search_song(album['tracks']['items'][song]['name'], artist = 'Lizzo').lyrics],
                             'Duration (s)': [audioFeatures['duration_ms']/1000],
                             'Acousticness': [audioFeatures['acousticness']],
                             'Danceability': [audioFeatures['danceability']],
                             'Energy': [audioFeatures['energy']],
                             'Instrumentalness': [audioFeatures['instrumentalness']],
                             'Key': [audioFeatures['key']],
                             'Liveness': [audioFeatures['liveness']],
                             'Loudness': [audioFeatures['loudness']],
                             'Mode': [audioFeatures['mode']],
                             'Speechiness': [audioFeatures['speechiness']],
                             'Tempo': [audioFeatures['tempo']],
                             'Time Signature': [audioFeatures['time_signature']],
                             'Valence': [audioFeatures['valence']]
                             })
        songsInfo = pd.concat([songsInfo, temp])

songsInfo.reset_index(drop = True).to_csv('Songs.csv',index = False)

##############################
## SOCIAL MEDIA DATASET ######
##############################

twitterApi = twitter.Api(consumer_key = 'DIEZciMCD3Ja2y45mf6GlRWPX',
				  consumer_secret = 'jbfKS4oNccmFlQTK2nNVPlirzhLf3sIt7DvVmFcxHvq7DAfd5L',
				  access_token_key = '2598747789-B3D3nYYZ89M5cSUZvohiGrvXzXWtYrpK8ot7Thj',
				  access_token_secret = 'dCqtZN81Emt0W9nCLzwfuFQfzx5SjepoAWTT3ycStmLRH',
                  sleep_on_rate_limit = True)

twitterID = twitterApi.GetUsersSearch(term = 'Lizzo')[0].id
lizzoTwitter = twitterApi.GetUser(twitterID)
socialMediaInfo = pd.DataFrame()

socialMediaInfo.loc[0,'Platform'] = 'Twitter'
socialMediaInfo.loc[0,'Username'] = lizzoTwitter.screen_name
socialMediaInfo.loc[0,'Followers'] = lizzoTwitter.followers_count

socialMediaInfo.loc[1,'Platform'] = 'Spotify'
socialMediaInfo.loc[1,'Username'] = lizzoSpotify['name']
socialMediaInfo.loc[1,'Followers'] = lizzoSpotify['followers']['total']

instagramURL = pd.Series(search('Lizzo instagram', num = 1, stop = 1, pause = 2))[0]
subsetURL = instagramURL[26:]

client = request.urlopen(instagramURL)
response = client.read()
page_soup = soup(response).html.find('script', text = re.compile('window\._sharedData'))
jsonSoup = json.loads(page_soup.string.partition('=')[-1].strip(' ;'))
client.close()

socialMediaInfo.loc[2,'Platform'] = 'Instagram'
socialMediaInfo.loc[2,'Username'] = subsetURL[:subsetURL.find('/')]
socialMediaInfo.loc[2,'Followers'] = jsonSoup['entry_data']['ProfilePage'][0]['graphql']['user']['edge_followed_by']['count']

socialMediaInfo.reset_index(drop = True).to_csv('Social.csv',index = False)


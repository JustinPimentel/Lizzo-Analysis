import re
import json
import spotipy
import twitter
import requests
import numpy as np
import pandas as pd
from os import chdir
from googlesearch import search
from bs4 import BeautifulSoup as soup
from spotipy.oauth2 import SpotifyClientCredentials

##########################
## APIs & Functions ######
##########################

def getWebsite(URL):
    return soup(requests.get(url = URL,headers = {'User-Agent': 'Mozilla/5.0'}).text)

def tempoNormalizer(value):
    return (value - minTempo)/(maxTempo - minTempo)

def noFeatorAnd(string):
    string = re.sub('And','&',string)
    return re.sub('\(.*\)','',string).strip()

chdir('/Users/justinpimentel/Desktop/Projects/Lizzo/Data')
client_credentials_manager = SpotifyClientCredentials(client_id="6c06af78e6d34ceabbe8dcd0249ce2af",
                                                      client_secret="24bd3827b5e24e5cb06794b867fb3252")
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

twitterApi = twitter.Api(consumer_key = 'DIEZciMCD3Ja2y45mf6GlRWPX',
				  consumer_secret = 'jbfKS4oNccmFlQTK2nNVPlirzhLf3sIt7DvVmFcxHvq7DAfd5L',
				  access_token_key = '2598747789-B3D3nYYZ89M5cSUZvohiGrvXzXWtYrpK8ot7Thj',
				  access_token_secret = 'dCqtZN81Emt0W9nCLzwfuFQfzx5SjepoAWTT3ycStmLRH',
                  sleep_on_rate_limit = True)

########################
## ALBUMS DATASET ######
########################

lizzoSpotifyID = sp.search(q = 'Lizzo', type = 'artist', limit = 1)['artists']['items'][0]['id']
lizzoSpotify = sp.artist(lizzoSpotifyID)

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

albumsInfo = albumsInfo.reset_index(drop = True)

########################
## SONGS DATASET #######
########################

songsInfo = pd.DataFrame()
for albumName in albumsInfo['Album Name']:
    album = sp.album(albumsInfo.loc[albumsInfo['Album Name'] == albumName,'ID'].values[0])
    for song in range(album['total_tracks']):
            songID = album['tracks']['items'][song]['id']
            audioFeatures = sp.audio_features(songID)[0]
            temp = pd.DataFrame({'Album': albumName,
                                 'Track Num': [album['tracks']['items'][song]['track_number']],
                                 'Song': [album['tracks']['items'][song]['name']],
                                 'Popularity': [sp.track(album['tracks']['items'][song]['id'])['popularity']],
                                 'Duration (s)': [audioFeatures['duration_ms']/1000],
                                 'Danceability': [audioFeatures['danceability']],
                                 'Energy': [audioFeatures['energy']],
                                 'Tempo': [audioFeatures['tempo']],
                                 'Valence': [audioFeatures['valence']],
                                 'Embed URL': 'https://open.spotify.com/embed/track/' + str(sp.track(songID)['id'])
                                 })
            songRIAA = temp['Song'][0]
            temp['Center'] = 0
            temp['RIAA'] = 1 if ((songRIAA == 'Juice') or (songRIAA == 'Good as Hell')) else 2 if (songRIAA == 'Truth Hurts') else 0
            songsInfo = pd.concat([songsInfo, temp])

songsInfo['Normalized Tempo'] = songsInfo['Tempo'].apply(tempoNormalizer)
songsInfo = songsInfo.reset_index(drop = True)
songsInfo.to_csv('Songs.csv',index = False)


## Petal Plot Dataset ##

maxTempo = np.max(songsInfo['Tempo'])
minTempo = np.min(songsInfo['Tempo'])

petalPlot = pd.melt(songsInfo, id_vars = ['Album','Song','Popularity','Tempo','RIAA','Embed URL'], value_vars = ['Normalized Tempo','Valence', 'Danceability','Energy','Center']).sort_values(['Album','Song'])
petalPlot['Song'] = petalPlot['Song'].apply(noFeatorAnd)
petalPlot.reset_index(drop = True).to_csv('PetalPlot.csv', index = False)
##############################
## SOCIAL MEDIA DATASET ######
##############################

instagramURL = pd.Series(search('Lizzo instagram', num = 1, stop = 1, pause = 2))[0]
subsetURL = instagramURL[26:]
igRaw = getWebsite(instagramURL).html.find('script', text = re.compile('window\._sharedData')).text
igJson = json.loads(igRaw.partition('=')[-1].strip(' ;'))

twitterID = twitterApi.GetUsersSearch(term = 'Lizzo')[0].id
lizzoTwitter = twitterApi.GetUser(twitterID)



socialMediaInfo = pd.DataFrame()

socialMediaInfo.loc[0,'Platform'] = 'Twitter'
socialMediaInfo.loc[0,'Username'] = lizzoTwitter.screen_name
socialMediaInfo.loc[0,'Followers'] = lizzoTwitter.followers_count

socialMediaInfo.loc[1,'Platform'] = 'Spotify'
socialMediaInfo.loc[1,'Username'] = lizzoSpotify['name']
socialMediaInfo.loc[1,'Followers'] = lizzoSpotify['followers']['total']


socialMediaInfo.loc[2,'Platform'] = 'Instagram'
socialMediaInfo.loc[2,'Username'] = subsetURL[:subsetURL.find('/')]
socialMediaInfo.loc[2,'Followers'] = igJson['entry_data']['ProfilePage'][0]['graphql']['user']['edge_followed_by']['count']

socialMediaInfo = socialMediaInfo.reset_index(drop = True)
socialMediaInfo.to_csv('Social.csv',index = False)

##############################
## ALBUM DATASET ADDITIONS ###
##############################

for albumName in albumsInfo['Album Name']:
    albumsInfo.loc[albumsInfo['Album Name'] == albumName, 'Avg. Valence'] = np.mean(songsInfo.loc[songsInfo['Album'] == albumName,'Valence'])
    albumsInfo.loc[albumsInfo['Album Name'] == albumName, 'Duration (s)'] = np.sum(songsInfo.loc[songsInfo['Album'] == albumName,'Duration (s)'])

albumsInfo.to_csv('Albums.csv',index = False)

###############################
## BILLBOARD TOP !00 SCRAPE ###
###############################

regex = re.compile('[fF]eaturing|&|(?<!Tyler),(?!The Creator)|(?<=Pedro Capo) X (?=Farruko)')

artistsRaw = getWebsite('https://www.billboard.com/charts/hot-100').html.findAll('div',{'class':'chart-list-item__artist'})
artistsList = [artist.text for artist in artistsRaw]
artistsClean = pd.Series(sum([re.split(regex, song) for song in artistsList],[])).str.strip().drop_duplicates()

artistsInfo = pd.DataFrame({'Name': artistsClean})
artistsInfo['Popularity'] = [sp.search(q = artist, limit = 1, type = 'artist')['artists']['items'][0]['popularity'] for artist in artistsInfo['Name']]

artistsInfo.to_csv('Artists.csv',index = False)


import re, os, sys
from func.basics import *
import importlib
import time, ciso8601, pytz
from datetime import datetime
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',

    handlers=[logging.FileHandler('log.txt'), logging.StreamHandler()],

    level=logging.INFO)

LOGGER = logging.getLogger(__name__)


## blu


def blutv(c,episodes):

    for m in range(len(c)):
        not_in = str(c[m]["episodeNumber"]) not in episodes
        if not_in == True: 
            episodes.append(str(c[m]["episodeNumber"]))

    return episodes


## trt

def trt(c,episodes):

    for m in range(len(c)):
        if str(c[m]["episode"]) not in episodes:
            episodes.append(str(c[m]["episode"]))
    
    return episodes


## trt_audio


def trtaudio(c,episodes):

    for m in range(len(c)):
        if str(c[m]["episodeNo"]) not in episodes:
            episodes.append(str(c[m]["episodeNo"]))
    
    return episodes

## tvplus


def tvplus(c,episodes):

    for m in range(len(c)):
        if c[m]["sitcomnum"] not in episodes:
         episodes.append(c[m]["sitcomnum"])
    return episodes

## trt_audio

def dsmartgo(c,episodes):

    for m in range(len(c)):
        me = c[m]["Metadata"]
        for t in range(len(me)):
            if me[t]["NameSpace"] == "episode_number" and\
            me[t]["Value"].lstrip("0") not in episodes:
                episodes.append(me[t]["Value"].lstrip("0"))
    return episodes

## exxen


def exxen(c,episodes):

    for m in range(len(c)):
        me = c[m]["Metadata"]
        for t in range(len(me)):
            if me[t]["NameSpace"] == "episode_no_in_season" and\
            me[t]["Value"].lstrip("0") not in episodes:
                episodes.append(me[t]["Value"].lstrip("0"))
    return episodes


def beinturkey(c,episodes):

    for m in range(len(c)):
        episodes.append(str(c[m]["episodeNo"]))
    return episodes

def todturkey(c,episodes):

    for m in range(len(c)):
        episodes.append(str(c[m]["episodeNo"]))
    return episodes

## gain


def gain(c,episodes):

    for t in range(len(c)):
        if c[t]["episodeNumber"] not in episodes and c[t]["episodeNumber"] != 0:
            episodes.append(str(c[t]["episodeNumber"]))
    return episodes


## fox


def fox(c,episodes):

    for t in range(len(c)):
        if c[t]["no"] not in episodes:
            episodes.append(c[t]["no"])
            
    return episodes

## claro

def claro(c,episodes):

    for t in range(len(c)):
        if c[t]["episode_number"] not in episodes:
            episodes.append(c[t]["episode_number"])
            
    return episodes

## disney

def disneyplus(c,episodes):

    for t in range(len(c)):
        if str(c[t]["episodeSequenceNumber"]) not in episodes:
            episodes.append(str(c[t]["episodeSequenceNumber"]))
            
    return episodes

## kablotv

def kablotv(c,episodes):

    for t in range(len(c)):
        if str(c[t]["EpisodeNo"]) not in episodes:
            episodes.append(str(c[t]["EpisodeNo"]))
            
    return episodes

## hbo

def hbomax(c,episodes):

    for t in range(len(c)):
        if str(c[t]["numberInSeason"]) not in episodes:
            episodes.append(str(c[t]["numberInSeason"]))
            
    return episodes

## hulu

def hulu(c,episodes):

    for t in range(len(c)):
        
        air_date = c[t]["premiere_date"]
        now_date = datetime.utcnow()

        if "availability" in c[t]["bundle"] and "start_date" in c[t]["bundle"]["availability"]:
            air_date = c[t]["bundle"]["availability"]["start_date"]

        if air_date.endswith("Z") == False:
            now_date = now_date.astimezone(pytz.timezone('US/Eastern'))

        air_date = ciso8601.parse_datetime(air_date)
        now_ts = now_date.timestamp()
        air_ts = air_date.timestamp()

        if air_ts > now_ts:
            continue

        if str(c[t]["number"]) not in episodes:
            episodes.append(str(c[t]["number"]))
            
    return episodes

def kanald(c,episodes):

    for t in range(len(c)):
        if str(c[t]["episode"]) not in episodes:
            episodes.append(str(c[t]["episode"]))
            
    return episodes

def puhu(c,episodes):

    for t in range(len(c)):
        LOGGER.info(c[t])
        if c[t]["meta"]["position"] not in episodes:
            episodes.append(c[t]["meta"]["position"])
       
    return episodes  

def fubotv(c,episodes):

    for t in range(len(c)):
        if "episodeNumber" in c[t]["metadata"] and str(c[t]["metadata"]["episodeNumber"]) not in episodes:
            episodes.append(str(c[t]["metadata"]["episodeNumber"]))
   
    return episodes 

#############


def masterclass(c,episodes):

    for t in range(len(c)):
        if str(c[t]["number"]) not in episodes:
            episodes.append(str(c[t]["number"]))
    return episodes  

def udacity(c,episodes):

    for t in range(len(c)):
        episodes.append(str(t+1))
    return episodes  


def edx(c,episodes):

    for t in range(len(c)):
        episodes.append(str(t+1))
    return episodes  



def alls(platform, last_episodes, season, content_information):

    episodes = []
    c = content_information["content"]

    episodes = eval(platform)(c,episodes)

    if last_episodes != 0:
        episodes_x = natural_sort(episodes)
        episodes = []
        for i in range(last_episodes):
            try:
                episodes.append(episodes_x[-i - 1])
            except:
                break

    episodes = natural_sort(episodes)
    return episodes

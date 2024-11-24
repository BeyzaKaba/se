import re, subprocess, json, platform
from datetime import datetime
from iso639 import languages
from pathlib import Path
from functools import partial
from io import DEFAULT_BUFFER_SIZE
import base64
from slugify import slugify
import ipinfo
import requests
import configparser
import time
from func.messages import *
from pinata_python.pinning import Pinning
import os

config = configparser.ConfigParser()
config.read('data/tokens/config.ini')

## Useful Functions


def natural_sort(l):
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(l, key=alphanum_key)

def chapter_timer(time, time_type):

    if time_type == "second":
        chapter_hour = int(time) // 3600
        chapter_minute = (int(time) - chapter_hour * 3600) // 60
        chapter_second = int(time) - chapter_hour * 3600 - chapter_minute * 60

    chapter_outputs = [chapter_hour, chapter_minute, chapter_second]

    for i in range(len(chapter_outputs)):
        if chapter_outputs[i] < 10:
            chapter_outputs[i] = "0" + str(chapter_outputs[i])
        else:
            chapter_outputs[i] = str(chapter_outputs[i])

    time = ':'.join(chapter_outputs)
    return time

def split_episodes(episodes):
    if "," in episodes:
        episodes = episodes.split(",")
    elif "-" in episodes:
        first_episode = int(episodes.split("-")[0])
        last_episode = int(episodes.split("-")[1]) + 1
        episodes = list(map(str, range(first_episode, last_episode)))

    if type(episodes) == str:
        episodes = episodes.split()
    episodes = natural_sort(episodes)
    return episodes

def category_translate(value):
    
    available = 0
    value = slugify(value)

    with open("data/extras/dictionary.json") as f:
        dic = json.loads(f.read())

    origin = []
    translates = []
    for items in dic:
        translates.append(slugify(items["translate"]))

    if value in translates:
        available = 1
        value = value.title()
    else:
        for items in dic:
            if items["origin"] in value:
                available = 1
                value = items["translate"]

    if available == 0:
        print("[warning] No translate for " + value)

    return value


def expire_date(date):

    ## tvplus and bein currently

    if type(date) != int:
        ## blu format to main
        date = date.replace("T","").replace("-","").replace("Z","")
        date = date.replace(":","")
        
        ## bein format to main
        if '.' in date:
            dates = date.split('.')
            date = dates[-1]+dates[1]+ dates[2] 
            date = date + '000000'

        end_time = datetime(year=int(date[:4]),
                            month=int(date[4:6]),
                            day=int(date[6:8]),
                            hour=int(date[8:10]),
                            minute=int(date[10:12]),
                            second=int(date[12:14]))
        expire_timestamp = int(end_time.timestamp())
    else:
        expire_timestamp = date
    remaining_timestamp = expire_timestamp - datetime.utcnow().timestamp()
    remaining_days = str(remaining_timestamp / 86400).split(".")[0] + " Days"
    remaining_hours = str(remaining_timestamp / 3600).split(".")[0] + " Hours"
    remaining_minutes = str(
        remaining_timestamp / 60).split(".")[0] + " Minutes"
    remaining_seconds = str(
        remaining_timestamp).split(".")[0] + " Seconds"

    remaining_types = [remaining_days, remaining_hours, remaining_minutes, remaining_seconds]

    for items in remaining_types:
        if items.startswith("0") == False:
            remaining = items
            break

    if int(remaining.split(" ")[0]) == 1:
        remaining = remaining[:-1]

    return remaining

def add_results(result_title, add_info, platform):

    if add_info.startswith(", "):
        add_info = add_info[2:]

    if add_info != "":
        add_info = " | " + add_info

    add_spaces = 40 - len(result_title)
    add_info_spaces = 40 - len(add_info)
    add_platform_spaces = 10 - len(platform)

    if add_info_spaces < 0:
        add_info = add_info[:add_info_spaces - 3] + "..."
    else:
        for t in range(add_info_spaces):
            add_info = add_info + " "

    if add_spaces < 0:
        result_title = result_title[:add_spaces - 3] + "..."
    else:
        for t in range(add_spaces):
            result_title = result_title + " "

    for t in range(add_platform_spaces):
        platform = platform + " "

    result = result_title + add_info + " | " + platform
    return result

def print_title(season, episode, title, content_type):
    if content_type == "multiple":
        if int(episode) < 10:
            episode_display = "0" + episode
        else:
            episode_display = episode
        print("Download for " + title + " S0" + season + "E" +
              episode_display + " is starting")
    elif content_type == "single":
        print("Download for " + title + " is starting")


def tmpupload(loc):
    file = loc
    url = 'https://tmpfiles.org/api/v1/upload'
    files = {'file': open(file, 'rb')}

    r = requests.post(url, files=files).json()
    if r["status"] == "success":
        url1 = r["data"]["url"]
        urson = url1.split("https://tmpfiles.org/")[1]
        url = "https://tmpfiles.org/dl/" + urson

    return url

def media_info(video_file):
    command = [
    "ffprobe",
    '-i',
    video_file,
    "-print_format",'json',
    '-show_format',
    '-show_streams']
    command = subprocess.run(command, capture_output=True)
    video_stream_info = json.loads(command.stdout)

    return video_stream_info

def get_resolution(video_file):

    r = media_info(video_file)
    video_stream_info = [x for x in r['streams'] if x['codec_type'] == 'video'][0]
    width = video_stream_info["width"]
    height = video_stream_info["height"]
    resolution = str(width) + "x" + str(height)
    return resolution

def tag_start():
    file = open("data/diagnosis/tags.txt", 'w')

    xml_version = "1.0"

    base = [
    '<?xml version="' + xml_version + '"?>',
    '<!DOCTYPE Tags SYSTEM "matroskatags.dtd">',
    "<Tags>"]

    file.write("\n".join(base))

    target = "50"
    tag = [
    "<Tag>",
    "<Targets>",
    "<TargetType>"+ target + "</TargetType>",
    "</Targets>"
    ]

    file.write("\n".join(tag))
    file.close()


def add_tag(target_name, target_string, target_language):
    if target_string != "":
        file = open("data/diagnosis/tags.txt", 'a', encoding="utf-8")
        file.write('  <Simple>\n   <Name>'+ target_name + '</Name>\n   <String>' +\
        target_string + '</String>\n   <TagLanguage>' + target_language + '</TagLanguage>\n  </Simple>\n')
        file.close()


def tag_end():
    file = open("data/diagnosis/tags.txt", 'a')
    file.write(' </Tag>\n</Tags>')
    file.close()


def tag_creator():


    ttv = 50
    tt = "TEST"

    tags = [
    "<Tag>",
    "<Targets>",
    "<TargetTypeValue>" + ttv + "</TargetTypeValue>",
    "<TargetType>" + tt + "</TargetType>",
    ""]


def convert_lang(v):

    if "[" in v and "]" in v:
        lang_code = v.split("[")[1].split("]")
        if type(lang_code) == list:
            lang_code = lang_code[0]
        lang_code = lang_code.split("-")[0]
    else:
        lang_code = "und"

    if type(lang_code) == list:
        for items in lang_code:
            if len(items) == 2 or len(items) == 3:
                lang_code = items.lower()


    if len(lang_code) == 2:
        try:
            lang_code = languages.get(part1=lang_code).part3
        except KeyError:
            lang_code = "und"
    elif len(lang_code) == 3:
        try:
            lang_code = languages.get(part2b=lang_code).part3
        except KeyError:
            try:
                lang_code = languages.get(
                    part3=lang_code).part3
            except KeyError:
                lang_code = "und"
    else:
        lang_code = "und"

    lang =  languages.get(part3=lang_code).name

    lp = lang_code + "," + lang
    return lp

def find_values(drm_info, platform):

    drm_info = Path(drm_info).read_bytes()
    offset = drm_info.rfind(b'pssh')
    pssh = drm_info[offset - 4:offset - 4 + drm_info[offset - 1]]
    pssh = base64.b64encode(pssh).decode()
    print(pssh)
    
    return pssh


def ip_info():

    ipinfo_headers = {
        'Accept': '*/*',
        'Accept-Language': 'en',
        'Referer': 'https://ipinfo.io/',
        'Content-Type': 'application/json'
    }

    ipinfo_token = config["general"]["ipinfo"]
    check_ip = ipinfo.getHandler(ipinfo_token)

    while True:
        try:
            details = check_ip.getDetails()
        except:
            print("[error] Trying check IP again")
        else:
            gi = details.all
            break

    return gi



def date_to_ts(air_date):

    date = air_date.split("T")[0].split("-")
    time = air_date.split("T")[1][:-1].split(":")

    date_int = []
    time_int = []
    for items in date:
        date_int.append(int(items))
    for items in time:
        time_int.append(int(items))
    date = date_int
    time = time_int
    air_date = datetime(date[0], date[1], date[2], time[0], time[1], time[2])
    ts = int(air_date.timestamp())
    return ts

def pinata_upload(loc,f_type):

    pinata_api = config["general"]["pinata_api"]
    pinata_secret = config["general"]["pinata_secret"]
    ipfs_provider = config["general"]["ipfs_server"]
    ipfs_stream_provider = config["general"]["ipfs_stream_server"]
    ipfs_base = "https://" + ipfs_provider + "/ipfs/"
    ipfs_stream_base = "https://" + ipfs_stream_provider + "/ipfs/"
    pinata = Pinning(PINATA_API_KEY=pinata_api, PINATA_API_SECRET=pinata_secret)
    print(loc)
    pin = pinata.pin_file_to_ipfs(loc)
    print(pin)
    ipfs_id = pin["IpfsHash"]
    

    if f_type == "stream":
        url = ipfs_stream_base + ipfs_id
    else:
        url = ipfs_base + ipfs_id

    while True:
        print("[stream] Creating cache for " + f_type + " file on IPFS" )
        try:
            create_cache =  requests.get(ipfs_base + ipfs_id)
        except:
            continue
        else:
            pinata.unpin(ipfs_id)
            break

    if f_type != "stream":
        os.remove(loc)

    return url










import requests
import json
import glob
import subprocess
from slugify import slugify
from bs4 import BeautifulSoup
import sys
import os
from iso639 import languages
from func.basics import *
from func.messages import *
import configparser

config = configparser.ConfigParser()
config.read('data/tokens/config.ini')


wget = config["binaries"]["wget"]

base_url = "https://puhutv.com"
base_player = "https://dygvideo.dygdigital.com/api/video_info?akamai=true&"
search_url = "https://appservice.puhutv.com/search/search"

headers = {
    'user-agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (Ktesttemp, like Gecko) Chrome/90.0.4430.85 Safari/537.36',
}


async def query(title, sr, at, ip_data, message):
    global qr
    qr = []

    search_title = title
    slug_title = slugify(search_title)

    params = {"query": slug_title}
    q = requests.get(search_url, params=params, headers=headers)
    q = q.json()
    q = q["data"]

    for i in range(len(q)):
        if slug_title in slugify(q[i]["name"]):
            c = requests.get(base_url + '/' + q[i]["slug"], headers=headers)
            t = BeautifulSoup(c.text, 'html.parser')
            info = json.loads(t.find('script', id='__NEXT_DATA__', type='application/json').text)
            data = info["props"]["pageProps"]["details"]["data"]
            content_info = {}
            content_info["id"] = data["id"]
            content_info["title"] = data["name"].strip()
            content_info["slug"] = data["slug"]
            content_info["single"] = q[i]["is_movie"]
            content_info["meta"] = q[i]["groups"]
            if q[i]["is_movie"] == False and info["props"]["pageProps"]["episodeData"] != []:
                content_info["seasons"] = data["meta"]["seasons"]
                content_info["content"] = info["props"]["pageProps"]["episodeData"]["data"]["episodes"]
            qr.append(content_info)
    sr["puhu"] = qr

    if qr != []:
        for i in range(len(qr)):
            if slug_title in slugify(qr[i]["title"]):
                r = {}
                r["id"] = qr[i]["id"]
                r["title"] = qr[i]["title"]
                r["platform"] = "puhu"
                r["meta"] = []
                for group in qr[i]["meta"]:
                    r["meta"].append(group["display_name"])
                at.append(r)


def select(ci, cid, season):
    global title
    global ct
    global wv_server
    global content_all
    global info
    wv_server = ""

    for i in range(len(qr)):
        if cid == qr[i]["id"]:
            title = qr[i]["title"]
            if qr[i]["single"] == True:
                ct = "single"
            else:
                ct = "multiple"
            ci["info"] = qr[i]
            if qr[i]["single"] == False:
                ci["info"].pop("content")
            info = ci["info"]
            if ct == "multiple":
                if season == 1:
                    ci["content"] = qr[i]["content"]
                else:
                    for t in qr[i]["seasons"]:
                        if season + "-sezon" in t["slug"]:
                            c = requests.get(base_url + '/' + t["slug"], headers=headers)
                            c = BeautifulSoup(c.text, 'html.parser')
                            info = json.loads(c.find('script', id='__NEXT_DATA__', type='application/json').text)
                            content_all = info["props"]["pageProps"]["episodes"]["data"]["episodes"]
                            ci["content"] = content_all


async def download(season, episode, message, dil):
    global drm_status
    global content
    global rtuk

    drm_status = 0
    slug_title = slugify(title)
    dot_title = slug_title.replace("-", ".")

    video_url = ""
    r_id = ""
    if ct == "multiple":
        c = content_all
        for m in range(len(c)):
            if "-" + episode + "-" in c[m]["slug"]:
                content = c[m]
                r_id = c[m]["video_id"]
                r_url = c[m]["slug"]
    else:
        r_url = info["slug"].replace("-detay", "-izle")
        c = requests.get(base_url + '/' + r_url, headers=headers)
        t = BeautifulSoup(c.text, 'html.parser')
        d = json.loads(t.find('script', id='__NEXT_DATA__', type='application/json').text)
        r_id = d["props"]["pageProps"]["movieAssets"]["data"]["video_id"]

    if r_id == "":
        await message.reply_text("[error] No media found")
        

    player = requests.get(base_player + 'PublisherId=29' + '&ReferenceId=' + r_id + '&SecretKey=NtvApiSecret2014*', headers=headers)
    player = json.loads(player.text, strict=True)
    video_url = player["data"]["flavors"]["hls"]

    if ct == "multiple":
        content["player"] = player["data"]
    else:
        info["player"] = player["data"]

    if video_url == "":
        await message.reply_text("[error] No video url")
        

    video_hls = requests.get(video_url, headers=headers).text
    video_hls = video_hls.split("\n")

    base_hls = video_url.split("/")
    base_hls = "/".join(base_hls[:-1])

    new_hls = []
    for i in video_hls:
        if i.startswith("#") == False:
            new_hls.append(base_hls + "/" + i.split("&r=")[0])
        else:
            new_hls.append(i)

    with open("encrypted/bypass.m3u8", "w") as file:
        file.write("\n".join(new_hls[:-1]))

    chunklist = requests.get(new_hls[-2], headers=headers).text
    if chunklist.find("rtuk") != -1:
        rtuk = True
    else:
        rtuk = False

    video_url = pinata_upload("encrypted/bypass.m3u8", "M3U8")

    # subtitles
    s = []
    if ct == "multiple":
        if "tracks" in content["player"]:
            s = content["player"]["tracks"]
        dot_title = dot_title + "."
    elif ct == "single":
        if "tracks" in info["player"]:
            s = info["player"]["tracks"]

    dwn_lang = []
    for t in range(len(s)):
        if s[t]["kind"] == "subtitles":
            sub_code = s[t]["language"].lower()
            sub_code = languages.get(part1=sub_code).part3
            sub_lang = languages.get(part3=sub_code).name
            sub_url = s[t]["src"]
            sub_codec = sub_url.split(".")[-1]
            out_name = 'decrypted/' + dot_title + season + \
                episode + "-" + sub_code + "subtitle." + sub_codec
            sub_run = [wget, sub_url, "--output-document=" + out_name]
            sub_down = subprocess.run(sub_run, capture_output=True, text=True)
            dwn_lang.append(sub_lang)
    if dwn_lang != []:
        await message.reply_text("[download] " + ", ".join(dwn_lang) + " subtitles are downloaded")
    return video_url


def fix_output(output_name):
    fragments = glob.glob(output_name + ".part*")
    f_l = []
    if rtuk == False:
        for items in fragments:
            f_l.append(items)
    else:
        for items in fragments:
            if "Frag0" not in items:
                f_l.append(items)
    f_l = natural_sort(f_l)
    combine = ["ffmpeg", "-i", "concat:" + "|".join(f_l), "-c", "copy", output_name, "-y"]
    subprocess.run(combine, capture_output=True, text=True)
    for items in fragments:
        os.remove(items)


def adapt(season, episode):
    global chapter_status
    global made_year
    global custom_title

    tags = []
    tag = {}
    tag["name"] = "COPYRIGHT"
    tag["value"] = "PuhuTV"
    tag["tag_language"] = "en"
    tags.append(tag)

    tag = {}
    tag["name"] = "DISTRIBUTED_BY"
    tag["value"] = "QUT"
    tag["tag_language"] = "en"
    tags.append(tag)

    tag_start()

    for i in range(len(tags)):
        nm = tags[i]["name"]
        v = tags[i]["value"]
        l = tags[i]["tag_language"]
        add_tag(nm, v, l)

    tag_end()

    made_year = ""
    chapter_status = 0
    custom_title = ""

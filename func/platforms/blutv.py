import requests, json, sys, os
import configparser
from slugify import slugify
from iso639 import languages
from imdb import Cinemagoer
from func.basics import *
import urllib.parse
import subprocess
config = configparser.ConfigParser()
config.read('data/tokens/config.ini')
import time
from vtt_to_srt.vtt_to_srt import ConvertFile
wget = config["binaries"]["wget"]
video_codecs = config["turkey"]["blu_video_codecs"].split(", ")

base_api = 'https://www.blutv.com/api'
search_api = base_api + '/search'
info_api = base_api + '/supercontents'
content_api = base_api + "/supercontents-active"
play_api = base_api + '/player-config'
content2_api = base_api + "/get-content-detail"
refresh_api = base_api + "/refresh"


headers = {
    'user-agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (Ktesttemp, like Gecko) Chrome/90.0.4430.85 Safari/537.36',
    'Content-Type': 'text/plain;charset=UTF-8',
}

async def query(title,sr,at,ip_data,message):

    global q

    slug_title = slugify(title)

    regions = ["turkey", "int", "mena"]
    region_code = ["", ".lama", ".aze"]
    region_live = ["569cafd6058d024688a14441","59cde800058d026e60370f96",""]

    q_l = []
    
    for r in range(len(region_code)):

        rc = region_code[r]

        json_data = {
            "application": "com.blu",
            "privilege_name": "Application:com.blu" + rc,
            "package_names": ["SVOD"],
            "from": 0,
            "size" : 999,
            "path" : "/",
            "query_string": title,
            "content_type": ["SerieContainer","MovieContainer"],
            "person" : "*",
            "version": 3
        }

        q = requests.post(url=search_api, headers=headers, json=json_data)
        q = q.json()

        if "errorCode" in q:
            print("[blutv] Skipping search for bluTV - " + q["errorMessage"])
            return

        q = q["result"]

        ## live 
        
        if region_live[r] != "":
            headers_l = headers
            headers_l["AppPlatform"] = "com.blu" + "tr"
            params = {'id': region_live[r],'media': 'mpd'}
            live = requests.get(url=play_api, headers=headers_l, params=params)
            print(live)
            live = live.json()["media"]["channels"]
            for channel in live:
                q.append(channel)

        if r == 0:
            for items in q:
                items["region"] = rc
            q_l = q
            continue

        for i in range(len(q)):
            exist = 0
            for t in range(len(q_l)):
                if q[i]["id"] == q_l[t]["id"]:
                    exist = 1

            if exist == 0:
                q[i]["region"] = rc
                q_l.append(q[i])

    q = q_l
    sr["blutv"] = q
    
    for i in range(len(q)):

        if slug_title in slugify(q[i]["title"]):

            add_info = []


            if "channelId" in q[i]:
                q[i]["stream_type"] = "live"
                r = {}
                r["title"] = q[i]["title"].strip()
                r["meta"] = ["CHANNEL"]
                r["platform"] = "blutv"
                r["id"] = q[i]["id"]
                at.append(r)            
                continue    
            
            q[i]["stream_type"] = "vod"

            if "contentType" in q[i]:
                add_info.append(category_translate(q[i]["contentType"]))

            if "exclusive" in q[i]["badge"]["badgeText"]:
                add_info.append("Original")

            if q[i]["comingSoon"] == True:
                add_info.append("Coming Soon")
            elif "onlyBluTV" in q[i]["badge"]["badgeText"]:
                add_info.append("Exclusive")

            if "REMAINING_DATE" in q[i]["badge"]["badgeText"]:
                remaining = "- EXPIRES IN " + q[i]["badge"][
                    "remainingNow"] + " Day"

                if int(q[i]["badge"]["remainingNow"]) > 1:
                    remaining = remaining + "s"
                add_info.append(remaining)

            if "region" in q[i]:
                add_info.append("- REGION " + q[i]["region"])

            r = {}
            r["title"] = q[i]["title"].strip()
            r["meta"] = add_info
            r["platform"] = "blutv"
            r["id"] = q[i]["id"]
            at.append(r)

def altyz(video,sub):
    start = time.time()
    vid = video
    stxt = sub.split(".srt")[0] + ".txt"
    subtxt = os.rename(sub, stxt)
    s = open(stxt, "r", encoding="UTF-8")
    subc = s.read()
    s.close()
    subg = subc.split("}")[0] + "}"
    print(subg)
    reklam = """0
00:00:00,000 --> 00:00:30,000
{\an8}Bu Bölüm{\c&H00FF00&}
{\an8}Hplatforms adına hazırlanmıştır..{\c&HFFFFFF&}\n"""
    ss = subc.replace(subg, "")
    subcontent = reklam + ss
    nsub = stxt.split(".txt")[0] + ".new.srt"
    with open(nsub, "w", encoding="UTF-8") as dosya:
        dosya.write(subcontent)
        dosya.close()
    sub = nsub
    print(vid)
    out_file = '.'.join(video.split('.')[:-1])
    output = out_file+'SUB.mp4'
    out_location = output
    
    command = [
            'ffmpeg','-hide_banner',
            '-i',vid,
            '-vf','subtitles='+sub,
            '-c:v','h264',
            '-map','0:v:0',
            '-map','0:a:0?',
            '-preset','superfast',
            '-y',out_location
            ]
    process = subprocess.run(command)
    os.remove(stxt)
    os.remove(vid)
    # https://github.com/jonghwanhyeon/python-ffmpeg/blob/ccfbba93c46dc0d2cafc1e40ecb71ebf3b5587d2/ffmpeg/ffmpeg.py#L11

    return output

def select(ci, cid, season):
    
    global title
    global ct
    global wv_server
    global info
    global content_all

    wv_server = "https://wdvn.blutv.com/"
    
    for i in range(len(q)):
        if cid == q[i]["id"]:
            title = q[i]["title"]

            if q[i]["stream_type"] == "vod":
                content_url = q[i]["url"]
                ct = q[i]["contentType"]
            else:
                ct = "single"
                info = q[i]
                ci["info"] = info
                content_all = info
                return
            break

    params = {'query': cid}

    info = requests.get(info_api, params=params, headers=headers)
    info = info.json()
    info["stream_type"] = "vod"
    info["region"] = q[i]["region"]

    if info["status"] == 500:
        print("[error] " + info["errorMessage"])
        sys.exit(0)

    if "originalName" in info:
        title = info["originalName"]

    ci["info"] = info
    
    blu_data = '{"q":"ContentType:{$in:[\'' + ct + '\']}",\
            "filter":"Ancestors/any(a:a/SelfPath eq \'' + content_url + '/\')",\
            "orderby":"SeasonNumber asc, EpisodeNumber asc"}'

    content = requests.post(content_api, headers=headers,
                                 data=blu_data).json()

    if content['status'] == 500:
        print("[error] " + content["errorMessage"])
        sys.exit(0)

    del content['status']
    if "movie" in ct.lower():
        ct = "single"
    else:
        ct = "multiple"

    ## new api
    is_v2 = False
    if content == {}:

        ## get token

        with open("data/tokens/turkey/blutv.json") as f:
            tokens = json.loads(f.read())

        if tokens["expire"] > int(time.time()):
            token = tokens["token"]
        else:
            token = refresh_token(tokens)

        user_id = tokens["user_id"]
        profile_id = tokens["profile_id"]


        headers_c = headers.copy()
        headers_c["AppPlatform"] = "com.blu" + info["region"]
        cookies_c = {"token_a":token}
        json_c = {"url":content_url,"userNo":user_id,"profileId":profile_id}
        content = requests.post(content2_api, cookies=cookies_c, headers=headers_c, json=json_c)
        content = content.json()

        if "seasons" in content:
            content = content["seasons"]
            is_v2 = True
        else:
            content = {}

    content_all = []


    if is_v2 == False:
        for i in content:
            sv = "seasonNumber" in content[i] and \
            content[i]["seasonNumber"] == int(season)
            cv = content[i]["contentType"] == "Episode"
            tv = sv and cv
            if tv == True:
                content_all.append(content[i])
    else:
        for i in content:
            if i["seasonNumber"] == int(season):
                content_all = i["episodes"]
    
    ci["content"] = content_all

async def download(season, episode,message,dil):
    
    global drm_status
    global video_url
    global content

    slug_title = slugify(title)
    dot_title = slug_title.replace("-", ".")

    content = ""
    if ct == "multiple":
        for m in range(len(content_all)):
            if int(episode) == content_all[m]["episodeNumber"]:
                content = content_all[m]
                break
    else:
        content = content_all

    if content == "":
        await message.reply_text("[error] No media found")


    params = {'id': content["id"],'media': 'mpd'}

    headers_p = headers.copy()
    headers_p["AppPlatform"] = "com.blu" + "tr"

    play = requests.get(play_api, params=params,headers=headers_p)
    print(play.content)
    play = play.json()["media"]

    content["play"] = play
    video_url = play["source"]
    base_codec = video_codecs[0]

    if play["drm"] == True:
        drm_status = 1
    else:
        drm_status = 0


    if info["stream_type"] == "live":

        if ".mpd" in video_url:
            video_format = "dash"
        else:
            video_format = "hls"

        streamer = {}
        streamer["type"] = video_format
        streamer["src"] = video_url

        if drm_status == 1:
            streamer["drm"] = {"widevine":{"licenseUrl":""},"playready":{"licenseUrl":""}}
            streamer["drm"]["widevine"]["licenseUrl"] = wv_server

        base_player = open("data/extras/stream.html", "r")
        base_player = base_player.read()
        base_player = base_player.replace("content_json",str(streamer))

        ui = {}
        
        base_player = base_player.replace("ui_json",str(ui))

        with open("data/diagnosis/stream/index.html", 'w') as f:
            f.write(base_player)

        await message.reply_text("[stream] Creating stream url via SIA")
        stream_url = pinata_upload("data/diagnosis/stream/index.html","stream")
        await message.reply_text("[stream] NOT WORKING YET, KNOWN ISSUE")
        await message.reply_text("[stream] " + stream_url)  

    if base_codec == "hvc" and "mpd" in video_url:
        hevc_url = video_url.replace("dash-0", "dash-1")
        hevc_test = requests.get(hevc_url)
        if "octet-stream" in hevc_test.headers["Content-Type"]:
            video_url = hevc_url
        else:
            await message.reply_text("[download] No HEVC support, using AVC")

    elif base_codec == "hvc" and "mpd" not in video_url:
        await message.reply_text("[download] No HEVC support, using AVC")

    ## subtitles

    if ct == "multiple":
        dot_title = dot_title + "."

    if play["subtitles"] != []:
        subs = play["subtitles"]
        dwn_lang = []
        for i in range(len(subs)):
            sub_code = subs[i]["label"]
            sub_lang = languages.get(part3=sub_code).name
            if sub_lang == "Turkish":
                sub_code = subs[i]["label"]
                sub_lang = languages.get(part3=sub_code).name
                sub_url = subs[i]["src"]
                sub_codec = subs[i]["src"].split(".")[-1]
                out_name = 'decrypted/' + dot_title + season + episode + "-" + sub_code + "subtitle." + sub_codec
                sub_down = [wget, sub_url, '--output-document=' + out_name]
                subprocess.run(sub_down, capture_output=True, text=True)
                convert_file = ConvertFile(out_name, "utf-8")
                try:
                    convert_file.convert()
                    doc = 'decrypted/' + dot_title + "-" + sub_code + "subtitle.srt"
                    await message.reply_document(doc)
                except Exception as e:
                    print(e)
                dwn_lang.append(sub_lang)

        dwn_lang.sort()
        sub_print = "[download] " + ", ".join(dwn_lang) + " subtitles are downloaded"
        if len(dwn_lang) == 1:
            sub_print = sub_print.replace("subtitles are", "subtitle is")
        await message.reply_text(sub_print)

    return video_url


def options_fix(options):
        
    if "x" in "\n".join(options):
        return options

    print("[download] No resolution info, fixing...")

    options_new = []
    qo = [wget, video_url, '--output-document=encrypted/quality_options.txt']
    qor = subprocess.run(qo, capture_output=True, text=True)
    qo = open("encrypted/quality_options.txt")
    qo = qo.readlines()
    base_url = "/".join(video_url.split("/")[:-1]) + "/"
    for i in range(len(qo)):
        if "BANDWIDTH" in qo[i]:
            bitrate = qo[i].split("BANDWIDTH=")[-1].split(",")[0]
            sq = qo[i]
            squ = base_url + qo[i+1]
            squ = squ.replace(".m3u8","0.ts").replace("\n","")
            qc = ["yt-dlp", squ, "-o", "encrypted/quality_test.ts","--force-overwrites"]
            qcr = subprocess.run(qc, capture_output=True, text=True)
            res = get_resolution("encrypted/quality_test.ts")
            os.remove("encrypted/quality_test.ts")
            for t in range(len(options)):
                if bitrate[:-3] + "k" in options[t] or bitrate[:-4] + "k" in options[t]:
                    new_option = options[t].replace("mp4 unknown",
                                                    "mp4 " + res)
                    options_new.append(new_option)

    os.remove("encrypted/quality_options.txt")
    options = options_new
    options.sort(reverse=True)

    return options

def save_id(dash_f):

    global dash_vid
    
    dash_vid = dash_f

def find_values(di,vt):
    
    global kid
    global pssh
    
    di = di["MPD"]["Period"]["AdaptationSet"]
    for t in range(len(di)):
        if "video" in di[t]["@contentType"] and vt == "video":
            my_id = ""
            hol = di[t]["Representation"]
            for k in range(len(hol)):
                if hol[k]["@id"] == dash_vid:
                    my_id = t
            if my_id != "":
                cp = di[t]["ContentProtection"]     
        if "audio" in di[t]["@contentType"] and vt != "video":
            cp = di[t]["ContentProtection"]
    
    for k in range(len(cp)):
        if "@cenc:default_KID" in cp[k]:
            kid = cp[k]["@cenc:default_KID"]
        if "@schemeIdUri" in cp[k] and "edef8ba9-79d6-4ace-a3c8-27dcd51d21ed" in cp[k]["@schemeIdUri"]:
            pssh = cp[k]["cenc:pssh"]

    kid = kid.replace("-","")


def chapters(default_chapter, duration):

    intro_start = ""
    intro_end = ""
    credits_start = ""
    chapter_status = 0

    c = content["play"]["videotags"]

    if "intro" in c:
        i = c["intro"]
        if i["show"] != None:
            intro_start = i["show"]
        if i["target"] != None:
            intro_end = i["target"]
    if "next" in content["play"]["videotags"]:
        n = c["next"]
        if n["show"] != None:
            credits_start = duration - n["show"]

    if intro_start != "" and intro_end != "":
        chapter_status = 1
    elif credits_start != "":
        chapter_status = 1

    if chapter_status == 1:
        chapters = []

        chapters.append("CHAPTER01=00:00:00.000\n")
        chapters.append("CHAPTER01NAME=" + default_chapter + "\n")
        if intro_start != "" and intro_end != "":
            chapters.append("CHAPTER02=" +
                            chapter_timer(intro_start, "second") + ".000\n")
            chapters.append("CHAPTER02NAME=Intro\n")
            chapters.append("CHAPTER03=" + chapter_timer(intro_end, "second") +
                            ".000\n")
            chapters.append("CHAPTER03NAME=" + default_chapter + "\n")

        if credits_start != "":
            chapters.append("CHAPTER04=" +
                            chapter_timer(credits_start, "second") + ".000\n")
            chapters.append("CHAPTER04NAME=Credits")

        file = open("data/diagnosis/chapters.txt", 'w')
        for items in chapters:
            file.writelines([items])
        file.close()

    return chapter_status


def adapt(season, episode):

    global chapter_status
    global custom_title
    global made_year
    global descem
    g = info

    if ct == "multiple":
        not_c = content
        n = "Episode"
    elif ct == "single":
        not_c = g
        n = "Movie"

    ## tags

    tags = []

    ### from g

    if "origin" in g and g["origin"] != "":
        tag = {}
        origin_country = g["origin"]
        tag["name"] = "RECORDING_LOCATION"
        tag["value"] = origin_country
        tag["tag_language"] = "en"
        tags.append(tag)

    made_year = ""
    if "made_year" in g and g["made_year"] != "":
        tag = {}
        made_year = g["made_year"].split("T")[0]
        tag["name"] = "DATE_RECORDED"
        tag["value"] = made_year
        tag["tag_language"] = "en"
        tags.append(tag)

    imdb_id = ""
    if "imdbUrl" in g and g["imdbUrl"] != "":
        tag = {}
        url = g["imdbUrl"].split("/")
        for t in range(len(url)):
            if "title" in url[t]:
                imdb_id = url[t + 1]
        tag["name"] = "IMDB"
        tag["value"] = imdb_id
        tag["tag_language"] = "en"
        tags.append(tag)

    age_sign = ""
    if "parentalRating" in g and g["parentalRating"] != "":
        age_sign = g["parentalRating"]
        if 18 <= age_sign:
            age_sign = "TV-MA"
        elif 12 <= age_sign < 18:
            age_sign = "TV-14"
        elif 7 <= age_sign < 12:
            age_sign = "TV-PG"
        elif age_sign < 7:
            age_sign = "TV-G"

    advisory = []
    if "userNibbles" in g and g["userNibbles"] != "":
        advisory_list = g["userNibbles"]
        for a in range(len(advisory_list)):
            sign = advisory_list[a]
            if "cinsellik" in sign:
                advisory.append("S")
            if "olumsuz-ornek" in sign:
                advisory.append("L")
            if "siddet-korku" in sign:
                advisory.append("V")

    if advisory != "":
        age_sign = age_sign + ", " + ", ".join(advisory)

    if age_sign != "":
        tag = {}
        tag["name"] = "LAW_RATING"
        tag["value"] = age_sign
        tag["tag_language"] = "en"
        tags.append(tag)

    if "isDiscovery" in g and g["isDiscovery"] == True:
        platform_tag = "Discovery+"
    else:
        platform_tag = "BluTV"
    tag = {}
    tag["name"] = "COPYRIGHT"
    tag["value"] = platform_tag
    tag["tag_language"] = "en"
    tags.append(tag)

    if "cast" in g and g["cast"] != []:
        cast = []
        cast_list = g["cast"]
        for a in range(len(cast_list)):
            d = cast_list[a]["fullName"]
            cast.append(d)
        tag = {}
        tag["name"] = "CAST"
        tag["value"] = ", ".join(cast)
        tag["tag_language"] = "en"
        tags.append(tag)

    if "directors" in g and g["directors"] != []:
        directors = []
        director_list = g["directors"]
        for a in range(len(director_list)):
            d = director_list[a]["fullName"]
            directors.append(d)
        tag = {}
        tag["name"] = "DIRECTOR"
        tag["value"] = ", ".join(directors)
        tag["tag_language"] = "en"
        tags.append(tag)

    ## to-do: genres should be translated
    if "genres" in g and g["genres"] != []:
        tag = {}
        tag["name"] = "GENRE"
        tag["value"] = ", ".join(g["genres"])
        tag["tag_language"] = "tr"
        tags.append(tag)

    ### from not_c

    air_date = ""
    if "startDate" in not_c and not_c["startDate"] != "":
        tag = {}
        air_date = not_c["startDate"].split("T")[0]
        tag["name"] = "DATE_RELEASED"
        tag["value"] = air_date
        tag["tag_language"] = "en"
        tags.append(tag)

    if "description" in not_c and not_c["description"] != "":
        tag = {}
        description = not_c["description"]
        tag["name"] = "COMMENT"
        tag["value"] = description
        tag["tag_language"] = "tr"
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

    ## chapters

    duration = not_c["duration"]
    print(not_c)
    descem = not_c["description"]

    chapter_status = chapters(n, duration)

    ## custom title

    custom_title = ""
    if imdb_id != "" and ct == "multiple":
        ia = Cinemagoer()
        i = ia.get_movie(imdb_id[2:])
        ia.update(i, 'episodes')
        try:
            imdb_title = i['episodes'][int(season)][int(episode)]['title']
        except KeyError:
            custom_title = ""
            pass
        else:
            if "episode" not in slugify(imdb_title) and "bolum" not in slugify(
                    imdb_title):
                custom_title = imdb_title


def refresh_token(tokens):

    print("[blutv] Refreshing token...")
    cookies_r = {"token_r":tokens["refresh_token"]}
    headers_r = headers.copy()
    headers_r["AppPlatform"] = "com.blu"

    json_r = {"excludeProfileId":None,"profileId":tokens["profile_id"]}

    refresh = requests.post(refresh_api, cookies=cookies_r, headers=headers_r, json=json_r)
    refresh = refresh.json()

    expire_time = int(time.time()) + refresh["tokenExpire"] - 1800

    new_tokens = {
        "user_id":tokens["user_id"],
        "profile_id":tokens["profile_id"],
        "refresh_token":refresh["refreshToken"],
        "token":refresh["accessToken"],
        "expire":expire_time}

    with open("data/tokens/turkey/blutv.json", 'w') as outfile:
        json.dump(new_tokens, outfile, indent=4)

    return refresh["accessToken"]

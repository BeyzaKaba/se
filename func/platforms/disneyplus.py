import requests, json, sys
from slugify import slugify
from func.basics import *
from func.messages import *
from vtt_to_srt.vtt_to_srt import ConvertFile
from func.proxy import *
import configparser
import os
from iso639 import languages
import time
import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler('log.txt'), logging.StreamHandler()],
                    level=logging.INFO)

LOGGER = logging.getLogger(__name__)
config = configparser.ConfigParser()
config.read('data/tokens/config.ini')
wget = config["binaries"]["wget"]

base_api = "https://disney.content.edge.bamgrid.com"
play_api = "https://disney.playback.edge.bamgrid.com/media/"

headers = {
    'User-Agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (Ktesttemp, like Gecko) Chrome/90.0.4430.85 Safari/537.36',
    'Referer': 'https://www.disneyplus.com/'}

language = config["disneyplus"]["display_language"]
regions = config["disneyplus"]["regions"].split(", ")

video_codecs = config["disneyplus"]["video_codecs"].split(", ")
video_bitrate = config["disneyplus"]["video_bitrate"].split(", ")[0]

audio_codecs = config["disneyplus"]["audio_codecs"].split(", ")

widevine = config["disneyplus"]["widevine"].split(", ")[0]

audio_pref = config["disneyplus"]["audio_preferred"].split(", ")
if audio_pref[0] == "": 
    audio_pref = []



async def query(title,sr,at,ip_data,message):

    global headers
    global q

    slug_title = slugify(title)

    for r in range(len(regions)):

        ## get token

        with open("data/tokens/international_streaming/disney_tokens.json") as f:
            tokens = json.loads(f.read())

        if tokens["expire"] > int(time.time()):
            token = tokens["token"]
        else:
            token = refresh_token(tokens,"expire")

        headers["authorization"] = "Bearer " + token

        params = ["","svc","search","disney",
            "version","5.1",
            "region",regions[r],
            "audience","k-false,l-true","maturity","1850",
            "language",language,
            "queryType","ge",
            "pageSize","45",
            "query",title]

        q = requests.get(base_api + "/".join(params),headers=headers)
        q = q.json()["data"]["search"]["hits"]

        q_l = []

        for t in range(len(q)):
            if "hit" in q[t]:
                q_l.append(q[t]["hit"])
            else:
                await message.reply_text("[error] [disneyplus] Different json format? Investigate.")

        q = q_l

        for t in range (len(q)):
            q[t]["region"] = regions[r]

        if r == 0:
            sr["disneyplus"] = q
        else:
            for i in range(len(q)):
                exist = 0
                db = sr["disneyplus"]
                for t in range(len(db)):

                    if "programId" in db[t]:
                        c_d = db[t]["programId"]
                    else:
                        c_d = db[t]["seriesId"]

                    if "programId" in q[i]:
                        t_d = q[i]["programId"]
                    else:
                        t_d = q[i]["seriesId"]
                    if c_d == t_d:
                        exist = 1

                if exist == 0:
                    sr["disneyplus"].append(q[i])
    
    q = sr["disneyplus"]

    for i in range(len(q)):

        on = ""
        if "internalTitle" in q[i]:
            on = q[i]["internalTitle"].split("-")[0].strip()

        dn = q[i]["text"]["title"]["full"]
        for items in dn:
            dn = dn[items]["default"]["content"]
        if type(dn) == dict:
            dn = ""

        match = slug_title in slugify(on) or slug_title in slugify(dn)

        if match == True:
            
            add_info = []

            if q[i]["type"] == "DmcSeries":
                add_info.append("Series")
            else:
                add_info.append("Movie")

            if q[i]["badging"] != None:
                ori = q[i]["badging"]

                if "disney" in ori:
                    add_info.append("D+ Original")
                elif "star" in ori:
                    add_info.append("Star Original")
                else:
                    print("[warning] [disneyplus] Missing badge" + ori)
                    add_info.append(ori.replace("originial","").title() + " Original")


            if "releases" in q[i]:
                add_info.append(str(q[i]["releases"][0]["releaseYear"]))

            if "Movie" in add_info:
                ts = int(q[i]["mediaMetadata"]["runtimeMillis"] / (60*1000))
                add_info.append(str(ts) + " min")

            add_info.append(q[i]["region"])

            if on != "":      
                result_title = on.strip()
            else:
                result_title = dn.strip()


            if "programId" in q[i]:
                c_i = q[i]["programId"]
            else:
                c_i = q[i]["seriesId"]                


            r = {}
            r["title"] = result_title
            r["meta"] = add_info
            r["platform"] = "disneyplus"
            r["id"] = str(c_i)
            at.append(r)

def select(ci,cid,season):
    
    global title
    global ct
    global region
    global wv_server
    global info
    global content_all

    wv_server = "https://disney.playback.edge.bamgrid.com/widevine/v1/obtain-license"
    sq = len(q) 
    LOGGER.info(sq) 
    for i in range(len(q)):
        
        if "programId" in q[i]:
            c_i = q[i]["programId"]
        else:
            c_i = q[i]["seriesId"]        

        if cid == str(c_i):

            title = ""
            if "internalTitle" in q[i]:
                title = q[i]["internalTitle"].split("-")[0].strip()

            if title == "":
                dn = q[i]["text"]["title"]["full"]
                for items in dn:
                    title = dn[items]["default"]["content"]
            
            if q[i]["type"] == "DmcSeries":
                ct = "multiple"
                encode_type = "encodedSeriesId"
                encode_id = q[i]["encodedSeriesId"]
            else:
                ct = "single"            
                encode_type = "encodedFamilyId"
                encode_id = q[i]["encodedParentOf"]

            region = q[i]["region"]

            params = ["","svc","content",q[i]["type"] + "Bundle",
                "version","5.1","region",region,
                "audience","k-false,l-true","maturity","1850",
                "language",language,
                encode_type,encode_id]

            info = requests.get(base_api + "/".join(params), headers=headers)
            info = info.json()["data"][q[i]["type"] + "Bundle"]
      
            if ct == "single":
                ci["info"] = info["video"]
            else:
                ci["info"] = info["series"]
                cs = info["episodes"]["videos"][0]["seasonSequenceNumber"]
                if int(season) == cs:
                    ci["content"] = info["episodes"]["videos"]
                else:
                    seasons = info["seasons"]["seasons"]
                    season_found = 0
                    for s in range(len(seasons)):
                        if seasons[s]["seasonSequenceNumber"] == int(season):
                            season_found = 1
                            season_id = seasons[s]["seasonId"]

                            params = ["","svc","content","DmcEpisodes",
                                "version","5.1","region",region,
                                "audience","k-false,l-true","maturity","1850",
                                "language",language,
                                "seasonId",season_id,
                                "pageSize","45",
                                "page","1"]

                            season_info = requests.get(base_api + "/".join(params),headers=headers)
                            season_info = season_info.json()["data"]["DmcEpisodes"]["videos"]
                            ci["content"] = season_info
                    if season_found == 0:
                        print("[error] No season " + season)

                content_all = ci["content"]
            LOGGER.info(ci)
            info = ci["info"]
            LOGGER.info(info)
            

async def download(season, episode, message, dil):
    
    global vo
    global audio_pref
    global ol
    global drm_status
    global content
    global video_url

    drm_status = 1

    slug_title = slugify(title)
    dot_title = slug_title.replace("-", ".")


    video_id = ""
    ol = ""
    if ct == "multiple":
        c = content_all
        for i in range(len(c)):
            if c[i]["episodeSequenceNumber"] == int(episode):
                video_id = c[i]["mediaMetadata"]["mediaId"]
                content = c[i]
                if "originalLanguage" in c[i]:
                    ol = c[i]["originalLanguage"]
    else:
        video_id = info["mediaMetadata"]["mediaId"]
        print(info)
        if "originalLanguage" in info:
            ol = info["originalLanguage"]
    
    
    if dil == "yok":
        if ol != "":
            audio_pref.append(ol)
    else:
        await message.reply_text(dil)
        audio_pref.append(dil)
    print(audio_pref)



    if video_id == "":
        await message.reply_text("[error] No media id found")
        

    headers_p = headers
    headers_p["Accept"] = "application/vnd.media-service+json; version=5"
    headers_p["x-dss-feature-filtering"] = "true"

    data = {'playback': {'attributes': {'resolution': {},'protocol': 'HTTP'}}}
    
    while True:

        video_play = play_api + video_id + '/scenarios/ctr-limited'
        video_opt = requests.post(video_play, headers=headers_p, json=data)

        if "errors" in video_opt.json():
            errors = video_opt.json()["errors"]
            
            blackout = 0
            for i in range(len(errors)):
                if "blackout" in errors[i]["code"]:
                    blackout = 1

            if blackout == 1:

                with open("data/tokens/international_streaming/disney_tokens.json") as f:
                    tokens = json.loads(f.read())
                
                token = refresh_token(tokens,"blackout")
                headers["authorization"] = "Bearer " + token
            else:
                for i in range(len(errors)):
                    print("[error] " + errors[i]["code"])
                
        else:
            break

    video_url = video_opt.json()["stream"]["complete"][0]["url"]
    video_url = video_url.split("?")[0]

    return video_url

async def adapt_url(quality,season,episode,message):

    global keys
    global audio_pref
    global quality_l
    global widevine_check

    await message.reply_text("[download] Creating m3u8 with options...")

    ## to-do: remove auth from headers no need
    video_opt = requests.get(video_url,headers=headers)

    vo = video_opt.text.split("\n")

    base_url = video_url.split("/")
    base_url = "/".join(base_url[:-1]) + "/"
    video = []
    audio = []
    sub = []
    keys = []

    for t in range(len(vo)):

        if "#EXT-X-MEDIA:TYPE=AUDIO" in vo[t]:
            a = {}

            a["name"] = vo[t].split('NAME="')[1].split('"')[0].replace("ü","u").replace("ç","c")
            a["language"] = vo[t].split('LANGUAGE="')[1].split('"')[0]
            a["codec"] =  vo[t].split('GROUP-ID="')[1].split('"')[0]
            
            if 'CHARACTERISTICS' in vo[t]:
                a["features"] =  vo[t].split('CHARACTERISTICS="')[1].split('"')[0]
            
            a["url"] = base_url + vo[t].split('URI="')[1].split('"')[0]
            audio.append(a)

        elif "#EXT-X-MEDIA:TYPE=SUBTITLES" in vo[t]:
            
            s = {}

            s["name"] = vo[t].split('NAME="')[1].split('"')[0].replace("ü","u").replace("ç","c")
            s["language"] = vo[t].split('LANGUAGE="')[1].split('"')[0]

            if "FORCED=YES" in vo[t]:
                s["forced"] = 1
            else:
                s["forced"] = 0

            if "describes-music-and-sound" in vo[t]:
                s["accessibility"] = 1
            else:
                s["accessibility"] = 0

            s["url"] = base_url + vo[t].split('URI="')[1].split('"')[0]
            print(s["language"])
            if s["language"] == "tr":
                sub.append(s)
            



        elif '#EXT-X-STREAM-INF:' in vo[t]:
            v = {}
            v["m_bandwidth"] = vo[t].split('BANDWIDTH=')[1].split(',')[0]
            v["bandwidth"] = vo[t].split('AVERAGE-BANDWIDTH=')[1].split(',')[0]

            v["codec"] = vo[t].split('CODECS="')[1].split('"')[0]
            v["resolution"] = vo[t].split('RESOLUTION=')[1].split(',')[0]

            char = vo[t].split('CHARACTERISTICS="')[1].split('"')[0]

            ## to-do: check method detect correctly
            if "com.dss.ctr.hd" in char:
                v["widevine"] = "3"
            elif "com.dss.ctr.fhd" in char:
                v["widevine"] = "2"
            elif "com.dss.ctr.uhd" in char:
                v["widevine"] = "1"

            v["url"] = base_url + vo[t+1]
            video.append(v)


        elif "#EXT-X-SESSION-KEY:" in vo[t]:

            if "edef8ba9-79d6-4ace-a3c8-27dcd51d21ed" in vo[t]:
                k = {}
                
                k["pssh"] = vo[t].split('base64,')[1].split('"')[0]

                if "com.dss.ctr.hd" in vo[t]:
                    k["kt"] = "3"
                if "com.dss.ctr.fhd" in vo[t]:
                    k["kt"] = "2"
                if "com.dss.ctr.uhd" in vo[t]:
                    k["kt"] = "1"

                if "kt" not in k:
                    k["kt"] = "0"

                keys.append(k)

    last_m3u8 = ["#EXTM3U\n","#EXT-X-INDEPENDENT-SEGMENTS\n"]

    for l in range(len(audio_codecs)):
        added_lang = []
        missing_lang = []
        print_add = []
        print_miss = []
        ac = audio_codecs[l]
        for t in range(len(audio)):

            al = audio[t]["language"].split("-")[0]

            
            if al in audio_pref and \
            ac in audio[t]["codec"] and \
            "features" not in audio[t] :

                a = '#EXT-X-MEDIA:'
                a = a + 'TYPE=AUDIO,'
                a = a + 'GROUP-ID' + '="' +  audio[t]["codec"] + '",'
                a = a + 'NAME'     + '="' +  audio[t]["name"] + '",'
                a = a + 'LANGUAGE' + '="' +  audio[t]["language"] + '",'

                mm = requests.get(audio[t]["url"],headers=headers)
                if "MAIN" in mm.text:
                    l_url = fix_url(mm.text,base_url)
                else:
                    l_url = audio[t]["url"]
                
                a = a + 'URI' + '="' + l_url  + '"'
                last_m3u8.append(a)
                added_lang.append(audio[t]["language"])
                print_add.append(convert_lang("[" + audio[t]["language"] + "]").split(",")[1])

        for t in audio_pref:
            if t not in added_lang:
                missing_lang.append(t)
        if added_lang != []:
            await message.reply_text(f"[download] Found codec match {ac}")

        if missing_lang == []:
            break
        else:
            audio_pref = missing_lang         


    match_v = []
    qualities = [360,480,540,720,1080,1440,2160]

    if int(quality) not in qualities:
        await message.reply_text("[download] No " + str(quality) + "p video, choosing closest one...")
        quality_dif_main = 10000

        for i in range(len(qualities)):
            quality_selected = qualities[i]
            quality_dif = int(quality) - quality_selected
            if quality_dif < 0:
                quality_dif = quality_dif * -1
            if quality_dif < quality_dif_main:
                quality_dif_main = quality_dif
                quality_id = i
    else:
        for i in range(len(qualities)):
            if int(quality) == qualities[i]:
                quality_id = i

    no_quality = []

    i = quality_id

    while True:

        quality_l = qualities[i]
        for l in range(len(video_codecs)):
            vc = video_codecs[l]
            for t in range(len(video)):
                if "x" + str(quality_l) in video[t]["resolution"]  and \
                int(widevine) <= int(video[t]["widevine"]) and \
                vc in video[t]["codec"]:
                    match_v.append(video[t])

            if len(match_v) == 0:
                pass
            else:
                break
        
        if i == -1:
            break

        if len(match_v) == 0:
            no_quality.append(str(quality_l) + "p")
            i = i - 1 
            pass
        else:
            if l != 0:
                if no_quality != []:
                    await message.reply_text("[download] [W-L" + widevine + "] No match for " + ", ".join(no_quality))
                await message.reply_text("[download] [W-L" + widevine + "] Found codec match " + vc  + " for " + str(quality_l) + "p")
            break

    ## to-do: sort, add options

    if len(match_v) == 0:
        print("[error] No matching video")
        

    match_v = sorted(match_v, key=lambda k: k['m_bandwidth'])
    if video_bitrate == "high":
        video = match_v[-1]
    elif video_bitrate == "low":
        video = match_v[0]

    widevine_check = video["widevine"]


    v = '#EXT-X-STREAM-INF:'
    v = v + 'BANDWIDTH'         + '='  +  video["m_bandwidth"] + ','
    v = v + 'AVERAGE-BANDWIDTH' + '='  +  video["bandwidth"] + ','
    v = v + 'CODECS'            + '="' +  video["codec"] + '",'
    v = v + 'RESOLUTION'        + '="' +  video["resolution"] + '",'


    mm = requests.get(video["url"],headers=headers)
    if "MAIN" in mm.text:
        l_url = fix_url(mm.text,base_url)
    else:
        l_url = video["url"]

    v = v + "\n" + l_url

    last_m3u8.append(v)

    last_m3u8 = "\n".join(last_m3u8)

    with open("decrypted/fix.m3u8", 'w') as f:
        f.write(last_m3u8)


    vu = tmpupload("decrypted/fix.m3u8")

    await message.reply_text("[download] Created m3u8: " + vu)


    ## subtitles    

    slug_title = slugify(title)
    dot_title = slug_title.replace("-", ".")

    if ct == "multiple":
        dot_title = dot_title + "."
    else:
        season = ""
        episode = ""

    dot_title = dot_title + season + episode

    downloaded_languages = []
    s = sub

    if len(s) > 0:
        await message.reply_text("[download] Downloading subtitles...")
    
    for i in range(len(s)):
        
        add_status = 1

        if s[i]["forced"] == 1 and s[i]["language"].split("-")[0].lower() not in audio_pref:
            add_status = 0

        if add_status == 1:
            code = s[i]["language"].split("-")[0]
            code = code.lower()
            try:
                code = languages.get(part1=code).part3
            except:
                code = "und"
            lang = languages.get(part3=code).name
            sub = s[i]["url"]
            sub_codec = "vtt"
            if s[i]["accessibility"] == 1:
                code = code + "1"
            if s[i]["forced"] == 1:
                code = code + "0"
            out_name = 'decrypted/' + dot_title + "-" + code + "subtitle." + sub_codec
            sub_down = ["yt-dlp","--external-downloader","aria2c", sub,"-o", out_name]
            subprocess.run(sub_down, capture_output=True, text=True)
            convert_file = ConvertFile(out_name, "utf-8")
            try:
                convert_file.convert()
                doc = 'decrypted/' + dot_title + "-" + code + "subtitle.srt"
                await message.reply_document(doc)
            except Exception as e:
                print(e)
                
            if "0" in code:
                lang = lang + "-F"
            elif "1" in code:
                lang = lang + "-SDH"
            downloaded_languages.append(lang)

        if len(downloaded_languages) > 1:
            print_languages = []
            downloaded_languages.sort()
            last_language = downloaded_languages[-1]
            for i in range(len(downloaded_languages) - 1):
                print_languages.append(downloaded_languages[i])
            s_i = ", ".join(
                print_languages
            ) + " and " + last_language + " subtitles are downloaded"

        elif len(downloaded_languages) == 1:
            s_i = downloaded_languages[0] + " subtitle is downloaded"

    if len(s) > 0:
        info_message = ["[download]", s_i]
        await message.reply_text(" ".join(info_message))            




    return vu





def fix_url(t,base_url):

    mm = t.split("\n")

    l_m3u8 = []

    whitelist = [
    "#EXTM3U","#EXT-X-VERSION",
    "#EXT-X-TARGETDURATION","#EXT-X-MEDIA-SEQUENCE",
    "#EXT-X-MAP","#EXTINF","#EXT-X-ENDLIST"]

    for i in range(len(mm)):
        tag = mm[i].split(":")[0]
        ll = mm[i]

        if  i == len(mm) - 1:
            next_info = ""
        else:
            next_info = mm[i+1]
        
        if tag in whitelist:
            ws = 1
        else:
            ws = 0

        if tag == "#EXTINF":
            if "MAIN" in next_info:
                ws = 1
            else:
                ws = 0


        if tag == "#EXT-X-MAP":
            if "MAIN" in mm[i]:
                ws = 1
            else:
                ws = 0

            if ws == 1:
                last_url = ll.split('"')[1].split('"')[0]
                ll = '#EXT-X-MAP:URI="' + base_url + "r/" +  last_url + '"'

        if "/" in tag:
            if "MAIN" in mm[i]:
                ll = base_url + "r/" + ll
                ws = 1
            else:
                ws = 0

        if ws == 1:
            l_m3u8.append(ll)


    l_m3u8 = "\n".join(l_m3u8)

    with open("decrypted/fix.m3u8", 'w') as f:
        f.write(l_m3u8)

    vu = tmpupload("decrypted/fix.m3u8")
    return vu


def find_values(drm_info,video_type):

    global pssh
    global kid

    pssh = ""
    for k in range(len(keys)):

        if keys[k]["kt"] == widevine_check:
            pssh = keys[k]["pssh"]

    kid = ""

def adapt_decryption():
    
    global wv_headers
    
    wv_headers = headers



def refresh_token(tokens,situation):

    if "blackout" in situation:
        print("[disneyplus] Blackout, bypassing...")
        proxies = proxy(region,"disneyplus")
    else:
        proxies = {}
        print("[disneyplus] Refreshing token...")
    data = {
    "grant_type": "refresh_token",
    "latitude":"0",
    "longitude":"0",
    "platform":"windows",
    "refresh_token": tokens["refresh_token"]
    }

    api_key = "ZGlzbmV5JmFuZHJvaWQmMS4wLjA.bkeb0m230uUhv8qrAXuNu39tbE_mD5EEhM_NAcohjyA"
    
    headers_r = {"authorization": "Bearer " + api_key}

    error_retries = 0
    while True:

        reflesh = requests.post("https://disney.api.edge.bamgrid.com/token", data=data, headers=headers_r,proxies=proxies)
        reflesh = reflesh.json()
        
        if "error" in reflesh:

            if "unauthorized_client" in reflesh["error"]:
                print("[disneyplus] IP Block? Trying to bypass...")
                proxies = proxy("US","disneyplus")
                if error_retries == 1:
                    return
                error_retries = error_retries + 1
                
            else:
                print("[error] [disneyplus] " + reflesh["error"] + ", " + reflesh["error_description"])
                
        else:
            expire_time = int(time.time()) + reflesh["expires_in"] - 1800

            new_tokens = {"refresh_token":reflesh["refresh_token"],"token":reflesh["access_token"],"expire":expire_time}

            with open("data/tokens/international_streaming/disney_tokens.json", 'w') as outfile:
                json.dump(new_tokens, outfile, indent=4)
            break
    return reflesh["access_token"]


def ol_status(m_ol):
    
    ol_p3 = languages.get(part1=ol).part3

    if m_ol == ol_p3:
        st = 1
    else:
        st = 0

    return st


def adapt(season, episode):

    global chapter_status
    global made_year
    global custom_title
    global descem
    g = info

    if ct == "multiple":
        not_c = content
        n = "Episode"
    elif ct == "single":
        not_c = info
        n = "Movie"

    ## tags

    tags = []

    ### from g

    ## to-do: add character info
    ## to-do: check other possible people
    cast = []
    producers = []
    directors = []
    if "participant" in g and "Actor" in g["participant"]:
        p_l = g["participant"]["Actor"]
        for i in range(len(p_l)):
            cast.append(p_l[i]["displayName"])
    if "participant" in g and "Created By" in g["participant"]:
        p_l = g["participant"]["Created By"]
        for i in range(len(p_l)):
            producers.append(p_l[i]["displayName"])
    if "participant" in g and "Director" in g["participant"]:
        p_l = g["participant"]["Director"]
        for i in range(len(p_l)):
            producers.append(p_l[i]["displayName"])

    if cast != []:
        tag = {}
        tag["name"] = "ACTOR"
        tag["value"] = ", ".join(cast)
        tag["tag_language"] = "en"
        tags.append(tag)

    if producers != []:
        tag = {}
        tag["name"] = "PRODUCER"
        tag["value"] = ", ".join(producers)
        tag["tag_language"] = "en"
        tags.append(tag)

    if directors != []:
        tag = {}
        tag["name"] = "DIRECTOR"
        tag["value"] = ", ".join(directors)
        tag["tag_language"] = "en"
        tags.append(tag)

    ## to-do: add content rating

    genres = []
    if  "typedGenres" in g and g["typedGenres"] != []:
        g_l = g["typedGenres"]
        for i in range(len(g_l)):
            genres.append(g_l[i]["name"])

    if genres != []:
        tag = {}
        tag["name"] = "GENRES"
        tag["value"] = ", ".join(genres)
        tag["tag_language"] = "en"
        tags.append(tag)    

    ## from not_c
    

    made_year = ""
    if  "releases" in not_c and not_c["releases"] != []:
        tag = {}
        made_year = g["releases"][0]["releaseDate"]

        if made_year != None:
            tag["name"] = "DATE_RECORDED"
            tag["value"] = made_year
            tag["tag_language"] = "en"
            tags.append(tag)
            made_year = made_year.split("-")[0]
        else:
            made_year = ""
    

    if "description" in not_c["text"]:
        desc = not_c["text"]["description"]["full"]

        d = "program"
        if "program" not in desc:
            for d in desc:
                break

        desc_f = desc[d]["default"]["content"]
        desc_l = desc[d]["default"]["language"]

        tag = {}
        tag["name"] = "COMMENT"
        tag["value"] = desc_f
        tag["tag_language"] = desc_l
        tags.append(tag)        

    tag = {}
    tag["name"] = "COPYRIGHT"
    tag["value"] = "Disney+"
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


    ## chapters

    ms = {}
    if "milestone" in not_c:
        ms = not_c["milestone"]
    chapter_status = chapters(n,ms)


    ## custom title

    custom_title = ""
    if  ct == "multiple" and "program" in not_c["text"]["title"]["full"]:
        ctt = not_c["text"]["title"]["full"]["program"]["default"]["content"]
        if "episode" not in slugify(ctt):
            custom_title = ctt
    descem = ""
    if  ct == "multiple" and "program" in not_c["text"]["description"]["medium"]:
        des = not_c["text"]["description"]["medium"]["program"]["default"]["content"]
        print(des)
        descem = des


def chapters(default_chapter, milestone):
    
    c = []

    tags =  ["intro_start","intro_end","recap_start","recap_end","up_next"]
    tags_dn = ["Intro",default_chapter,"Recap",default_chapter,"Credits"]

    for i in milestone:
        if i in tags:
            t = int(milestone[i][0]["milestoneTime"][0]["startMillis"])
            ms = str(t)[-3:]
            t = t / 1000
            
            na = ""
            for l in range(len(tags)):
                if tags[l] == i: 
                    na = tags_dn[l]
            if t < 15:
                t = 0
                ms = "000"

            t = chapter_timer(t, "second")
            c.append("\nCHAPTER01=" + t + "." + ms)
            c.append("\nCHAPTER01NAME=" + na)


    if c != [] and "00:00:00.000" not in c[0]:
        c_l = []
        c_l.append("\nCHAPTER01=00:00:00.000")
        c_l.append("\nCHAPTER01NAME=" + default_chapter)
        for s in c:
            c_l.append(s)
        c = c_l

    if c != [] and "CHAPTER01NAME=" not in c[-1]:
        c.append("CHAPTER01NAME=Episode")


    if c != []:
        chapter_status = 1
        file = open("data/diagnosis/chapters.txt", 'w')
        file.writelines(c)
        file.close()
    else:
        chapter_status = 0

    return chapter_status







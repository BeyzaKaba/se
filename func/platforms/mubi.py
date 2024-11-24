import requests
import json, os, sys
from slugify import slugify
from func.basics import *
import configparser
from config import MUBI_TOKEN, MUBI_BEARER

config = configparser.ConfigParser()
config.read('data/tokens/config.ini')

wget = config["binaries"]["wget"]

bearer = MUBI_TOKEN
video_codec = config["mubi"]["mubi_codec"]
prior_ct = config["mubi"]["mubi_prior"].split(", ") 
delete_ct = config["mubi"]["mubi_exclude"].split(", ") 
select_re =  config["mubi"]["mubi_regions"].split(", ") 
max_ct =  int(config["mubi"]["mubi_max_country"])



base_api = "https://api.mubi.com/v3"
search_api = base_api + "/search/films"

async def query(slug_title,results_diagnosis,available_ids,available_titles, message):
    
    regions = []
    
    with open("data/extras/mubi_regions.json") as f:
        regions_list = json.loads(f.read())

    ## add priories
    
    for items in regions_list:
        print(items)
        if items["code"] in prior_ct:
            regions.append(items["code"])

    ## add regions
    for items in regions_list:
        if items["region"] in select_re and \
        items["code"] not in delete_ct and \
        items["code"] not in regions:
            regions.append(items["code"])

    ## diminish
    regions_l = []
    for items in regions:
        if len(regions_l) < max_ct:
            regions_l.append(items)
    regions = regions_l


    for r in range(len(regions)):
        
        headers_x = {'CLIENT': 'web','Client-Country': regions[r]}
        params = {'query': slug_title,'page': '1','per_page': '30','playable': 'true',}
        q = requests.get(search_api, params=params, headers=headers_x)
        q = q.json()["films"]
        print(q)
        available_ids.append(q)
        for items in q:
            items["region"] = regions[r]

        if r == 0:
            results_diagnosis["mubi"] = q
        else:
            for i in range(len(q)):
                exist = 0
                db = results_diagnosis["mubi"]
                for t in range(len(db)):
                    if q[i]["id"] == db[t]["id"]:
                        exist = 1
                if exist == 0:
                    results_diagnosis["mubi"].append(q[i])
    

    if "mubi" in results_diagnosis:

        q = results_diagnosis["mubi"]
        for i in range(len(q)):

            on = q[i]["title"]
            dn = q[i]["original_title"]
            match = slug_title in slugify(on) or slug_title in slugify(dn)
            
            if match == True:
                
                if "mubi_release" in q[i] and q[i]["mubi_release"] == True:
                    add_info = "Original "
                
                add_info = "Movie"

                if "year" in q[i]:
                    add_info = add_info + ", " + str(q[i]["year"])

                if "duration" in q[i]:
                    add_info = add_info + ", " + str(q[i]["duration"]) + " min"

                result_title = dn.strip()

                if "historic_countries" in q[i] and q[i]["historic_countries"] != []:
                    for items in q[i]["historic_countries"]:
                        if items == "China" or items == "India":
                            result_title = on.strip()
            


def select(results_diagnosis,content_information,content_id,season):
    global title
    global ct

    q = results_diagnosis["mubi"]
    for i in range(len(q)):
        print(content_id)
        print(q[i]["id"])
        if str(content_id) == str(q[i]["id"]):
            if "original_title" in q[i]:
                title = q[i]["original_title"]
            else:
                title = q[i]["title"]
            
            content_type = "multiple"
            region = q[i]["region"]
            headers = {'CLIENT': 'web','Client-Country': "US",'Authorization': 'Bearer ' + bearer,'Client-Accept-Video-Codecs': 'vp9,h264'}
            info = requests.get('https://api.mubi.com/v3/films/' + str(content_id), headers=headers)
            info = info.json()
            print(info)
            headers = {'CLIENT': 'web','Client-Country': region,'Authorization': 'Bearer ' + bearer,'Client-Accept-Video-Codecs': 'vp9,h264'}
            auth = requests.post('https://api.mubi.com/v3/films/'+ str(content_id) +'/viewing', headers=headers)
            content = requests.get('https://api.mubi.com/v3/films/' + str(content_id)   + '/viewing/secure_url', headers=headers)
            content = content.json()

            if "code" in content and content["code"] == 50:
                
                proxies = proxy(region,"mubi")

                auth = requests.post('https://api.mubi.com/v3/films/'+ content_id +'/viewing', headers=headers, proxies=proxies)
                content = requests.get('https://api.mubi.com/v3/films/' + content_id   + '/viewing/secure_url', headers=headers, proxies=proxies)                 
                content = content.json()


    content_information["info"] = info
    content_information["content"] = content
    ct = "single"


async def download(season, episode,content_type, content_information,
                                 title, message, dil):
    global drm_status
    
    drm_status = 1
    slug_title = slugify(title)
    dot_title = slug_title.replace("-", ".")

    print(content_information)
    c = content_information["content"]


    video_url = ""    
    video_url = c["url"]
    if ".mpd" not in video_url:
        urls = c["urls"]

        for items in urls:
            if "dash" in items["content_type"]:
                video_url = items["src"]

    if video_url == "":
        await message.reply_text("fck no url")
        

    if video_codec == "hevc":
        video_url = video_url.replace("AVC1","hvc1")
    elif video_codec == "vp09":
        video_url = video_url.replace("AVC1","vp09")


    ## subtitles

    if "text_track_urls" in c and c["text_track_urls"] != []:
        await message.reply_text("Downloading subtitles")
        s = c["text_track_urls"]
        downloaded_languages = []
        
        for i in range(len(s)):
            code = s[i]["id"].split("_")[-1]
            code = languages.get(part1=code).part3
            lang = languages.get(part3=code).name
            if lang == "Turkish":
                code = s[i]["id"].split("_")[-1]
                code = languages.get(part1=code).part3
                lang = languages.get(part3=code).name
                sub = s[i]["url"]
                sub_codec = s[i]["url"].split(".")[-1]
                sub_codec = "srt"
                out_name = 'decrypted/' + dot_title + "-" + code + "subtitle." + sub_codec
                sub_down = [wget, sub, '--output-document=' + out_name]
                subprocess.run(sub_down, capture_output=True, text=True)
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

        info_message = ["INFO:", s_i]

        await message.reply_text(" ".join(info_message))

    return video_url

def adapt_decryption():
    global wv_headers
    token = MUBI_BEARER
    wv_headers = {'dt-custom-data': token}

def adapt(content_type,content_information,season,episode):
    global chapter_status
    global made_year
    chapter_status = 0
    g = content_information["info"]
    s = content_information["content"]
    n = "Movie"
    
    ## tags

    tags = []

    ### from g


    made_year = ""
    if "year" in g and g["year"] != "":
        tag = {}
        made_year = str(g["year"])
        tag["name"] = "DATE_RECORDED"
        tag["value"] = made_year
        tag["tag_language"] = "en"
        tags.append(tag)

    if "genres" in g and g["genres"] != []:
        genres = []
        genre_list = g["genres"]
        for a in range(len(genre_list)):
            d = genre_list[a]
            genres.append(d)
        tag = {}
        tag["name"] = "GENRE"
        tag["value"] = ", ".join(genres)
        tag["tag_language"] = "en"
        tags.append(tag)

    description = []
    if "short_synopsis" in g and g["short_synopsis"] != "":
        description.append(g["short_synopsis"])
    if "default_editorial" in g and g["default_editorial"] != "":
        description.append("From Mubi: " + g["default_editorial"])  
    if "industry_events" in g and g["industry_events"] != []:
        events = []
        event_list = g["industry_events"]
        for a in range(len(event_list)):
            name = event_list[a]["name"]
            add = event_list[a]["entries"][0]
            name = name + " " + add
            events.append(name)
        description.append("Awards & Festivals: " + " - ".join(events))

    if description != []:
        tag = {}
        tag["name"] = "COMMENT"
        tag["value"] = "\n\n".join(description)
        tag["tag_language"] = "en"
        tags.append(tag)        


    cast = []
    writers = []
    as_directors = []
    art_directors = []
    directors = []
    sps = []
    editors = []
    ex_producers = []
    producers = []
    cinematographers = []
    sound_engs = []
    production_designers = []
    custome_designers = []
        
    if "cast" in g and g["cast"] != []:
        people_list = g["cast"]
        for a in range(len(people_list)):
            role = slugify(people_list[a]["credits"])
            d = people_list[a]["name"]

            if "cast" in role or "self" in role:
                cast.append(d)
            if "writer" in role:
                writers.append(d)      
            if "screenplay" in role:
                sps.append(d)
            if "editor" in role:
                editors.append(d)
            if "cinematography" in role:
                cinematographers.append(d)
            if "sound" in role:
                sound_engs.append(d)
            if "production-design" in role:
                production_designers.append(d)
            if "custome-design" in role:
                custome_designers.append(d)

            if "assistant-director" in role:
                as_directors.append(d)  
            elif "art-director" in role:
                art_directors.append(d)  
            elif "director" in role:
                directors.append(d)  

            if "executive-producer" in role:
                ex_producers.append(d)               
            elif "producer" in role:
                producers.append(d)


    if cast != []:
        tag = {}
        tag["name"] = "ACTOR"
        tag["value"] = ", ".join(cast)
        tag["tag_language"] = "en"
        tags.append(tag)
    if writers != []:
        tag = {}
        tag["name"] = "WRITTEN_BY"
        tag["value"] = ", ".join(writers)
        tag["tag_language"] = "en"
        tags.append(tag)
    if as_directors != []:
        tag = {}
        tag["name"] = "ASSISTANT_DIRECTOR"
        tag["value"] = ", ".join(as_directors)
        tag["tag_language"] = "en"
        tags.append(tag)
    if art_directors != []:
        tag = {}
        tag["name"] = "ART_DIRECTOR"
        tag["value"] = ", ".join(art_directors)
        tag["tag_language"] = "en"
        tags.append(tag)
    if directors != []:
        tag = {}
        tag["name"] = "DIRECTOR"
        tag["value"] = ", ".join(directors)
        tag["tag_language"] = "en"
        tags.append(tag)
    if sps != []:
        tag = {}
        tag["name"] = "SCREENPLAY_BY"
        tag["value"] = ", ".join(sps)
        tag["tag_language"] = "en"
        tags.append(tag)
    if editors != []:
        tag = {}
        tag["name"] = "EDITED_BY"
        tag["value"] = ", ".join(editors)
        tag["tag_language"] = "en"
        tags.append(tag)
    if ex_producers != []:
        tag = {}
        tag["name"] = "EXECUTIVE_PRODUCER"
        tag["value"] = ", ".join(ex_producers)
        tag["tag_language"] = "en"
        tags.append(tag)
    if producers != []:
        tag = {}
        tag["name"] = "PRODUCER"
        tag["value"] = ", ".join(producers)
        tag["tag_language"] = "en"
        tags.append(tag)
    if cinematographers != []:
        tag = {}
        tag["name"] = "DIRECTOR_OF_PHOTOGRAPHY"
        tag["value"] = ", ".join(cinematographers)
        tag["tag_language"] = "en"
        tags.append(tag)
    if sound_engs != []:
        tag = {}
        tag["name"] = "SOUND_ENGINEER"
        tag["value"] = ", ".join(sound_engs)
        tag["tag_language"] = "en"
        tags.append(tag)
    if production_designers != []:
        tag = {}
        tag["name"] = "PRODUCTION_DESIGNER"
        tag["value"] = ", ".join(production_designers)
        tag["tag_language"] = "en"
        tags.append(tag)
    if custome_designers != []:
        tag = {}
        tag["name"] = "COSTUME_DESIGNER"
        tag["value"] = ", ".join(custome_designers)
        tag["tag_language"] = "en"
        tags.append(tag)




    ## to-do: add other age_sign
    age_sign = ""
    if "content_rating" in g and g["content_rating"] != {}:
        age_sign = g["content_rating"]["label"]
        if age_sign == "adult":
            age_sign = "TV-MA"
        elif age_sign == "caution":
            age_sign = "TV-14"

    ## to-do: add advisory
    advisory = ""

    if advisory != "":
        age_sign = age_sign + ", " + ", ".join(advisory)

    if age_sign != "":
        tag = {}
        tag["name"] = "LAW_RATING"
        tag["value"] = age_sign
        tag["tag_language"] = "en"
        tags.append(tag)


    if "historic_countries" in g and g["historic_countries"] != []:
        countries = []
        country_list = g["historic_countries"]
        for a in range(len(country_list)):
            d = country_list[a]
            countries.append(d)
        tag = {}
        tag["name"] = "RECORDING_LOCATION"
        tag["value"] = ", ".join(countries)
        tag["tag_language"] = "en"
        tags.append(tag)


    tag = {}
    tag["name"] = "COPYRIGHT"
    tag["value"] = "Mubi"
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

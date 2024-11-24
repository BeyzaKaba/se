import requests, sys, subprocess, string, platform
import os
import configparser
import glob
import json, base64, time, random
from slugify import slugify
from iso639 import languages
from func.basics import *
from func.messages import *
from func.proxy import proxy

config = configparser.ConfigParser()
config.read('data/tokens/config.ini')

display_language = "tr"

wget = config["binaries"]["wget"]
mp4box = config["binaries"]["mp4box"]
base_api = 'https://cms-api.exxen.com/api'
search_api = base_api + '/GetItemResults'
content_api = base_api + '/GetItemById'
play_api = base_api + '/GetFilteredVideos'

base_url = 'https://www.exxen.com'
main_url = "https://www.exxen.com/tr"
signin_url = 'https://www.exxen.com/en/sign-in'
profile_url = 'https://www.exxen.com/en/Profile/change?profileId='
signin_api = "https://api-crm.exxen.com/membership/login/email"
exxen_key = "5f07276b91aa33e4bc446c54a9e982a8"


proxies = {}
headers = {
    'user-agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (Ktesttemp, like Gecko) Chrome/90.0.4430.85 Safari/537.36',
    'Content-Type': 'application/json;charset=utf-8',
}


async def query(title,sr,at,ip_data,message):

    global q
    
    if len(title) <= 2:
        await message.reply_text("[exxen] Minimum 3 characters needs for search, skipping")
        return
        
    json = {'contentTypes': [6,5,15],
        'text': title,
        'pageIndex': 0,
        'pageSize': 999,
        'language': display_language,
    }

    q = requests.post(search_api, headers=headers, json=json)

    q = q.json()["Items"]
    
    sr["exxen"] = q

    for i in range(len(q)):

        m = q[i]["Filters"]
        
        on = ""
        dn = ""
        for t in range(len(m)):
            if m[t]["NameSpace"] == "original_name":
                on = m[t]["Value"]
            if m[t]["NameSpace"] == "displaytitle":
                dn = m[t]["Value"]
        
        match = slugify(title) in slugify(on) or slugify(title) in slugify(dn)
        
        if match == False:
            continue

        add_info = []

        for t in q[i]["ParentCategories"]:
            match1 = t["Tags"] == [] and q[i]["Name"] not in t["Name"]
            if match1 == True: 
                add_info.append(t["Name"])

        if on != "":
            result_title = on
        elif dn != "":
            result_title = dn
        else:
            result_title = q[i]["Name"].strip()

        r = {}
        r["title"] = result_title
        r["meta"] = add_info
        r["platform"] = "exxen"
        r["id"] = q[i]["AssetId"]
        at.append(r)


def select(ci, cid, season):
    
    global title
    global ct
    global competition_status
    global wv_server
    global info
    global content_all
    global is_event

    wv_server = "https://wv-proxy.ercdn.com/api/erproxy"
    
    is_event = False
    for i in range(len(q)):
        if cid == q[i]["AssetId"]:
            title = q[i]["Name"].strip()
            if q[i]["ContentType"][0]["Id"] == 5:
                ct = "multiple"
            elif q[i]["ContentType"][0]["Id"] == 15:
                ct = "single"
                is_event = True
            else:
                ct = "single"

    params = {'id': cid,'language': 'tr'}
    info = requests.get(content_api,
                                params=params,
                                headers=headers)
    info = info.json()
    ci["info"] = info

    if ct == "multiple":

        categories = []
        cat = ci["info"]["Category"]
        for i in range(len(cat)):
            category_id = cat[i]["Id"]
            categories.append(category_id)

        data = {
            'categories': categories,
            'contentTypes': ['1'],
            'sortDirection': 'ASCE',
            'customSortField': 'episode_number',
            'sortType': 'custom',
            'language': 'tr',
            'PageSize': "999",
        }

        content_all = requests.post(play_api,
                                     json=data,
                                     headers=headers).json()

        season_titles = []

        for items in content_all["Items"]:
            season_status = 0
            episode_status = 0

            if "-onceki-bolumler" in items["EncodedURL"]:
                if season == "0":
                    for t in range(len(items["Metadata"])):
                        l = items["Metadata"][t]
                        if l["NameSpace"] == "season" and \
                        l["Value"].lstrip("0") == "1":
                            season_status = 1
                        if l["NameSpace"] == "episode_no_in_season" and \
                        l["Value"].lstrip("0") != "":
                            episode_status = 1

            else:
                for t in range(len(items["Metadata"])):
                    l = items["Metadata"][t]
                    if l["NameSpace"] == "season" and \
                    l["Value"].lstrip("0") == season:
                        season_status = 1
                    if l["NameSpace"] == "episode_no_in_season" and \
                    l["Value"].lstrip("0") != "" and \
                    "fragman" not in items["EncodedURL"] and\
                    "trailer" not in items["EncodedURL"]:
                        episode_status = 1

            if season_status == 1 and episode_status == 1:
                season_titles.append(items)

        if season_titles == []:
            print("exxen no season!")

        content_all = season_titles
        ci["content"] = season_titles

    elif is_event == True:

        categories = []
        cat = ci["info"]["Category"]
        for i in range(len(cat)):
            category_id = cat[i]["Id"]
            categories.append(category_id)

        data = {
            'categories': categories,
            'contentTypes': ['16'],
            'sortDirection': 'ASCE',
            'customSortField': 'episode_number',
            'sortType': 'custom',
            'language': "tr",
            'PageSize': "999",
        }

        content_all = requests.post(play_api,
                                     json=data,
                                     headers=headers)
        content_all = content_all.json()["Items"]
        ci["content"] = content_all

async def download(season, episode, message, dil):
    
    global drm_status
    global content
    global is_partly
    global video_urls
    global selected_part

    drm_status = 1
    slug_title = slugify(title)
    dot_title = slug_title.replace("-", ".")

    is_partly = False
    video_url = ""
    if ct == "multiple":

        find_content = 0
        c = content_all
        for i in range(len(c)):
            m = c[i]["Metadata"]
            for t in range(len(m)):
                if m[t]["NameSpace"] == "episode_no_in_season" and\
                m[t]["Value"].lstrip("0") == episode:
                    v = c[i]["CdnUrls"]
                    for u in range(len(v)):
                        if v[u]["ContentType"] == 13:
                            content = c[i]
                            video_url = v[u]["ContentUrl"]
                            break
    elif is_event == True:

        selected_part = 0
        video_urls = []
        parts = ["1-devre","2-devre"]
        parts_display = ["First Half","Second Half"]
        for p in range(len(parts)):
            part = parts[p]
            for items in content_all:
                if part in items["EncodedURL"]:
                    v = items["CdnUrls"]
                    for u in range(len(v)):
                        if v[u]["ContentType"] == 13:
                            video_url = v[u]["ContentUrl"]
                    video_urls.append({"url":video_url,"name":parts_display[p],"type":part})
        video_url = video_urls
        if len(video_url) > 1:
            is_partly = True

    elif ct == "single":
        v = info["CdnUrls"]
        for u in range(len(v)):
            if v[u]["ContentType"] == 13:
                video_url = v[u]["ContentUrl"]
                break

    extra = [episode,season,ct]
    if video_url == "" or video_url == []:
        await message.reply_text("[error] No video url found")
        

    extra.append(title)

    ## subtitles

    if ct == "multiple":
        subs = content["SubtitleUrls"]
        dot_title = dot_title + "."
    elif ct == "single":
        subs = info["SubtitleUrls"]

    dwn_lang = []
    subs = []
    for t in range(len(subs)):
        sub_code = subs[t]["SubtitleName"]
        sub_code = languages.get(part1=sub_code).part3
        sub_lang = languages.get(part3=sub_code).name
        sub_url = subs[t]["SubtitleUrl"]
        sub_codec = sub_url.split(".")[-1]
        out_name = 'decrypted/' + dot_title + season + episode + "-" + sub_code + "subtitle." + sub_codec
        sub_down = subprocess.run(
            [wget, sub_url, "--output-document=" + out_name],
            capture_output=True,
            text=True)
        dwn_lang.append(sub_lang)

    if len(dwn_lang) > 1:
        await message.reply_text("[download] "+ ", ".join(dwn_lang) + " subtitles are downloaded")

    return video_url


def account_check():


    with open("data/accounts/exxen/accounts.json") as f:
        accounts = json.loads(f.read())

    ## input accounts
    accs = open("data/accounts/exxen/input.txt").read().split("\n")
    if accs == [""]:
        accs = []

    ## add expired to check list
    remove_list = []
    for items in accounts:
        if items["expire"] < int(datetime.utcnow().timestamp()):
            accs.append(items["username"] + ":" + items["password"])
            remove_list.append(items)
    for items in remove_list:
        if items in accounts:
            accounts.remove(items)

    if accs == []:
        return

    accs_l = []
    for acc in accs:
        if "Subscription - " in acc:
            acc = acc.split("Subscription - ")[1]
        acc = acc.split("|")[0].strip()
        accs_l.append(acc)
    accs = accs_l

    remove_list = []
    for i in range(len(accs)):

        if ":" not in accs[i]:
            continue

        d = accs[i]
        d = d.split("|")[0].strip()
        email = d.split(":")[0].strip()
        password = d.split(":")[1].strip()

        acc_info = {'Email': email,'Password': password}
        signin_params = {"key":exxen_key}

        retries = 0
        while True:
            try:
                response = requests.post(signin_api,data=acc_info,params=signin_params).json()
            except:
                retries = retries + 1
                if retries == 5:
                    continue
            else:
                break

        ## if successfully get response remove acc to readd
        for items in accounts:
            if items["username"] == email:
                remove_list.append(items)

        ## bad username/password
        if response["Success"] == False:
            continue

        response = response["Result"]["Products"]

        ## no package
        if response == []:
            continue

        has_sport = False
        for items in response:
            addon_name = items["LicenseName"]
            if "Spor" in addon_name:
                has_sport = True
                break
        expire = date_to_ts(items["LicenseEndDate"]) - 60 * 60 * 3 ## switch utc
        acc = {"username":email,"password":password,"expire":expire,"has_sport":has_sport}
        accounts.append(acc)
    accounts = sorted(accounts, key=lambda i: i['expire'],reverse=True)

    for items in remove_list:
        if items in accounts:
            accounts.remove(items)

    with open("data/accounts/exxen/input.txt", 'w') as f:
        f.write("")
    with open("data/accounts/exxen/accounts.json", 'w') as outfile:
        json.dump(accounts, outfile, indent=4)


def refresh_token(tokens):

    ## add/review accounts
    

    print("[exxen] Refreshing token...")

    with open("data/accounts/exxen/accounts.json") as f:
        accounts = json.loads(f.read())

    find_status = 0
    remove_list = []

    for k in range(len(accounts)):

        username = accounts[k]["username"]
        password = accounts[k]["password"]

        if url_type == "sport" and accounts[k]["has_sport"] == False:
            continue

        while True:
            session = requests.Session()
            device_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=22))
            signin = session.post(signin_url)
            
            if "csrf" in signin.cookies:
                csrf = signin.cookies["csrf"]
                break
            else:
                session.close()
                print("[exxen] Startup error, trying again...")
                print(" ".join(warning_message))
                pass

        cookies = {'lang': 'en', 'csrf': csrf, "d_id": device_id}

        request_token = signin.text.split(
            '<input name="__RequestVerificationToken" type="hidden" value="'
        )[1].split('"')[0]

        data = {
            '__RequestVerificationToken': request_token,
            '__reCAPTCHAVerificationToken': '',
            'Email': username,
            'Password': password,
            'RememberMe': 'true',
        }

        signin = session.post(signin_url, cookies=cookies, data=data)

        if "u-p-s" not in signin.cookies:
            print("[exxen] Account " + username + " is not working, trying again...")
            remove_list.append(accounts[k])
        else:
            ups = signin.cookies["u-p-s"]
            
            for i in range(len(signin.history)):

                if "exxen" in signin.history[i].cookies:
                    exxen_token = signin.history[i].cookies["exxen"]
                if "u_rmb" in signin.history[i].cookies:
                    rmb = signin.history[i].cookies["u_rmb"]

            profile_id = signin.text.split("changeprofile('")[1].split("'")[0]
            
            cookies = {
                'lang': 'en',
                'csrf': csrf,
                'exxen': exxen_token,
                'd_id': device_id,
                'u_rmb': rmb,
                'u-p-s': ups,
                'cookieconsent_status': 'dismiss'
            }

            profile_info = session.post(profile_url + profile_id, cookies=cookies)
            back_to_home = session.get('https://www.exxen.com/tr',cookies=cookies)
            print(back_to_home.text.split("var AuthCheck = ")[1])
            if "var AuthCheck = true" in back_to_home.text:
                find_status = 1
                expire = int(time.time()) + 14440 - 300

                tokens["token"] = exxen_token
                tokens["profile"] = profile_id
                tokens["expire"] = expire
                tokens["has_sport"] = accounts[k]["has_sport"]

                with open("data/tokens/turkey/exxen.json", 'w') as outfile:
                    json.dump(tokens, outfile, indent=4)
                break
            else:
                remove_list.append(accounts[k])
                pass

    for items in remove_list:
        if items in accounts:
            accounts.remove(items)

    with open("data/accounts/exxen/accounts.json", 'w') as outfile:
        json.dump(accounts, outfile, indent=4)

    if find_status == 0:
        print("[error] [exxen] No Account, stopping")

    return tokens


def adapt_decryption():

    global wv_headers
    global proxies
    global selected_part
    global url_type

    base_url = "https://www.exxen.com/tr/watch-"

    if ct == "multiple":
        url_type = "serie"
        c = content
    elif is_event == True:
        url_type = "sport"

        encode_identifier = video_urls[selected_part]["type"]
        for items in content_all:
            if encode_identifier in items["EncodedURL"]:
                c = items
                break
        selected_part = selected_part + 1

    else:
        url_type = "movie"
        c = info

    encoded_url = c["EncodedURL"]
    encode_id = c["AssetId"]

    exxen_url = base_url + url_type + "/" + encoded_url + "/" + encode_id

    with open("data/tokens/turkey/exxen.json") as f:
        tokens = json.loads(f.read())

    ## add situation
    if url_type == "sport" and tokens["has_sport"] == False:
        tokens = refresh_token(tokens)
    if tokens["expire"] < int(time.time()):
        tokens = refresh_token(tokens)

    cookies = {}
    cookies["lang"] = "en"
    cookies["exxen"] = tokens["token"]
    profile_id = tokens["profile"]

    while True:

        session = requests.Session()
        select_user = session.post(profile_url + profile_id, cookies=cookies,proxies=proxies)
        video_settings = session.get(exxen_url, cookies=cookies,proxies=proxies)
        video_settings = video_settings.text.split(
            "var videoProperties = ")[-1].split(";")[0]
        
        video_settings = json.loads(video_settings)
        drm_ticket = video_settings["playerModel"]["drmTicket"]
        
        if drm_ticket != None:
            break

        error_code = video_settings["playerModel"]["errorCode"]
        if error_code == "00014":
            proxies = proxy("TR","exxen")
        elif error_code == "0009":
            print("[error] No subscription found")
            sys.exit(0)
        else:
            print("[error] " + video_settings["playerModel"]["message"])
            sys.exit(0)
    wv_headers = {'x-erdrm-message': drm_ticket}

def chapters(chapter_name, chapter_end, platform):

    chapters = []
    if platform == "exxen":
        chapters.append("CHAPTER01=00:00:00.000\n")
        chapters.append("CHAPTER01NAME=" + chapter_name + "\n")
        chapters.append("CHAPTER02=" + chapter_timer(chapter_end, "second") +
                        ".000\n")
        chapters.append("CHAPTER02NAME=Credits")
    else:
        chapters.append("CHAPTER01=00:00:00.000\n")
        chapters.append("CHAPTER01NAME=First Half\n")
        chapters.append("CHAPTER02=" + chapter_timer(chapter_end, "second") +
                        ".000\n")
        chapters.append("CHAPTER02NAME=Second Half")

    file = open("data/diagnosis/chapters.txt", 'w')
    for items in chapters:
        file.writelines([items])
    file.close()


def adapt(season, episode):
    global chapter_status
    global custom_title
    global made_year
    global event_name
    global event_date
    global descem

    g = info

    if ct == "multiple":
        not_c = content
        n = "Episode"
    else:
        not_c = info
        n = "Movie"


    if is_event == True:

        for items in content_all:
            if "1-devre" in items["EncodedURL"]:
                not_c = items
                break

        metas = info["Metadata"]

        ## displays

        displays = []
        comp = ""
        for meta in metas:
            if meta["NameSpace"] == "championships":
                comp = meta["Value"]
        for meta in metas:
            if meta["NameSpace"] == "sporseason":
                comp = comp + " " + meta["Value"].split("-")[-1]
        if comp != "":
            displays.append(comp)

        for meta in metas:
            if meta["NameSpace"] == "round_week":

                week = meta["Value"]

                if ".Hafta" in week:
                    week = "Week " + week[0]
                displays.append(week)
        
        event_name = ", ".join(displays)

        event_date = ""
        for meta in metas:
            if meta["NameSpace"] == "kickofftime":
                event_date = meta["Value"]
                event_date = event_date[:4] + "-" + event_date[4:6] + "-" + event_date[6:8]
        if event_date == "":
            event_date = not_c["CreateDate"].split("T")[0]


        ## tags

        tags = []

        if "Description" in g:
            
            tag = {}
            tag["name"] = "COMMENT"
            tag["value"] = g["Description"]
            tag["tag_language"] = display_language
            tags.append(tag)

        tag = {}
        tag["name"] = "GENRE"
        tag["value"] = "SPORT"
        tag["tag_language"] = "en"
        tags.append(tag)

        tag = {}
        tag["name"] = "COPYRIGHT"
        tag["value"] = "EXXEN"
        tag["tag_language"] = "en"
        tags.append(tag)

        tag = {}
        tag["name"] = "DISTRIBUTED_BY"
        tag["value"] = "QUT"
        tag["tag_language"] = "en"
        tags.append(tag)

        tag = {}
        tag["name"] = "DATE_RECORDED"
        tag["value"] = event_date
        tag["tag_language"] = "en"
        tags.append(tag)

        tag_start()

        for i in range(len(tags)):
            nm = tags[i]["name"]
            v = tags[i]["value"]
            l = tags[i]["tag_language"]
            add_tag(nm, v, l)

        tag_end()
        
        chapter_status = 0
        custom_title = ""
        made_year = event_date.split("-")[0]
        
        return




    ## tags

    tags = []

    ### from g

    m = g["Metadata"]

    ctt = ""
    if "ParentCategories" in g and g["ParentCategories"] != []:
        t = g["ParentCategories"]
        en = g["EncodedURL"]
        for i in t:
            if en not in i["UrlEncodedName"]:
                ctt = i["Name"]
    if ctt != "":
        tag = {}
        tag["name"] = "ct"
        tag["value"] = ctt
        tag["tag_language"] = "en"
        tags.append(tag)

    cast = []
    for i in range(len(m)):
        dnn = m[i]["NameSpace"]
        if dnn == "cast":
            person = m[i]["Value"]
            cast.append(person)
    if cast != []:
        tag = {}
        tag["name"] = "ACTOR"
        tag["value"] = ", ".join(cast)
        tag["tag_language"] = "en"
        tags.append(tag)

    director = []
    for i in range(len(m)):
        dnn = m[i]["NameSpace"]
        if dnn == "director":
            person = m[i]["Value"]
            director.append(person)
    if director != []:
        tag = {}
        tag["name"] = "DIRECTOR"
        tag["value"] = ", ".join(director)
        tag["tag_language"] = "en"
        tags.append(tag)

    writer = []
    for i in range(len(m)):
        dnn = m[i]["NameSpace"]
        if dnn == "writer":
            person = m[i]["Value"]
            writer.append(person)
    if writer != []:
        tag = {}
        tag["name"] = "WRITTEN_BY"
        tag["value"] = ", ".join(writer)
        tag["tag_language"] = "en"
        tags.append(tag)

    producer = []
    for i in range(len(m)):
        dnn = m[i]["NameSpace"]
        if dnn == "producer":
            person = m[i]["Value"]
            producer.append(person)
    if producer != []:
        tag = {}
        tag["name"] = "PRODUCER"
        tag["value"] = ", ".join(producer)
        tag["tag_language"] = "en"
        tags.append(tag)

    made_year = ""
    for i in range(len(m)):
        dnn = m[i]["NameSpace"]
        if dnn == "made_year":
            made_year = m[i]["Value"]

    if made_year != "":
        tag = {}
        tag["name"] = "DATE_RECORDED"
        tag["value"] = made_year
        tag["tag_language"] = "en"
        tags.append(tag)

    age_sign = ""
    advisory = []
    if "parentalRating" in g and g["parentalRating"] != "":
        for i in range(len(m)):
            dnn = m[i]["NameSpace"]
            if dnn == "smart_signs":
                v = m[i]["Value"]
                if "Genel İzleyici" in v:
                    age_sign = "0"
                elif "Yaş" in v:
                    age_sign = v.split(" ")[0]
                elif "Cinsellik" in v:
                    advisory.append("S")
                elif "Olumsuz" in v:
                    advisory.append("L")
                elif "Korku" in v:
                    advisory.append("V")
    if age_sign.isdigit() == True:
        age_sign = int(age_sign)
        if 18 <= age_sign:
            age_sign = "TV-MA"
        elif 12 <= age_sign < 18:
            age_sign = "TV-14"
        elif 7 <= age_sign < 12:
            age_sign = "TV-PG"
        elif age_sign < 7:
            age_sign = "TV-G"

    if advisory != []:
        age_sign = age_sign + ", " + ", ".join(advisory)

    if age_sign != "":
        tag = {}
        tag["name"] = "LAW_RATING"
        tag["value"] = age_sign
        tag["tag_language"] = "en"
        tags.append(tag)

    ### from not_c

    m = not_c["Metadata"]

    air_date = ""
    for i in range(len(m)):
        dnn = m[i]["NameSpace"]
        if dnn == "AirDate":
            air_date = m[i]["Value"].split(".")
            air_date.reverse()
            air_date = "-".join(air_date)
    if air_date != "":
        tag = {}
        tag["name"] = "DATE_RELEASED"
        tag["value"] = air_date
        tag["tag_language"] = "en"
        tags.append(tag)

    if "Description" in not_c and not_c["Description"] != "":
        tag = {}
        description = not_c["Description"]
        tag["name"] = "COMMENT"
        tag["value"] = description
        tag["tag_language"] = "tr"
        tags.append(tag)
        
    descem = not_c["Description"]

    tag = {}
    tag["name"] = "DISTRIBUTED_BY"
    tag["value"] = "QUT"
    tag["tag_language"] = "en"
    tags.append(tag)

    tag = {}
    tag["name"] = "COPYRIGHT"
    tag["value"] = "Exxen"
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

    chapter_status = 0
    for i in range(len(m)):
        dnn = m[i]["NameSpace"]
        if dnn == "ending_time":
            chapter_status = 1
            ce = m[i]["Value"]

    platform = "exxen"
    if chapter_status == 1:
        chapters(n, ce, platform)

    ## custom title

    custom_title = ""
    for i in range(len(m)):
        dnn = m[i]["NameSpace"]
        if dnn == "displaytitle" and\
        " - " in m[i]["Value"]:
            ctt = m[i]["Value"].split(" - ")
            if len(ctt) == 2:
                ctt = ctt[-1]
            else:
                fct = " ".join(ctt)
                for t in range(len(ctt)):
                    if "bolum" in slugify(ctt[t]):
                        fct = ", ".join(ctt[t + 1:])
                        break
                ctt = fct
            custom_title = ctt
        ## to-do : find proper way to eliminate unwanted info



def combine_parts(content_list,content):

    videos = []
    audios = []
    l_list = []
    for items in content_list:
        if "video" in items:
            videos.append(items)
        elif "audio" in items:
            print(items)
            audios.append(items)
        else:
            l_list.append(items)

    videos = natural_sort(videos)
    audios = natural_sort(audios)
    audio_codec = audios[0].split("-")[1].split("audio")[0]

    videos_pre = videos
    audios_pre = audios

    videos = " -cat ".join(videos)
    audios = " -cat ".join(audios)

    combine_video = [mp4box,"-quiet" ,"-cat", videos,"-new","decrypted/" + content + "video.mp4"]
    combine_video = " ".join(combine_video)
    print("[combine] Combining video parts to one file")
    os.system(combine_video)
    combine_audio = [mp4box,"-quiet" ,"-cat", audios,"-new","decrypted/" + content + audio_codec + "audio.m4a"]
    combine_audio = " ".join(combine_audio)
    print("[combine] Combining audio parts to one file")
    os.system(combine_audio)

    for items in videos_pre:
        os.remove(items)
    for items in audios_pre:
        os.remove(items)

    l_list = l_list + glob.glob("decrypted/" + content + "video.mp4")
    l_list = l_list + glob.glob(("decrypted/" + content + "*audio.m4a"))
    
    return l_list









import requests, sys
from slugify import slugify
from func.basics import *
from func.messages import *
from func.proxy import *

base_api = "https://api.gainapis.com/v2"
query_api = base_api + "/search"
season_api = base_api + "/content/season"
video_base = base_api + "/content/media/manifests/"

headers = {'user-agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (Ktesttemp, like Gecko) Chrome/90.0.4430.85 Safari/537.36',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
}

async def query(title,sr,at,ip_data,message):

    global q
    global proxies

    proxies = {}
    mc = ip_data["country"].upper()
    if mc != "TR" and title.lower().endswith(" tr") == True:
        title = " ".join(title.split(" ")[:-1])
        proxies = proxy("TR","gain")

    params = {'keyword': title}
    q = requests.get(query_api, headers=headers, params=params,proxies=proxies)
    q = q.json()["data"]["titles"]

    for i in range(len(q)):

        if slugify(title) in slugify(q[i]["metadata"]["name"]):

            meta = q[i]["metadata"]
            add_info = []

            if "isGainOriginals" in meta and meta["isGainOriginals"] == True:
                add_info.append("ORIGINAL")

            if "category" in meta:
                add_info.append(category_translate(meta["category"]))

            r = {}
            r["title"] = meta["name"].strip()
            r["meta"] = add_info
            r["platform"] = "gain"
            r["id"] = q[i]["id"]
            at.append(r)

def select(ci, cid, season):
    global title
    global ct
    global wv_server
    global info
    global content_all

    wv_server = ""
    proxies = {}


    for items in q:
        if cid == items["id"]:
            info = items
            ci["info"] = items
            title = items["metadata"]["name"]
            break

    headers_e = headers.copy()
    headers_e["X-App-Language"] = "EN"
    params = {'titleId': cid}
    seas = requests.get(season_api, params=params, headers=headers_e, proxies=proxies).json()["data"]["seasonInfo"]

    single_types = ["Film"]
    if seas == None or info["metadata"]["category"] in single_types:
        ct = "single"
        content_all = []
    else:
        ct = "multiple"

        has_season = False
        avail_seasons = []
        for sea in seas:
            avail_seasons.append(str(sea["seasonNumber"]))
            if sea["seasonNumber"] == int(season):
                has_season = True
                sea_id = sea["seasonId"]
                break
        if has_season == False:
            print("[error] Season is not available, available ones: " + ", ".join(avail_seasons))
            sys.exit(0)

        ## get episodes
        params = {'seasonId': sea_id}
        eps = requests.get(season_api, params=params, headers=headers_e, proxies=proxies).json()["data"]["episodes"]
        content_all = []
        for ep in eps:
            if ep["episodeNumber"] == 0:
                continue
            content_all.append(ep)

    ci["content"] = content_all


async def download(season, episode, message, dil):
    
    global drm_status
    global content

    drm_status = 0

    video_url = ""
    if ct == "single":
        t = info["id"]
        content = []
        video_url = video_base + t + ".m3u8"
    else:
        c = content_all
        for i in range(len(c)):
            if c[i]["episodeNumber"] == int(episode):
                content = c[i]
                video_url = video_base + c[i]["mediaId"] + ".m3u8"

    if video_url == "":
        await message.reply_text("[error] No video url")

    ## check existence of video url
    vd = requests.get(video_url,proxies=proxies).text
    if "file not found" in vd.lower():
        await message.reply_text("[error] File not found")
        

    ## subtitles

    slug_title = slugify(title)
    dot_title = slug_title.replace("-", ".")

    if ct == "multiple":
        dot_title = dot_title + "."
    else:
        season = ""
        episode = ""

    dot_title = dot_title + season + episode

    subs = []
    dwld_subs = []
    sub_data = requests.get(video_url).text.split("\n")

    for items in sub_data:
        if "#EXT-X-MEDIA:TYPE=SUBTITLES" in items:

            sub = {}
            sub["language"] = items.split('LANGUAGE="')[1].split('"')[0]
            sub["url"] = items.split('URI="')[1].split('"')[0]

            sub["accessibility"] = False
            if "public.accessibility" in items:
                sub["accessibility"] = True
          
    s = subs
    if len(s) > 0:
        await message.reply_text("[download] Downloading subtitles...")

    for i in range(len(s)):

        code = s[i]["language"].split("-")[0]
        code = code.lower()
        try:
            code = languages.get(part1=code).part3
        except:
            code = "und"
        lang = languages.get(part3=code).name
        sub = s[i]["url"]
        sub_codec = sub.replace(".m3u8","").replace(".mp4","").split(".")[-1]
        if s[i]["accessibility"] == True:
            code = code + "1"
        out_name = 'decrypted/' + dot_title + "-" + code + "subtitle." + sub_codec
        sub_down = ["yt-dlp","--external-downloader","aria2c", sub,"-o", out_name]
        subprocess.run(sub_down, capture_output=True, text=True)

        ## fix subtitle
        sub_txt = open(out_name, encoding="utf8").read()
        sub_txt = sub_txt.replace("WEBVTT\nX-TIMESTAMP-MAP=LOCAL:00:00:00.000,MPEGTS:63000\n\n","")
        unwanted_chars = ["<b>","</b>","</i>","</i>"]
        for char in unwanted_chars:
            sub_txt = sub_txt.replace(char,"")

        sub_txt = sub_txt.split("\n\n")
        sub_ltxt = []
        for items in sub_txt:
            if items not in sub_ltxt:
                sub_ltxt.append(items)
        sub_txt = "WEBVTT\n\n" + "\n\n".join(sub_ltxt)
        with open(out_name, 'w') as f:
            f.write(sub_txt)

        if "0" in code:
            lang = lang + "-F"
        elif "1" in code:
            lang = lang + "-SDH"
        dwld_subs.append(lang)

    if len(dwld_subs) > 0:
        await message.reply_text("[download] " + ", ".join(dwld_subs) + " is downloaded")


    return video_url


def chapters(chapter_name, intro_start, intro_end, credits_start):
    
    chapter_status = 0
    chapters = []

    if intro_start != 0 or intro_end == 0:
        chapter_status = 1
        chapters.append("CHAPTER01=00:00:00.000\n")
        chapters.append("CHAPTER01NAME=" + chapter_name + "\n")

    if intro_end != 0:
        chapter_status = 1
        chapters.append("CHAPTER02=" + chapter_timer(intro_start, "second") +
                        ".000\n")
        chapters.append("CHAPTER02NAME=Intro\n")
        chapters.append("CHAPTER03=" + chapter_timer(intro_end, "second") +
                        ".000\n")
        chapters.append("CHAPTER03NAME=" + chapter_name + "\n")

    if credits_start != 0:
        chapter_status = 1
        chapters.append("CHAPTER04=" + chapter_timer(credits_start, "second") +
                        ".000\n")
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

    g = info["metadata"]

    if ct == "multiple":
        not_c = content["metadata"]
        n = "Episode"
    elif ct == "single":
        s = g
        not_c = g
        n = "Movie"

    ## tags

    tags = []

    ### from g

    if "category" in g and g["category"] != "":
        tag = {}
        content_x = g["category"]
        tag["name"] = "CONTENT_TYPE"
        tag["value"] = category_translate(content_x)
        tag["tag_language"] = "en"
        tags.append(tag)

    age_sign = ""
    advisory = []
    if "contentRatings" in g and g["contentRatings"] != []:
        sign = " ".join(g["contentRatings"])

        if "content18" in sign:
            age_sign = "TV-MA"
        elif "content13" in sign:
            age_sign = "TV-14"
        elif "content7" in sign:
            age_sign = "TV-PG"
        elif "contentAll" in sign:
            age_sign = "TV-G"

        if "contentSexuality" in sign:
            advisory.append("S")
        if "contentNegative" in sign:
            advisory.append("L")
        if "contentViolence" in sign:
            advisory.append("V")

    if advisory != []:
        age_sign = age_sign + ", " + ", ".join(advisory)

    if age_sign != "":
        tag = {}
        tag["name"] = "LAW_RATING"
        tag["value"] = age_sign
        tag["tag_language"] = "en"
        tags.append(tag)

    ### from not_c

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

    tag = {}
    tag["name"] = "COPYRIGHT"
    tag["value"] = "Gain"
    tag["tag_language"] = "en"
    tags.append(tag)


    tag_start()

    for i in range(len(tags)):
        nm = tags[i]["name"]
        v = tags[i]["value"]
        l = tags[i]["tag_language"]
        add_tag(nm, v, l)

    tag_end()


    ## not available
    
    made_year = ""

    ## chapters

    i_s = 0
    i_e = 0
    c_s = 0

    if "playerMediaMetaData" in content:
        chp_info = content["playerMediaMetaData"]
        if chp_info["startIntro"] != None:
            i_s = chp_info["startIntro"]
        if chp_info["introDuration"] != None:
            i_e = i_s + chp_info["introDuration"]
        if chp_info["skipNextEpisode"] != None:
            c_s = i_s + chp_info["skipNextEpisode"]


    chapter_status = chapters(n, i_s, i_e, c_s)

    ## custom_title

    custom_title = ""
    print(not_c)
    possible = not_c["name"].split(" - ")[-1]
    if "bolum" not in slugify(possible):
        custom_title = possible
    descem = not_c["description"]

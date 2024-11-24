import requests
import json
import xmltodict
from subprocess import check_output
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
import time
import subprocess
import math
import os
PRGRS = {}
from PIL import Image
import pyrogram
from config import POSTA, PASS, LOG_CHANNEL, CAP
import subprocess
trtdigitaltest = '3cdaf5f04d9449e0b9c82b9a08f1bb1a'
from iso639 import languages
import glob
from func.upload import tg_upload
from pywidevine.cdm import Cdm
from pywidevine.device import Device
from pywidevine.pssh import PSSH
bad_key = "00000000000000000000000000000000"
import os
import asyncio

def getdurnodrm(video):
    input_filename = video

    out = subprocess.check_output(["ffprobe", "-v", "quiet", "-show_format", "-print_format", "json", input_filename])

    ffprobe_data = json.loads(out)
    duration_seconds = ffprobe_data["format"]["duration"]
    if "." in duration_seconds:
        dur = duration_seconds.split(".")[0]
    else:
        dur = duration_seconds
    print(dur)
    return dur
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

def get_ticket(videoid):
    bearer = get_bearer()
    url = f"https://eu1.tabii.com/apigateway/entitlement/v1/ticket/{videoid}"
    headers = {
        'authority': 'eu1.tabii.com',
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'tr',
        'authorization': f'Bearer {bearer}',
        'content-type': 'application/json',
        'origin': 'https://www.tabii.com',
        'platform': 'web',
        'referer': 'https://www.tabii.com/',
        'sec-ch-ua': '"Google Chrome";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'trtdigitaltest': trtdigitaltest,
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
    }
    r = requests.get(url, headers=headers).json()
    ticket = r["ticket"]
    return ticket
    
def get_keys(mpd, kalite):
    r = requests.get(mpd).text
    if int(kalite) == 1080:
        videokid = r.split('height="1080"')[1].split('cenc:default_KID="')[1].split('"')[0].replace("-", "")
        print(videokid)
    else:
        videokid = r.split('maxHeight="720"')[1].split('cenc:default_KID="')[1].split('"')[0].replace("-", "")
        print(videokid)
    audiokid = r.split('contentType="audio"')[1].split('cenc:default_KID="')[1].split('"')[0].replace("-", "")
    print(audiokid)
    pssh = r.split('pssh>')[1].split('<')[0]
    return videokid, audiokid, pssh

def get_profilid(accessToken):
    headers = {
        'authority': 'eu1.tabii.com',
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'tr',
        'authorization': f'Bearer {accessToken}',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://www.tabii.com',
        'platform': 'web',
        'referer': 'https://www.tabii.com/',
        'sec-ch-ua': '"Google Chrome";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'trtdigitaltest': trtdigitaltest,
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
    }
    responsez = requests.get(
        "https://eu1.tabii.com/apigateway/profiles/v2/",
        headers=headers,
    )
    # sk profil id
    z:dict = json.loads(responsez.text)

    profilecount = z.get('count')
    for i in z.get('data'):
        if not i.get('kids'):
            profile_id = i.get('SK')
            print(f"{profilecount} adet profil bulundu. seçilen: {i.get('name')} ({i.get('maturityLevel')})")
            return profile_id

def get_bearer():
    mail = POSTA
    password = PASS

    session = requests.Session()
    headers = {
        'authority': 'eu1.tabii.com',
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'tr',
        'content-type': 'application/json',
        'origin': 'https://www.tabii.com',
        'platform': 'web',
        'referer': 'https://www.tabii.com/',
        'sec-ch-ua': '"Google Chrome";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'trtdigitaltest': trtdigitaltest,
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
    }

    json_data = {
        'email': mail,
        'password': password,
        'remember': False,
    }

    response = session.post('https://eu1.tabii.com/apigateway/auth/v2/login', headers=headers, json=json_data)

    y = json.loads(response.text)

    accessToken = y['accessToken']
    refreshToken = y['refreshToken']
    headers = {
        'authority': 'eu1.tabii.com',
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'tr',
        'authorization': f'Bearer {accessToken}',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://www.tabii.com',
        'platform': 'web',
        'referer': 'https://www.tabii.com/',
        'sec-ch-ua': '"Google Chrome";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'trtdigitaltest': trtdigitaltest,
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
    }

    responses = session.post('https://eu1.tabii.com/apigateway/auth/v2/token/verify', headers=headers)

    a = json.loads(responses.text)

    headers = {
        'authority': 'eu1.tabii.com',
        'accept': '*/*',
        'accept-language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
        'access-control-request-headers': 'authorization,content-type,platform,trtdigitaltest',
        'access-control-request-method': 'POST',
        'origin': 'https://www.tabii.com',
        'referer': 'https://www.tabii.com/',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
    }


    accountId = a['accountId']


    headers = {
        'authority': 'eu1.tabii.com',
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'tr',
        'authorization': f'Bearer {accessToken}',
        'content-type': 'application/json',
        'origin': 'https://www.tabii.com',
        'platform': 'web',
        'referer': 'https://www.tabii.com/',
        'sec-ch-ua': '"Google Chrome";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'trtdigitaltest': trtdigitaltest,
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
    }

    json_data = {
        'refreshToken': refreshToken,
    }
    profil_id = get_profilid(accessToken)
    uri = f'https://eu1.tabii.com/apigateway/profiles/v2/' + profil_id + '/token'

    responsez = session.post(uri, headers=headers, json=json_data)

    z = json.loads(responsez.text)
    accessTokenz = z['accessToken']

    return accessTokenz

def get_seasons(id):
    url = f"https://eu1.tabii.com/apigateway/catalog/v1/show/{id}"
    bearer = get_bearer()
    headers = {
        'authority': 'eu1.tabii.com',
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'tr',
        'authorization': f'Bearer {bearer}',
        'content-type': 'application/json',
        'origin': 'https://www.tabii.com',
        'platform': 'web',
        'referer': 'https://www.tabii.com/',
        'sec-ch-ua': '"Google Chrome";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'trtdigitaltest': trtdigitaltest,
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
    }
    r = requests.get(url, headers=headers).json()
    ne = r["data"]["contentType"]
    if ne == "series":
        seasons = r["data"]["seasons"]
    else:
        seasons = r["data"]["currentContent"] 
    print(len(seasons))
    title = r["data"]["title"]
    desce = r["data"]["description"]
    for i in r["data"]["images"]:
         if i["imageType"] == "mainWithLogo":
             imagep = i["name"]
             image = f"https://cms-tabii-public-image.tabii.com/int/w3840/q900//w200/{imagep}"
    return seasons, title, ne, desce, image
    
def download_video(mpd,kalite,encv_name):
    opt = ["yt-dlp", "-F", "--allow-unplayable-formats", mpd]

    options = subprocess.run(opt, capture_output=True, text=True)
    if "ERROR" in options.stderr:
        print("[error] " + options.stderr.split(";")[0])
    options = options.stdout
    options = options.split("---\n")[-1].split("\n")

    quality_videos = []
    quality = kalite
    for i in range(len(options)):
        if "x" + str(quality) in options[i]:
            quality_videos.append(options[i].split("|")[1] + "|" + options[i].split("|")[0])
        quality_videos.sort(reverse=True)
    if quality_videos == []:
        print(str(quality) + "p video Yok...")
        return
    if quality_videos != []:
        for items in quality_videos:
            dash_f = items.split("|")[1].split(" ")[0]
            output_name = encv_name
            video_down = [
                "yt-dlp", "--external-downloader", "aria2c",
                "--progress","--no-warnings", "-q", '-f', dash_f,
                "--allow-unplayable-format", mpd, "-o", output_name
                 ]
            print(f"{quality}p Video İndiriliyor...")
            video_run = subprocess.run(video_down)
    return output_name

def download_audio(mpd, istenen,enca_name):
    opt = ["yt-dlp", "-F", "--allow-unplayable-formats", mpd]

    options = subprocess.run(opt, capture_output=True, text=True)
    if "ERROR" in options.stderr:
        print("[error] " + options.stderr.split(";")[0])
    options = options.stdout
    options = options.split("---\n")[-1].split("\n")

    for i in range(len(options)):
        format_id = options[i].split(" ")[0]
        lp = convert_lang(options[i])
        print(lp)
        lang_code = lp.split(",")[0]
        lang = lp.split(",")[1] 
        if istenen == "tr":
            iste = "tur"
        if lang_code == iste:
            output_name = enca_name
            audio_down = [
                "yt-dlp", "--external-downloader", "aria2c", 
                "--progress","--no-warnings", "-q", '-f', format_id,
                "--allow-unplayable-format", mpd, "-o", output_name
            ]
            print(f"{lang} Ses İndiriliyor.. ")
            audio_run = subprocess.run(audio_down)
        return output_name

def get_dec_keys(videokid, audiokid, pssh, widevine_url):
    pssh_wv = PSSH(pssh) 
    devices = glob.glob("data/devices/*.wvd")
    device_location = devices[0]
    device = Device.load(device_location)
    cdm = Cdm.from_device(device)
    session_id = cdm.open()
    challenge = cdm.get_license_challenge(session_id, pssh_wv)
    headers = {
        'user-agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (Ktesttemp, like Gecko) Chrome/90.0.4430.85 Safari/537.36'
    }
    license_data = challenge
    widevine_headers = headers
    widevine_license = requests.post(
        url=widevine_url,
        data=license_data,
        headers=widevine_headers)
    wv_c = widevine_license.content
    cdm.parse_license(session_id,wv_c)
    keys = []
    for key in cdm.get_keys(session_id):
       if key.type == "CONTENT" and key.key.hex() != bad_key:
           keys.append(f"{key.kid.hex}:{key.key.hex()}")
    cdm.close(session_id) 
    print(keys)
    if len(keys) == 1:
        kid = keys[0].split(":")[0]
        audiodecryption_key = keys[0].split(":")[1]
        videodecryption_key = keys[0].split(":")[1]
    else:
        for t in range(len(keys)):
            if audiokid == keys[t].split(":")[0]:
                audiodecryption_key = keys[t].split(":")[1]
            if videokid == keys[t].split(":")[0]:
                videodecryption_key = keys[t].split(":")[1]
    return videodecryption_key, audiodecryption_key

def decrypt_video_audio(videodecryption_key,audiodecryption_key,enc_video,enc_audio,videokid,audiokid,dec_vid,dec_aud):
    video = dec_vid
    stream_type = "video"
    videodecrypt = [
            "packager", "--quiet", "input=" + enc_video + ",stream=" +
            stream_type + ",output=" + video,
            "--enable_raw_key_decryption", "--keys",
            "label=0:key_id=" + videokid + ":key=" + videodecryption_key
        ]
    print("Video Şifresi Çözülüyor")
    decrypt = subprocess.run(videodecrypt, capture_output=True, text=True)
    if "Error" in decrypt.stderr:
        print("[error] " + decrypt.stderr)

    audio = dec_aud
    stream_tpe = "audio"
    audiodecrypt = [
            "packager", "--quiet", "input=" + enc_audio + ",stream=" +
            stream_tpe + ",output=" + audio,
            "--enable_raw_key_decryption", "--keys",
            "label=0:key_id=" + audiokid + ":key=" + audiodecryption_key
        ]
    print("Ses Şifresi Çözülüyor")
    auddecrypt = subprocess.run(audiodecrypt, capture_output=True, text=True)
    if "Error" in auddecrypt.stderr:
        print("[error] " + auddecrypt.stderr)
    return video, audio

def birlestir(name,video,audio,desc):
    name = name.upper().replace(" ", ".")
    command = f"mkvmerge -q --disable-track-statistics-tags {video} {audio} -o {name}"
    print("Video ve Ses birleştiriliyor..")
    birlestirme = os.system(command)
    os.remove(audio)
    os.remove(video)
    return name

def cevireng(metin):
    önceki_karakterler = ["ş",
                          "ç",
                          "ö",
                          "ğ",
                          "ü",
                          "ı",
                          "Ş",
                          "Ç",
                          "Ö",
                          "Ğ",
                          "Ü",
                          "İ"]

    sonraki_karakterler = ["s",
                          "c",
                          "o",
                          "g",
                          "u",
                          "i",
                          "S",
                          "C",
                          "O",
                          "G",
                          "U",
                          "I"]
    for i in range(12):
         metin=metin.replace(önceki_karakterler[i],sonraki_karakterler[i]).replace(" ", ".").replace(":", ".")
    return metin

def download_nodrm(mpd,kalite,encv_name):
    opt = ["yt-dlp", "-F", "--allow-unplayable-formats", mpd]

    options = subprocess.run(opt, capture_output=True, text=True)
    if "ERROR" in options.stderr:
        print("[error] " + options.stderr.split(";")[0])
    options = options.stdout
    options = options.split("---\n")[-1].split("\n")

    quality_videos = []
    quality = kalite
    for i in range(len(options)):
        if "x" + str(quality) in options[i]:
            quality_videos.append(options[i].split("|")[1] + "|" + options[i].split("|")[0])
        quality_videos.sort(reverse=True)
    if quality_videos == []:
        print(str(quality) + "p video Yok...")
        return
    if quality_videos != []:
        for items in quality_videos:
            dash_f = items.split("|")[1].split(" ")[0]
            output_name = encv_name.upper()
            video_down = [
                "yt-dlp", "--external-downloader", "aria2c",
                "--progress","--no-warnings", "-q", '-f', dash_f,
                "--allow-unplayable-format", mpd, "-o", output_name
                 ]
            print(f"{quality}p Video İndiriliyor...")
            video_run = subprocess.run(video_down)
    return output_name

async def download_tabi(id, kalite, istenen, msg, message, season,episodes,last_episodes, userbot):
    accessToken = get_bearer()
    headers = {
        'authority': 'eu1.tabii.com',
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'tr',
        'authorization': f'Bearer {accessToken}',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://www.tabii.com',
        'platform': 'web',
        'referer': 'https://www.tabii.com/',
        'sec-ch-ua': '"Google Chrome";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'trtdigitaltest': trtdigitaltest,
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
    }

    id

    url = f"https://eu1.tabii.com/apigateway/search/v1?Limit=5&PageNumber=1&Search={id}"

    r = requests.get(url,headers=headers).json()

    sonuclar = []
    for q in r["data"]:
        js = {}
        js["name"] = q["title"]
        js["id"] = q["id"]
        js["tur"] = q["contentType"]
        sonuclar.append(js)

    text = ""
    say = 1
    for i in sonuclar:
        text += f"{say}- {i['name']} - {i['tur']}\n"
        say += 1

    await message.reply_text(text)
    secilen = await message.chat.ask("seç birini:")
    secti = int(secilen.text) - 1
    print(f"Seçilen: {sonuclar[secti]['name']}\nid: {sonuclar[secti]['id']}")
    sezonlar, title, ne, desce, image = get_seasons(sonuclar[secti]['id'])
    await msg.edit("Bölümler Alındı..")
    bolumler = []
    caption = f"{title}\n\n{desce}"
    try:
        ali = await message.reply_photo(
            photo=image,
            caption=f"{title}\n\n||{desce}||"
        )
        await ali.copy(LOG_CHANNEL)
    except Exception as e:
        print(e)
        a = await message.reply_text(f"{image}\n\n{title}\n\n||{desce}||")
        await a.copy(LOG_CHANNEL)
    if 1 == 1:
        say = 0
        bosay = 0
        for sezon in sezonlar:
            if ne == "movie":
                if say == 1:
                    return
            say += 1 
            print(ne)
            
            bolumler = []
            if ne == "series":
                sezonsay = sezon["seasonNumber"] 
                print(len(sezon["episodes"]))
                for b in sezon["episodes"]:
                    if int(sezonsay) == int(season):
                        bosay += 1
                    if episodes == "" and int(last_episodes) == 0:
                        if int(sezonsay) == int(season):
                            bolumler.append(b)
                    elif episodes != "":
                        if int(sezonsay) == int(season):
                            n = b["episodeNumber"]
                            bolumum = episodes
                            if int(n) == int(bolumum):
                                bolumler.append(b)
                if int(last_episodes) != 0:
                    sonlar = last_episodes
                    istedigim = int(bosay) - int(sonlar)
                    esksay = 0
                    if int(sezonsay) == int(season):
                        for b in sezon["episodes"]:
                            esksay += 1
                            if esksay > istedigim:
                                bolumler.append(b)
            elif ne == "movie":
                sezonsay = 1
                bolumler.append(sezonlar)
            
            else:
                await message.reply_text("Bunu çekemiyorum..")
            for bolum in bolumler:
                if ne == "series":
                    sayi = bolum["episodeNumber"]
                else:
                    sayi = 1
                if bolum["media"][0]["drmSchema"] != "clear":
                    resource_id = bolum["media"][0]["resourceId"]
                    ticketid = bolum["id"]
                    ticket = get_ticket(ticketid)
                    await msg.edit("Ticket Alındı..")
                    if "mpd" in bolum["media"][0]["url"]:
                        mpuri = bolum["media"][0]["url"]
                    else:
                        mpuri = bolum["media"][1]["url"]
                    mpd = f"https://eu1.tabii.com/apigateway/pbr/v1/media{mpuri}?width=-1&height=-1&bandwidth=-1&subtitleType=vtt"
                    videokid, audiokid, pssh = get_keys(mpd,kalite)
                    await msg.edit("Keyler Alındı..")
                    widevine_url = f"https://eu1.tabii.com/apigateway/drm/v1/wv?ticket={ticket}&resource_id={resource_id}"
                else:
                    mpuri = bolum["media"][0]["url"]
                    mpd = f"https://eu1.tabii.com/apigateway/pbr/v1/media{mpuri}"
                etitle = cevireng(title)
                encv_name = f"{etitle}.{sezonsay}-{sayi}.enc.video.mp4"
                await msg.edit("Video İndiriliyor..")
                if bolum["media"][0]["drmSchema"] != "clear":
                    enc_video = download_video(mpd, kalite, encv_name)
                else:
                    if int(sayi) < 10: 
                        namee = f"{title}.S0{sezonsay}E0{sayi}.{kalite}P.WEB-DL.H264-TR.mkv"
                    else:
                        namee = f"{title}.S0{sezonsay}E{sayi}.{kalite}P.WEB-DL.H264-TR.mkv"
                    name = cevireng(namee)
                    video = download_nodrm(mpd, kalite, name)
                    isim2 = video.replace(".mkv", ".mp4").upper()
                if bolum["media"][0]["drmSchema"] != "clear":
                    await msg.edit("Ses İndiriliyor..")
                    enca_name = f"{etitle}.{sezonsay}-{sayi}.enc.audio.m4a"
                    enc_audio = download_audio(mpd, istenen, enca_name)
                    await msg.edit("Şifreler Çözülüyor..")
                    videodecryption_key, audiodecryption_key = get_dec_keys(videokid, audiokid, pssh, widevine_url)
                    print("Decryption Keyler alındı...")
                    print(videodecryption_key)
                    print(audiodecryption_key)
                    dec_vid = f"{etitle}.{sezonsay}-{sayi}.dec.video.mp4"
                    dec_aud = f"{etitle}.{sezonsay}-{sayi}.dec.audio.m4a"
                    video, audio = decrypt_video_audio(videodecryption_key,audiodecryption_key,enc_video,enc_audio,videokid,audiokid,dec_vid,dec_aud)
                    await msg.edit("Video ve Ses Birleştiriliyor..")
                    if ne == "series":
                        if int(sayi) < 10: 
                            name = f"{title}.S0{sezonsay}E0{sayi}.{kalite}P.WEB-DL.H264-TR.mkv"
                        else:
                            name = f"{title}.S0{sezonsay}E{sayi}.{kalite}P.WEB-DL.H264-TR.mkv"
                    else:
                        name = f"{title}.{kalite}P.WEB-DL.H264-TR.mkv"
                    isim = cevireng(name)
                    isim2 = isim.replace(".mkv", ".mp4").upper()
                if ne == "series":
                    desc = bolum["description"]
                else:
                    desc = desce
                if bolum["media"][0]["drmSchema"] != "clear":
                    video = birlestir(isim,video,audio,desc)
                start_time = time.time()
                print(video)
                try:
                    os.rename(video, isim2) 
                except Exception as e:
                    await message.reply_text(e)
                video = isim2
                if CAP.lower() == "true":
                    print("l")
                else:
                    desc = ""
                await tg_upload(message,video,desc)
                if bolum["media"][0]["drmSchema"] != "clear":
                    os.remove(enc_video)
                    os.remove(enc_audio)
                

    return video



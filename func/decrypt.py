import json, requests, re, glob
import argparse, xmltodict
import subprocess, base64, random
import configparser, importlib
from slugify import slugify
from pywidevine.cdm import Cdm
from pywidevine.device import Device
from pywidevine.pssh import PSSH
from func.basics import *
from func.messages import *

config = configparser.ConfigParser()
config.read('data/tokens/config.ini')

shaka_limit = int(config["decrypt"]["shaka_limit"])
packager = config["binaries"]["packager"]
mp4decrpyt = config["binaries"]["mp4decrypt"]

http_proxy = config["proxy"]["https"]
https_proxy = config["proxy"]["https"]

headers = {
    'user-agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (Ktesttemp, like Gecko) Chrome/90.0.4430.85 Safari/537.36'
}

bad_key = "00000000000000000000000000000000"


async def decrypt(content_list, content_type, i, title, platform,
                    widevine_server, content_information,season,episode,message):


    slug_title = slugify(title)
    dot_title = slug_title.replace("-", ".")
    
    media_list = content_list[i].replace('\\', "/").replace(
        "encrypted/", "").replace(".mp4", "").replace(".m4a", "")
    video_type = media_list.split("-")[1]

    if video_type[-1].isdigit() == True:
        part = video_type[-1]
        video_type = video_type[:-1]
    else:
        part = ""

    if content_type == "multiple":
        dot_title = dot_title + "."


    drm_info = "encrypted/" + dot_title + season + episode + "-drm" + part + ".key"
    await message.reply_document(drm_info)
    inits_main = ["exxen","dsmartgo","mubi","claro"]
    inits_special = ["disneyplus","nbatv"]
    inits = inits_main + inits_special

    if platform not in inits_main and platform not in inits:
        
        drm_info = open(drm_info)

        drm_info = xmltodict.parse(drm_info.read()) 

    ## find pssh and kid

    pl = "func.platforms." + platform
    module = importlib.import_module(pl)

    if platform in inits_main:
        pssh = find_values(drm_info,platform)
        kid = ""
    else:
        module.find_values(drm_info,video_type)
        kid = module.kid
        pssh = module.pssh

    ## decrypt

    decryption_key = ""
    cache_status = 0

    ## local database

    with open("data/extras/cached_keys.json") as f:
        cached_keys = json.loads(f.read())

    for u in range(len(cached_keys)):
        if pssh == cached_keys[u]["pssh"]:
            keys = cached_keys[u]["keys"]
            if len(keys) == 1:
                kid = keys[0].split(":")[0]
                decryption_key = keys[0].split(":")[1]
            else:
                for t in range(len(keys)):
                    if kid == keys[t].split(":")[0]:
                        decryption_key = keys[t].split(":")[1]

    if decryption_key != "":
        cache_status = 1
        await info("decrypt","foundkey","local",message)

    ## GET READY

    widevine_headers = headers
    proxies = {} 
    cookies = {}
    params = {}

    extra_headers = [
    "beinturkey","exxen","dsmartgo","mubi","tainiothiki",
    "vix","disneyplus","nbatv","hbomax",
    "f1tv","paramountplus","optussport",
    "peacock","fubotv"
    ]
    extra_server = ["vix","claro","hulu","hbomax","f1tv","starz","paramountplus","dazn","optussport","peacock"]
    extra_license = ["claro","channel4","tidal"]
    extra_proxy = ["dsmartgo","claro","kablotv","paramountplus","exxen"]
    extra_cookies = ["kablotv","dsmartgo"]
    extra_params = ["starz","tidal"]
    extra_json_response = ["channel4","tidal"]
    extras = extra_headers + extra_server + extra_license + extra_proxy 
    extras = extras + extra_cookies + extra_params + extra_json_response

    if decryption_key == "" and platform in extras:
        module.adapt_decryption()

        if platform in extra_headers:
            widevine_headers = module.wv_headers
        if platform in extra_server:
            widevine_server = module.wv_server
        if platform in extra_license:
            license_data = module.wv_data
            license_name = module.wv_key
        if platform in extra_proxy:
            proxies = module.proxies
        if platform in extra_cookies:
            cookies = module.cookies
        if platform in extra_params:
            params = module.wv_params
        if platform in extra_json_response:
            licenser_name = module.wvr_name

    if decryption_key == "":

        pssh_wv = PSSH(pssh) 
        devices = glob.glob("data/devices/*.wvd")
        device_location = devices[0]
        device = Device.load(device_location)
        cdm = Cdm.from_device(device)
        session_id = cdm.open()
        challenge = cdm.get_license_challenge(session_id, pssh_wv)

        if platform in extra_license:
            widevine_body = base64.b64encode(challenge)
            widevine_body = widevine_body.decode('utf-8')
            license_data[license_name] = widevine_body
            widevine_license = requests.post(url=widevine_server,
                                             json=license_data,
                                             headers=widevine_headers,
                                             params=params,
                                             proxies=proxies)
        else:
            license_data = challenge
            widevine_license = requests.post(url=widevine_server,
                                             data=license_data,
                                             headers=widevine_headers,
                                             params=params,
                                             cookies=cookies,
                                             proxies=proxies)
        wv_c = widevine_license.content
        print(wv_c)
        if platform in extra_json_response:
            wv_c = bytes.decode(wv_c)
            wv_c = json.loads(wv_c)
            wv_c = wv_c["payload"]
            wv_c = wv_c
        if platform == "mubi":
            wc = widevine_license.text.split('"license":"')[1].split('"')[0]
            print(wc)
            wv_c = wc

        cdm.parse_license(session_id,wv_c)
        keys = []
        for key in cdm.get_keys(session_id):
            if key.type == "CONTENT" and key.key.hex() != bad_key:
                keys.append(f"{key.kid.hex}:{key.key.hex()}")
        cdm.close(session_id) 

        if keys == []:
            await message.reply_text("[error] No key found")   
        wv_response = {"pssh": pssh, "keys": keys}

        cached_keys.append(wv_response)
        if len(keys) == 1:
            kid = keys[0].split(":")[0]
            decryption_key = keys[0].split(":")[1]
        else:
            for t in range(len(keys)):
                if kid == keys[t].split(":")[0]:
                    decryption_key = keys[t].split(":")[1]
        
        if decryption_key != "":
            await info("decrypt","requestkey","pywidevine",message)

    if decryption_key == "":
        extra = content_list[i].replace("\\", "/").replace("encrypted/","")
        await error("decrypt","nokey",extra,message)

    ## save keys to local

    final_caches = []
    for dic in cached_keys:
        if dic not in final_caches:
            final_caches.append(dic)

    with open("data/extras/cached_keys.json", 'w') as outfile:
        json.dump(final_caches, outfile, indent=4)

    ## decrypt content

    input_name = content_list[i].replace("\\", "/")
    output_name = 'decrypted/' + content_list[i].replace("\\", "/").replace(
        "encrypted/", "")

    if "audio" in input_name:
        stream_type = "audio"
    elif "video" in input_name:
        stream_type = "video"

   
    await info("decrypt","start",input_name.replace("encrypted/", ""),message)
    if 1 == 1:
        method = "shaka"
        decrypt = [
            "shakapackager", "--quiet", "input=" + input_name + ",stream=" +
            stream_type + ",output=" + output_name,
            "--enable_raw_key_decryption", "--keys",
            "label=0:key_id=" + kid + ":key=" + decryption_key
        ]

    else:
        method = "bento"
        decrypt = [
            "mp4decrypt", "--key", kid + ":" + decryption_key, input_name,
            output_name
        ]
    decrypt = subprocess.run(decrypt, capture_output=True, text=True)
    if "Error" in decrypt.stderr:
        await message.reply_text("[error] " + decrypt.stderr)




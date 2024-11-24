import requests
from pywidevine.cdm import Cdm
from pywidevine.device import Device
from pywidevine.pssh import PSSH
import glob
bad_key = "00000000000000000000000000000000"
from iso639 import languages
import subprocess
import os
from func.upload import tg_upload
from pyrogram import Client, filters 
import asyncio
import os
import time
sira = []
import asyncio
import ffmpeg
from subprocess import check_output

import time
import math
PRGRS = {}
from config import LOG_CHANNEL, userbot

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


@Client.on_message(filters.command('mpd'))
async def giris(bot, message):
  sira.append(message)
  if len(sira) == 1:
    await blumpd(bot, sira[0])
  else:
    msg = await message.reply_text(f"İşlem Sıraya Eklendi Sıran: {len(sira)}")
      
      
async def sirakontrol(bot):
  del sira[0]
  if len(sira) > 0:
    await blumpd(bot, sira[0])
    
async def blumpd(bot, message):
  try:
    wv_server = "https://wdvn.blutv.com/"
    mpd = message.text.split(" ")[1]
    mpdistek = requests.get(mpd)
    audiokid = mpdistek.text.split('contentType="audio"')[1].split('default_KID="')[1].split('"')[0].replace("-", "")
    videokid = mpdistek.text.split('maxHeight="1080"')[1].split('default_KID="')[1].split('"')[0].replace("-", "")
    print(audiokid)
    print(videokid)
    pssh = mpdistek.text.split('pssh>')[1].split('<')[0]
    print(pssh)
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
        url=wv_server,
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
        decryption_key = keys[0].split(":")[1]
    else:
        for t in range(len(keys)):
            if audiokid == keys[t].split(":")[0]:
                audiodecryption_key = keys[t].split(":")[1]
            if videokid == keys[t].split(":")[0]:
                videodecryption_key = keys[t].split(":")[1]
    print(audiodecryption_key)
    print(videodecryption_key)
    opt = ["yt-dlp", "-F", "--allow-unplayable-formats", mpd]

    options = subprocess.run(opt, capture_output=True, text=True)
    if "ERROR" in options.stderr:
        await message.reply_text("[error] " + options.stderr.split(";")[0])
    options = options.stdout
    options = options.split("---\n")[-1].split("\n")
    istenen = message.text.split(" ")[2]

    #Ses Seçtirip İndirtme
    
    for i in range(len(options)):
        format_id = options[i].split(" ")[0]
        lp = convert_lang(options[i])
        print(lp)
        lang_code = lp.split(",")[0]
        lang = lp.split(",")[1] 
        if lang_code == istenen:
            output_name = "sifrelises.m4a"
            audio_down = [
                "yt-dlp", "--external-downloader", "aria2c", 
                "--progress","--no-warnings", "-q", '-f', format_id,
                "--allow-unplayable-format", mpd, "-o", output_name
            ]
            await message.reply_text(f"{lang} Ses İndiriliyor.. ")
            audio_run = subprocess.run(audio_down)
    # İstenilen Kaliteyi Seçip İndirtme
    quality_videos = []
    quality = message.text.split(" ")[3]
    for i in range(len(options)):
        if "x" + str(quality) in options[i]:
            quality_videos.append(options[i].split("|")[1] + "|" + options[i].split("|")[0])
        quality_videos.sort(reverse=True)
    if quality_videos == []:
        await message.reply_text(str(quality) + "p video Yok...")
        return
    if quality_videos != []:
        for items in quality_videos:
            dash_f = items.split("|")[1].split(" ")[0]
            output_name = "sifrelivideo.mp4"
            video_down = [
                "yt-dlp", "--external-downloader", "aria2c",
                "--progress","--no-warnings", "-q", '-f', dash_f,
                "--allow-unplayable-format", mpd, "-o", output_name
                 ]
            await message.reply_text(f"{quality}p Video İndiriliyor...")
            video_run = subprocess.run(video_down)
    input_name =  "sifrelises.m4a"
    output_name = "sifresizses.m4a"
    ses = "sifresizses.m4a"
    audiodecrypt = [
            "packager", "--quiet", "input=" + input_name + ",stream=" +
            "audio" + ",output=" + output_name,
            "--enable_raw_key_decryption", "--keys",
            "label=0:key_id=" + audiokid + ":key=" + audiodecryption_key
    ]
    await message.reply_text("Ses Şifresi Çözülüyor...")
    decrypt = subprocess.run(audiodecrypt, capture_output=True, text=True)
    if "Error" in decrypt.stderr:
        await message.reply_text("[error] " + decrypt.stderr)
    os.remove(input_name)
    input_name =  "sifrelivideo.mp4" 
    output_name = "sifresizvideo.mp4"
    video = "sifresizvideo.mp4"
    videodecrypt = [
            "packager", "--quiet", "input=" + input_name + ",stream=" +
            "video" + ",output=" + output_name,
            "--enable_raw_key_decryption", "--keys",
            "label=0:key_id=" + videokid + ":key=" + videodecryption_key
        ]

    await message.reply_text("Video Şifresi Çözülüyor...")
    decrypt = subprocess.run(videodecrypt, capture_output=True, text=True)
    if "Error" in decrypt.stderr:
        await message.reply_text("[error] " + decrypt.stderr)
    os.remove(input_name)
    if len(message.text.split(" ")) == 5:
        out_location = message.text.split(" ")[4]
    else:
        out_location = "video.mp4"
    command = [
            'ffmpeg','-hide_banner',
            '-i',video,
            '-i',ses,
            '-map','0:v','-map','1:a',
            '-c:v','copy',
            '-y',out_location
            ]
    await message.reply_text("Video ve Ses birleştiriliyor..")
    process = subprocess.run(command, capture_output=True, text=True)
    os.remove(video)
    os.remove(ses)
    msg = await message.reply_text("Yükleniyor..")
    video = out_location
    desc = ""
    await tg_upload(message,video,desc)
    await sirakontrol(bot)
  except Exception as e:
    await message.reply_text(e)
    await sirakontrol(bot)
     
    
    
            


    

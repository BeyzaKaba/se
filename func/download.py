import glob, requests, re, os, subprocess
import configparser
from iso639 import languages
from slugify import slugify
from func.messages import *
from func.basics import *
import importlib, time
from func.platforms.puhu import fix_output
config = configparser.ConfigParser()
config.read('data/tokens/config.ini')

wget = config["binaries"]["wget"]
proxy = config["proxy"]["https"].split("/")[-1]
http_proxy = config["proxy"]["http"]
https_proxy = config["proxy"]["https"]
no_aria = config["general"]["no_aria"].split(", ")


async def download(video_url, quality, season, episode, title, platform,
             content_type, drm_status,message, dil):

    slug_title = slugify(title)
    dot_title = slug_title.replace("-", ".")

    if content_type == "multiple":
        dot_title = dot_title + "."

    if drm_status == 0:
        output_folder = "decrypted"
    else:
        output_folder = "encrypted"

    ## pre-download adjustments

    partly = ["vix"]
    
    ol_availables = ["disneyplus","hbomax"]
    url_diminish = ["disneyplus","fox","kablotv","fubotv","espnplus","paramountplus","dsmartgo"]
    options_diminish = [
    "vix","starz","hulu","hbomax","f1tv","kanald",
    "blutv","starz","channel4","paramountplus","euroleaguetv",
    "ufcfightpass","dazn","nflgamepass","nbatv","masterclass","tidal","udacity","edx","fubotv","dsmartgo"]
    audio_platforms = ["trtaudio"]
    multi_kids =["hbomax","blutv","tainiothiki"]
    adapt_multiples = ["f1tv"]
    possible_expire = ["nflgamepass","euroleaguetv","ufcfightpass","nbatv"]
    music_streaming = ["tidal"]

    if platform in url_diminish:
        pl = "func.platforms." + platform
        module = importlib.import_module(pl)
        video_url = await module.adapt_url(quality,season,episode,message)

        if platform == "disneyplus":
            quality = module.quality_l

    if platform in music_streaming:
        pl = "func.platforms." + platform
        module = importlib.import_module(pl)
        if module.is_video == False:
            audio_platforms.append(platform)

    ## yt-dlp check options

    if type(video_url) != list:
        video_urls = [{"url":video_url,"name":"main"}]
    else:
        video_urls = video_url
        
    print(video_urls)
    
    for v in range(len(video_urls)):

        video_url = video_urls[v]["url"]
        video_name = video_urls[v]["name"]

        if video_name != "main":
            print("[download] Downloading: " + video_name.split(" - ")[0])

        opt = ["yt-dlp", "-F", "--allow-unplayable-formats", video_url]

        options = subprocess.run(opt, capture_output=True, text=True)
        
        if "ERROR" in options.stderr:
            print("[error] " + options.stderr.split(";")[0])
        options = options.stdout
        options = options.split("---\n")[-1].split("\n")
        print(options)
        if platform in options_diminish and v == 0:
            pl = "func.platforms." + platform
            module = importlib.import_module(pl)
            options = module.options_fix(options)

        if platform in adapt_multiples and v != 0:
            pl = "func.platforms." + platform
            module = importlib.import_module(pl)
            options = module.adapt_multiples(options,video_urls[v])

        ## audios
        print(options)
        print(platform)
        for i in range(len(options)):

            if platform != "gain" and "audio" in options[i]:

                format_id = options[i].split(" ")[0]
                lp = convert_lang(options[i])
                print(lp)
                
                lang_code = lp.split(",")[0]
                lang = lp.split(",")[1]
                part = ""
                #####################
                tur_platformlar = ["exxen", "blutv"]
                if platform in tur_platformlar:
                    if platform == "blutv":
                        istenen = [f"{dil}"]
                    else:
                        istenen = ["tur"]
                elif platform == "mubi":
                    istenen = [f"{dil}"]
                else:
                    istenen = [f"{lang_code}"]
                if lang_code in istenen:
                    if len(video_urls) > 1:
                        part = str(v)

                    ol_s = 0
                    if platform in ol_availables:
                        pl = "func.platforms." + platform
                        module = importlib.import_module(pl)
                        ol_s = module.ol_status(lang_code)
                    if ol_s == 1:
                        lang_code = lang_code

                    if platform == "disneyplus":
                        output_folder = "decrypted"


                #####################

                    output_name = output_folder + "/" + dot_title + season + episode + "-" + lang_code + "audio" + part + ".m4a"

                    audio_down = [
                        "yt-dlp", "--external-downloader", "aria2c", 
                        "--progress","--no-warnings", "-q", '-f', format_id,
                        "--allow-unplayable-format", video_url, "-o", output_name
                    ]

                #####################

                    if platform in no_aria:
                        audio_down[1] = "--concurrent-fragments"
                        audio_down[2] = "30"
                    if platform == "tidal" and format_id == "mp4":
                        audio_down.remove("-f")
                        audio_down.remove(format_id)
                    if v != 0 and platform == "f1tv" and video_urls[v]["type"] == "obc":
                        lang = "Team Radio"

                #####################

                    await info("download", "audiod", lang, message)
                    audio_run = subprocess.run(audio_down)


        ## videos

        #####################

        if platform == "disneyplus":
            output_folder = "encrypted"
        if platform in possible_expire:
            expire = video_url.split('exp=')[1].split("~")[0]
            if expire.isdigit() == True:
                expire = int(expire) - int(time.time())
                if expire < 10:
                    pl = "func.platforms." + platform
                    module = importlib.import_module(pl)
                    video_url = module.refresh_url()                

        #####################

        quality_videos = []

        for i in range(len(options)):
            if "x" + str(quality) in options[i]:
                quality_videos.append(options[i].split("|")[1] + "|" +
                                      options[i].split("|")[0])

        quality_videos.sort(reverse=True)
        if quality_videos == [] and platform not in audio_platforms:
            await message.reply_text("[download] No " + str(quality) + "p video, choosing closest one...")
            
            quality_dif_main = 10000

            for i in range(len(options)):
                if "x" in options[i] and "audio only" not in options[i]:
                    quality_selected = int(options[i].split("x")[1].split(" ")[0])
                    quality_dif = quality - quality_selected
                    if quality_dif < 0:
                        quality_dif = quality_dif * -1
                    if quality_dif < quality_dif_main:
                        quality_dif_main = quality_dif
                        quality_id = i

            quality_videos.append(options[quality_id].split("|")[1] + "|" +
                                  options[quality_id].split("|")[0])
        #####################

        if platform in partly:
            module = importlib.import_module(pl)
            quality_videos = module.video_fix(options, quality_videos)

        #####################

        if quality_videos != []:

            if platform not in partly:
                quality_videos = [quality_videos[0]]

            for items in quality_videos:

                dash_f = items.split("|")[1].split(" ")[0]
                part = ""

                if len(video_urls) > 1:
                    part = str(v)
                if platform == "f1tv" and v == 0:
                    part = ""

                output_name = output_folder + "/" + dot_title + season + episode + "-video" + part + ".mp4"
                video_down = [
                    "yt-dlp", "--external-downloader", "aria2c",
                    "--progress","--no-warnings", "-q", '-f', dash_f,
                    "--allow-unplayable-format", video_url, "-o", output_name
                ]

                #####################

                if platform == "puhu":
                    video_down.append("--keep-fragments")
                    video_down.append("--force-overwrites")            
                if platform in no_aria:
                    video_down[1] = "--concurrent-fragments"
                    video_down[2] = "30"
                if platform == "fubotv" and module.viewable_download == True and module.drm_status == 0:
                    await message.reply_text("[download] Viewable download, you can stream video on decrypted folder")
                    video_down[1] = "--concurrent-fragments"
                    video_down[2] = "30"
                if platform in multi_kids:
                    module.save_id(dash_f)

                #####################

                download_info = items.split()


                for t in range(len(download_info)):
                    if "x" in download_info[t]:
                        download_quality = download_info[t]
                        await info("download", "videod", download_quality,message)
                video_run = subprocess.run(video_down)

                #####################

                if platform == "puhu":
                    fix_output(output_name)

                #####################

        ## drm

        if drm_status == 1:

            await message.reply_text("[download] Downloading DRM file")

            erstream = ["exxen", "dsmartgo"]
            drmtoday = ["mubi", "claro"]
            rep = ["nbatv"]

            if platform in partly:
                dash_f = dash_f.split("-")[0]

            if platform in erstream:
                dd = requests.get(video_url).text
                rep = dd.split('media="')[1].split('"')[0]
                drm_url = video_url.split(".smil/")[0] + ".smil/" + rep
                drm_url = drm_url.replace("$RepresentationID$",dash_f)

                ## platform adjustments
                if platform == "exxen":
                    drm_url = drm_url.replace("-$Time$","").replace("=iv","=hv").replace("=ia","=iv")
                if platform == "dsmartgo":
                    drm_url = drm_url.replace("_$Time$","")
            
                output_name = "encrypted/" + dot_title + season + episode + "-drm" + part + ".key"
                drm_down = ["yt-dlp", drm_url, "-o", output_name]
            elif platform in drmtoday:
                parts = video_url.split("/")
                playlist_url = ""
                for items in parts:
                    if "ism" in items:
                        playlist_url = items.split(".ism")[0]
                base_url = "/".join(parts[:-1])
                drm_url = base_url + "/dash/" + playlist_url
                drm_url = drm_url + "-" + dash_f + ".dash"
                output_name = "encrypted/" + dot_title + season + episode + "-drm.key"
                drm_down = ["yt-dlp", drm_url, "-o", output_name]
            elif platform in rep:
                drm_url = video_url.split("/")
                output_name = "encrypted/" + dot_title + season + episode + "-drm.key"
                drm_url = "/".join(drm_url[:-1]) + "/" + dash_f + "/Time=init.mp4"
                drm_down = ["yt-dlp", drm_url, "-o", output_name]
            else:
                output_name = "--output-document=encrypted/" + dot_title + season + episode + "-drm.key"
                drm_down = [wget, video_url, output_name]
                
                if platform == "kablotv":
                    if proxy != "":
                        drm_down.append("-e")
                        drm_down.append("use_proxy=on")
                        drm_down.append("-e")
                        drm_down.append('http_proxy=' + http_proxy )
                    drm_down.append('--header=Referer:https://www.kablowebtv.com/WebTV')
                    drm_down.append('--header=User-Agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (Ktesttemp, like Gecko) Chrome/90.0.4430.85 Safari/537.36')
            drm_run = subprocess.run(drm_down, capture_output=True, text=True)

        ## subtitles from dash

        dash_sub = 0
        if dash_sub == 1:
            opt = [
                "yt-dlp", "--list-subs", "--allow-unplayable-formats", video_url
            ]
            opt = subprocess.run(opt, capture_output=True, text=True)
            sub_options = opt.stdout
            await message.reply_text(sub_options)

            if "no subtitles" not in sub_options:

                sub_options = sub_options.split("Formats\n")[1].split("\n")

                if platform == "tvplus":
                    tvplus.subs(video_url, sub_options)

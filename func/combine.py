import os, subprocess
import configparser
from iso639 import languages
from slugify import slugify
from func.basics import *
from func.messages import *
from func.upload import tg_upload
from func.platforms.blutv import altyz
import importlib
from config import LOG_CHANNEL
config = configparser.ConfigParser()
config.read('data/tokens/config.ini')

mkvmerge = config["binaries"]["mkvmerge"]
mha1_decoder = "data/apps/libmpegh"
import os
import time
import asyncio
import ffmpeg
from subprocess import check_output

config = configparser.ConfigParser()
config.read('data/tokens/config.ini')

mkvmerge = config["binaries"]["mkvmerge"]
mha1_decoder = "data/apps/libmpegh"
import time
import math
PRGRS = {}
import aiohttp


async def combine(content_information, content_list, content_type, subtitles,
                  season, episode, title, platform, images,message,userbot):

    slug_title = slugify(title)
    dot_title = slug_title.replace("-", ".")

    if content_type == "multiple":
        dot_title = dot_title + "."

    content = dot_title + season + episode + "-"
    mkv_files = ""
    global_options = ""

    pl = "func.platforms." + platform
    module = importlib.import_module(pl)
    if platform == "mubi":
        module.adapt(content_type,content_information,season,episode)
    else:
        module.adapt(season,episode)
    chapter_status = module.chapter_status
    if platform == "mubi":
        custom_title = ""
    else:
        custom_title = module.custom_title
    print(custom_title)
    descem = ""
    descemler = ["disneyplus", "gain", "blutv", "exxen"]
    if platform in descemler:
        descem = module.descem
    print(descem) 
    made_year = module.made_year    
    
    partly_platforms = ["vix"]
    maybe_partly = ["exxen"]
    if platform in maybe_partly and module.is_partly == True:
        partly_platforms.append(platform)
    if platform in partly_platforms:
        content_list = module.combine_parts(content_list,content)

    ## global options

    audio_platforms = ["trtaudio"]

    if platform == "tidal" and module.is_video == False:
        audio_platforms.append("tidal")

    if platform in audio_platforms:
        mui_type = content_list[0].split("-")[-1].split(".")[0]
        codec_type = "audio"
        media_end = "-" + mui_type + ".m4a"
    else:
        mui_type = "video"
        codec_type = "video"
        media_end = "-video.mp4"
    
    media_name = "decrypted/" + dot_title + season + episode + media_end
    codec_quality = "720"
    codec_name = "h264"
    metadata = " --global-tags data/diagnosis/tags.txt"
    if chapter_status == 1:
        metadata = metadata + " --chapters data/diagnosis/chapters.txt"

    ## global options
    global_options = " "
    no_title_platforms = ["tidal"]
    if platform not in no_title_platforms:
        global_options = ' --title "' + title.strip()

    events_platforms = ["paramountplus","dazn","fubotv","beinturkey","espnplus"]
    missing_dates = ["beinturkey"]
    is_event = False
    if platform in events_platforms:
        is_event = module.is_event
        if is_event == True:
            event_name = module.event_name
            
            if platform in missing_dates:
                event_date = mui["tags"]["creation_time"].split("T")[0]
            else:
                event_date = module.event_date
    
    if is_event == True:
        displays = ["",event_name,event_date]
    elif content_type == "single":
        displays = [""]
        if made_year != "":
            displays.append(made_year)
    elif content_type == "multiple":
        displays = ["","Season " + season,"Episode " + episode]
        if custom_title != "":
            displays.append(custom_title)
    if platform not in no_title_platforms:
        global_options = global_options + ", ".join(displays) + '"'

    ## platform adjustments

    no_season_platforms = ["trt_audio","kanald","masterclass","udacity","edx"]
    if platform in no_season_platforms:
        global_options = global_options.replace(", Season " + season, "")

    ## combine settings
    
    adapt_multiples = ["f1tv"]
    total_audio = 0

    for items in content_list:
        if content in items and "audio.m4a" in items:
            total_audio = total_audio + 1

    for items in content_list:
        if content in items:
            if "video" in items:

                video_name = ""
                if platform in adapt_multiples:
                    pl = "func.platforms." + platform
                    module = importlib.import_module(pl)
                    video_name = module.adapt_output(items)

                if video_name != "":
                    video_name = '--track-name 0:"' + video_name + '"'


                mkv_files = mkv_files + " --language 0:und " + video_name + " " + items
            
            if "audio" in items:
                audio_code = items.split("audio.m4a")[0].split("-")[1]

                if total_audio == 1 or "org" in audio_code:
                    dt = "yes"
                elif "0" in audio_code:
                    dt = "yes"
                    audio_code = audio_code.replace("0","")
                else:
                    dt = "no"

                try:
                    country_name = languages.get(part3=audio_code).name
                except KeyError:
                    country_name = "und"
                    audio_code = "und"

                ## platform adjustments

                ## default track
                if dt == "no" and platform == "f1tv" and audio_code == "eng":
                    dt = "yes"
                if dt == "no" and platform == "f1tv" and "audio.m4a" in items:
                    dt = "yes"
                if dt == "no" and platform == "exxen" and audio_code == "tur":
                    dt = "yes"

                ## language name
                if audio_code == "ter":
                    country_name = "Turkish with Therapist"
                    audio_code = "tur"
                if platform == "f1tv" and (audio_code == "und" or audio_code == "zxx"):
                    audio_code = "zxx"
                    country_name = "No commentary"
                if audio_code == "org":
                    audio_code = "und"
                    country_name = "Original Language"
                if audio_code == "und" and platform == "channel4":
                    audio_code = "eng"
                    country_name = "English"
                if audio_code == "und" and platform == "euroleaguetv":
                    audio_code = "eng"
                    country_name = "English"

                if platform in adapt_multiples and "audio.m4a" not in items:
                    pl = "func.platforms." + platform
                    module = importlib.import_module(pl)
                    audio_code = "und"
                    dt = "no"
                    country_name = module.adapt_output(items)

                country_name = '"' + country_name + '"'

                mkv_files = mkv_files + " --language 0:" + audio_code + " --default-track 0:" + dt + " --track-name 0:" + country_name + " " + items

    ## subtitle codes: 0 = forced, 1 = accessibility

    for i in range(len(subtitles)):
        await message.reply_document(subtitles[i])
        subtitle = subtitles[i].replace("decrypted/", "")
        if content in subtitle:
            subtitle_code = subtitle.split("subtitle")[0].split("-")[1]
            
            sub_force = "no"
            if "0" in subtitle_code:
                sub_force = "yes" 
                subtitle_code = subtitle_code.replace("0","")

            sub_accessibility = "no"
            if "1" in subtitle_code:
                sub_accessibility = "yes"
                subtitle_code = subtitle_code.replace("1","")

            try:
                country_name = languages.get(part3=subtitle_code).name
            except KeyError:
                country_name = "und"
                subtitle_code = "und"

            ## platform adjustments

            ## language name
            if platform == "blu" and subtitle_code == "ter":
                country_name = "Turkish with Therapist"
                subtitle_code = "tur"


            adds = ""

            if sub_force == "yes":
                adds = adds + " --forced-display-flag 0:yes "
                country_name = country_name + " - Forced"

            if sub_accessibility == "yes":
                adds = adds + " --hearing-impaired-flag 0:yes "
                country_name = country_name + " - SDH"

            country_name = '"' + country_name + '"'

            mkv_files = mkv_files + " --language 0:" + subtitle_code + " --default-track 0:no " + adds + " --track-name 0:" + country_name + " " + subtitles[
                i]


    for i in range(len(images)):
        image = images[i]
        if content in image:
            mkv_files = mkv_files + " --attach-file " + image + " --attachment-mime-type image/jpeg"



    if is_event == True:
        content_final_name = dot_title + "." + event_date.replace("-",".") + "." + codec_quality + "p.web." + codec_name
        content_final_name = content_final_name.upper() 
        content_final_name += "-TR.mkv"
    elif content_type == "single":
        content_final_name = dot_title + "." + codec_quality + "p.web." + codec_name
        content_final_name = content_final_name.upper() 
        content_final_name += "-TR.mkv"
    elif content_type == "multiple":
        content_final_name = dot_title + "s" + season + "e" + episode + "." + codec_quality + "p.web." + codec_name
        content_final_name = content_final_name.upper() 
        content_final_name += "-TR.mkv"
        if season != "None" and episode != "None" and int(episode) < 10:
            content_final_name = content_final_name.replace(
                "E" + episode, "E0" + episode)
            global_options = global_options.replace("E" + episode,
                                                    "E0" + episode)
        if season != "None" and episode != "None" and int(season) < 10:
            content_final_name = content_final_name.replace(
                "S" + season, "S0" + season)
            global_options = global_options.replace("S" + season,
                                                    "S0" + season)



    if platform in audio_platforms:
        content_final_name = content_final_name.replace(
            codec_quality + "p.web.", codec_quality + "kbps.web.")

        if codec_quality == "":
            content_final_name = content_final_name.replace(
            codec_quality + "kbps.web.","web.")

        content_final_name = content_final_name.replace(".mkv", ".mka")
        content_final_name = content_final_name.replace("s0" + season, "")
    if platform in no_season_platforms:
        content_final_name = content_final_name.replace("S0" + season, "")

    await info("combine","combine",content_final_name,message)

    combine = "mkvmerge" + " -q --disable-track-statistics-tags " + global_options + metadata + " -o " + content_final_name + mkv_files
    os.system(combine)
    start_time = time.time()
    isim = content_final_name.replace(".mkv", ".mp4").upper()
    video = content_final_name
    try:
        os.rename(video, isim)
    except Exception as e:
        print(e)
    video = isim
    if platform in descemler:
        try:
            if content_type == "single":
                desc = ""
            else:
                desc = descem
        except Exception as e:
            print(e)
    else:
        desc = descem
    if platform == "blutv" and audio_code != "tur":
        sub = subtitles[0]
        s = await message.reply_text("Alt yazı gömülüyor..")
        video = altyz(video,sub)
        await s.delete()
    elif platform == "mubi" and audio_code != "tur":
        sub = subtitles[0]
        s = await message.reply_text("Alt yazı gömülüyor..")
        video = altyz(video,sub)
        await s.delete()
    elif platform == "disneyplus" and audio_code != "tur":
        sub = subtitles[0]
        s = await message.reply_text("Alt yazı gömülüyor..")
        video = altyz(video,sub)
        await s.delete()
        
    if platform == "blutv":
        p = "BLUTV"
    elif platform == "exxen":
        p = "EXXEN"
    elif platform == "disneyplus":
        p = "DSNP"
    elif platform == "mubi":
        p = "MUBI"
    elif platform == "tabii":
        p = "TABII"
    elif platform == "gain":
        p = "GAIN"
    elif platform == "puhu":
        p = "PUHU"
    else:
        p = "HPLATFORM"

    a = video.split("0P.")
    newname = f"{a[0]}0P.{p}.{a[1]}"
    try:
        os.rename(video, newname)
        video = newname
    except Exception as e:
        print(e)
    await tg_upload(message,video,desc)




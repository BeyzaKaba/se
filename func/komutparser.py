import glob, os, sys
from slugify import slugify
from func import basics, query, download, decrypt, combine, alls, messages
import argparse
import importlib
from pyrogram import Client, filters
from pyromod import listen
from config import userbot, LOG_CHANNEL, OWNER_ID
import logging
import requests
from PIL import Image
from func.platforms.tabii import download_tabi

sira = []

from pyrogram.types import Message

async def on_task_complete(bot, message: Message):
    if len(sira) > 0:
        await siram(bot, sira[0])

@Client.on_message(filters.command('log') & filters.private & filters.user(OWNER_ID))
async def log_handler(bot, message):
    with open('log.txt', 'rb') as f:
        try:
            await bot.send_document(document=f,
                                  file_name=f.name, reply_to_message_id=message.id,
                                  chat_id=message.chat.id, caption=f.name)
        except Exception as e:
            await message.reply_text(str(e))

@Client.on_message(filters.command('dl') & filters.private)
async def dl(bot, message):
    try:
        sirasi = len(sira)
        await message.reply_text(f"İşlem Sıraya Eklendi...\n\nSıranız: {sirasi}")
        sira.append(message)
        if len(sira) == 1:
            await siram(bot, message)
    except Exception as e:
        await message.reply_text(e)
        del sira[0]
        await on_task_complete(bot, message)


async def siram(bot, message):
    l = await message.reply_text("işlem başladı...")

    parser = argparse.ArgumentParser()

    parser.add_argument('-t',"--title",
                        required=True,
                        dest='title',
                        help="query search, part of title is ok"
                        )

    parser.add_argument('-q',"--quality",
                        default=2160,
                        type=int,
                        dest='quality',
                        help="default 2160p"
                        )

    parser.add_argument('-p',"--platform",
                        default="",
                        dest='platform',
                        help="select platform, if not will search on all platforms"
                        )

    parser.add_argument('-s',"--season",
                        default="",
                        dest='season',
                        help='selected season, only one season allowed'
                        )

    parser.add_argument('-e',"--episodes",
                        default="",
                        dest='episodes',
                        help='episodes with comma 1,2,3,4 or minus 1-4'
                        )

    parser.add_argument('-l',"--last-episodes",
                        default=0,
                        type=int,
                        dest='last_episodes',
                        help='last x episodes of season'
                        )

    parser.add_argument('-c',"--clean",
                        default=1,
                        type=int,
                        dest='remove_files',
                        help='clean files after combine, default 1'
                        )
    
    parser.add_argument('-d',"--dil",
                        default="yok",
                        type=str,
                        dest="dil")
    
    komut = message.text.split(" ")
    komut.remove("/dl")
    args = parser.parse_args(komut)

    title = args.title
    platform = args.platform
    season = args.season
    dil = args.dil
    last_episodes = args.last_episodes
    quality = args.quality

    episodes = args.episodes
    if (season != "" and episodes == "") or last_episodes != 0:
        all_episodes = 1
    else:
        all_episodes = 0

    episodes = basics.split_episodes(args.episodes)
    quality = args.quality
    remove_files = args.remove_files
    if platform == "tabii":
        episodes = args.episodes
        await download_tabi(title, quality, dil, l, message,season,episodes,last_episodes,userbot)
    else:
        await query.query(title, season, platform, message,platform)
        title = query.title_function
        platform = query.platform
        content_information = query.ci

        content_type = query.ct
        content_id = query.cid
        if platform == "mubi":
            widevine_server = "https://lic.drmtoday.com/license-proxy-widevine/cenc/"
        else:
            widevine_server = query.widevine_server

        slug_title = slugify(title)
        dot_title = slug_title.replace("-", ".")


        if all_episodes == 1 and content_type == "multiple":
            episodes = alls.alls(platform, last_episodes, season, content_information)


        if content_type == "single":
            season = ""
            episodes = [""]
        elif content_type == "multiple":
            dot_title = dot_title + "."

        music_streaming = ["tidal"]
        if platform in music_streaming and content_type == "multiple":
            season = ""
            episodes = list(range(0,len(content_information["content"])))

        ori_content_type = content_type
        print(content_information)
        if platform == "exxen":
            c_information = content_information
            
            desc = c_information["info"]["Description"]
            title = c_information["info"]["Name"]
            print(desc)
          
            images = content_information["info"]["Images"]
            print(images)
            image = "yok"
            ty = images[1]["ImageUrl"]
            image = f"https://image.exxen.com{ty}"
            te = f"{title}\n\n||{desc}||"
            print(image)
            if image != "yok":
                try:
                    imgg = f"{title}.photo.png"
                    response = requests.get(image)
                    with open(imgg, "wb") as f:
                        f.write(response.content)
                    ali = await message.reply_photo(
                        photo=imgg,
                        caption=te
                    )
                    await ali.copy(LOG_CHANNEL)
                    os.remove(imgg)
                except Exception as e:
                    print(e)
        if platform == "blutv":
            if content_type == "multiple":
                title = content_information["info"]["title"]
                desc = content_information["info"]["description"]
                lon = "https://blutv-images.mncdn.com/q/t/i/bluv2/100/1408x752/"
                image = lon + str(content_information["info"]["posters"][0]["id"])
                try:
                    imgg = f"{title}.photo.jpg"
                    response = requests.get(image)
                    with open(imgg, "wb") as f:
                        f.write(response.content)
                    ali = await message.reply_photo(
                        photo=imgg,
                        caption=f"{title}\n\n||{desc}||"
                    )
                    await ali.copy(LOG_CHANNEL)
                    os.remove(imgg)
                except Exception as e:
                    print(e)
        if platform == "disneyplus":
            if content_type == "single":
                desc = content_information["info"]["text"]["description"]["medium"]["program"]["default"]["content"]
            else:
               desc = content_information["info"]["text"]["description"]["medium"]["series"]["default"]["content"]

            try:
                if content_type == "single":
                    image = content_information["info"]["image"]["tile"]["1.78"]["program"]["default"]["url"]
                else:
                    image = content_information["info"]["image"]["tile"]["1.78"]["series"]["default"]["url"]
            except Exception as e:
                print(e)
    
            try:
                imgg = f"{title}.photo.png"
                response = requests.get(image)
                with open(imgg, "wb") as f:
                    f.write(response.content)
                im = Image.open(imgg)
                bg = Image.new("RGB", im.size, (255,255,255))
                bg.paste(im,im)
                bg.save(f"{title}.photo.2.jpg")
                os.remove(imgg)
                imgg = f"{title}.photo.2.jpg"
                ali = await message.reply_photo(
                    photo=imgg,
                    caption=f"{title}\n\n||{desc}||"
                )
                await ali.copy(LOG_CHANNEL)
                os.remove(imgg)
            except Exception as e:
                print(e)

        for episode in episodes:
    
            await messages.start(title,str(season),str(episode),platform,message,l)
    
            pl = "func.platforms." + platform
            module = importlib.import_module(pl)
            if platform == "mubi":
                video_url = await module.download(season, episode,content_type, content_information, title, message, dil)
            else:
                video_url = await module.download(season, episode,message, dil)
            drm_status = module.drm_status

            if platform in music_streaming and content_type == "multiple":
                title = module.title
                slug_title = slugify(title)
                dot_title = slug_title.replace("-", ".")
                episode = ""
                content_type = "single"

            await download.download(video_url, quality, season, episode, title, platform,
                          content_type, drm_status,message,dil)


            dwn_list = []
            if drm_status == 1:
                dwn_list = glob.glob("encrypted/" + dot_title + season + episode +  "*video*")
                dwn_list = dwn_list + glob.glob(("encrypted/" + dot_title + season + episode + "*audio*"))
                dwn_list.sort()
        
                for i in range(len(dwn_list)):
                    await decrypt.decrypt(dwn_list, content_type, i, title, platform,
                                widevine_server, content_information,season,episode,message)

            cmb_list = glob.glob("decrypted/" + dot_title + season + episode + "*video*")
            cmb_list = cmb_list + glob.glob(("decrypted/" + dot_title + season + episode + "*audio*"))
            cmb_list.sort()
            sub_list = glob.glob("decrypted/" + dot_title + season + episode + "*subtitle*")
            sub_list.sort()
            images = glob.glob("decrypted/" + dot_title + season + episode + "*image*")

            await combine.combine(content_information, cmb_list, content_type, sub_list,
                        season, episode, title, platform, images,message,userbot)

            if remove_files == 1:
                await messages.end(message)
                cmb_list = glob.glob("decrypted/" + dot_title + season + episode + "*video*")
                cmb_list = cmb_list + glob.glob(("decrypted/" + dot_title + season + episode + "*audio*"))
                drm_list = glob.glob(("encrypted/" + dot_title + season + episode + "*drm*"))
                dlt_list = dwn_list + cmb_list + sub_list + drm_list + images
                for items in dlt_list:
                    try:
                        os.remove(items)
                    except Exception as e:
                        print(e)

            content_type = ori_content_type
    del sira[0]
    await on_task_complete(bot, message)


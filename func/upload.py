 # Coded by @mmagneto

import os
import time
import asyncio
import ffmpeg
from subprocess import check_output
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from config import LOG_CHANNEL, userbot
import math

def get_codec(filepath, channel="v:0"):
    output = check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            channel,
            "-show_entries",
            "stream=codec_name,codec_tag_string",
            "-of",
            "default=nokey=1:noprint_wrappers=1",
            filepath,
        ]
    )
    return output.decode("utf-8").split()

async def encode(filepath):
    path, extension = os.path.splitext(filepath)
    file_name = os.path.basename(path)
    encode_dir = file_name
    output_filepath = encode_dir + 'A.mp4'
    assert (output_filepath != filepath)
    if os.path.isfile(output_filepath):
        print('"{}" Atlanıyor: dosya zaten var'.format(output_filepath))
    print(filepath)

    # Get the audio and subs channel codec
    audio_codec = get_codec(filepath, channel='a:0')

    if not audio_codec:
        audio_opts = '-c:v copy'
    elif audio_codec[0] in 'aac':
        audio_opts = '-c:v copy'
    else:
        audio_opts = '-c:a aac -c:v copy'

    command = ['ffmpeg', '-y', '-i', filepath]
    command.extend(audio_opts.split())
    proc = await asyncio.create_subprocess_exec(
        *command, output_filepath,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await proc.communicate()
    return output_filepath

async def progress_bar(current, total, text, message, start):

    now = time.time()
    diff = now-start
    if round(diff % 10) == 0 or current == total:
        percentage = current*100/total
        speed = current/diff
        elapsed_time = round(diff)*1000
        eta = round((total-current)/speed)*1000
        ett = eta + elapsed_time

        elapsed_time = TimeFormatter(elapsed_time)
        ett = TimeFormatter(ett)

        progress = "[{0}{1}] \n**İlerleme**: {2}%\n".format(
            ''.join(["●" for i in range(math.floor(percentage / 10))]),
            ''.join(["○" for i in range(10 - math.floor(percentage / 10))]),
            round(percentage, 2))

        tmp = progress + "**Indirilen**: {0}/{1}\n**Hız**: `{2}`/s\n**Tahmini Süre**: `{3}`\n".format(
            humanbytes(current),
            humanbytes(total),
            humanbytes(speed),
            # elapsed_time if elapsed_time != '' else "0 s",
            ett if ett != '' else "0 s"
        )

        try :
            await message.edit(
                text = '{}'.format(tmp)
            )
        except:
            pass

def humanbytes(size):
    # https://stackoverflow.com/a/49361727/4723940
    # 2**10 = 1024
    if not size:
        return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'Ki', 2: 'Mi', 3: 'Gi', 4: 'Ti'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'

def format_filename(filename):
    # Dosya adı ve uzantısını ayır
    name, ext = os.path.splitext(filename)
    
    # Dosya adını böl ve dönüştür
    formatted_name = '.'.join(word.capitalize() for word in name.split('.'))
    
    # Uzantıyı geri ekle
    return formatted_name + ext
 
def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
        ((str(hours) + "h, ") if hours else "") + \
        ((str(minutes) + "m, ") if minutes else "") + \
        ((str(seconds) + "s, ") if seconds else "") + \
        ((str(milliseconds) + "ms, ") if milliseconds else "")
    return tmp[:-2]

def get_width_height(filepath):
    metadata = extractMetadata(createParser(filepath))
    if metadata.has("width") and metadata.has("height"):
      return metadata.get("width"), metadata.get("height")
    else:
      return 1280, 720
    
async def get_thumbnail(video_file, output_directory, ttl):
    # https://stackoverflow.com/a/13891070/4723940
    out_put_file_name = output_directory + \
                        "/" + str(time.time()) + ".jpg"
    file_genertor_command = [
        "ffmpeg",
        "-ss",
        str(ttl),
        "-i",
        video_file,
        "-vframes",
        "1",
        out_put_file_name
    ]
    # width = "90"
    process = await asyncio.create_subprocess_exec(
        *file_genertor_command,
        # stdout must a pipe to be accessible as process.stdout
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    # Wait for the subprocess to finish
    stdout, stderr = await process.communicate()
    if os.path.lexists(out_put_file_name):
        return out_put_file_name
    else:
        return None

def get_duration(filepath):
    metadata = extractMetadata(createParser(filepath))
    if metadata.has("duration"):
      return metadata.get('duration').seconds
    else:
      return 0   

async def tg_upload(message,video,desc):
    caption = f"{video}\n\n||{desc}||"
    try:
        d = await message.reply_text("MP4 Yapılıyor..")
        nv = await encode(video)
        await d.delete()
        video = nv
    except Exception as e:
        print(e)
    start_time = time.time()
    duration = get_duration(video)
    thumb_path = f"thumbs/{message.chat.id}/{message.chat.id}.jpg"
    if os.path.exists(thumb_path):
        thumb = thumb_path
    else:
        thumb = await get_thumbnail(video, "decrypted", duration / 4)
    msg = await message.reply_text("Yükleniyor..")
    file_size = os.stat(video).st_size
    if file_size > 2093796556 and file_size < 4294967296:
        await userbot.send_video(
            chat_id=LOG_CHANNEL,
            video=video,
            caption=caption,
            thumb=thumb, 
            progress=progress_bar,
            progress_args=(
                'Dosyan Yükleniyor!',
                msg,
                start_time),
            duration=duration)
        await msg.edit("Yüklendi...")
    elif file_size < 2093796556:
        copy = await message.reply_video(
            video=video,
            caption=caption,
            thumb=thumb,
            progress = progress_bar, 
            progress_args = (
                'Dosyan Yükleniyor!',
                msg,
                start_time
                ),
            duration=duration)
        try:
            await copy.copy(LOG_CHANNEL)
        except Exception as e:
            await message.reply_text(e)
        await msg.edit("Yüklendi...")
    os.remove(video)

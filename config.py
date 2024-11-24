import os
from pyrogram import Client

BOT_TOKEN = os.environ.get("BOT_TOKEN", "6818172335:AAHjP5v26nmSZnMWF583p5cSOhRIjA5cjWA")
API_HASH = os.environ.get("API_HASH", "c23db4aa92da73ff603666812268597a")
API_ID = os.environ.get("API_ID", 2374174)
MUBI_TOKEN = "643dfc8eee88d0147244cb05bd9f2f02bb834b"
MUBI_BEARER = "eyJ1c2VySWQiOjEyMjg4ODQzLCJzZXNzaW9uSWQiOiI2NDNkZmM4ZWVlODhkMDE0NzI0NGNiMDViZDlmMmYwMmJiODM0YiIsIm1lcmNoYW50IjoibXViaSJ9"
OWNER_ID = os.environ.get("OWNER_ID", "ahmet118")
STREAMTAPE_API_PASS="lW3WyaGz9rh7ko7"
LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "-1001580827602"))
POSTA = "gncrali2006@gmail.com"
PASS = "Gncrali2006"
CAP = "true"
STREAMTAPE_API_USERNAME="041db6b5ed20e4d5816b"
STRING_SESSION = os.environ.get('STRING_SESSION', 'BACeFRNDSmQmRgHaYJqpzyBbI1XY9CxGqbFZe_BUeHY2W9hh0ZC2OaSjs7fSWXz1KNyMiECBDgHyDvMhx9YS_Cjd6z3wXaXq1OIVYUZvGH46iAAI39rv00cLNLElpiR0R7Xm-lyFAbvXrkLcptQTmZLXzOBBF2mg6mclarQzIFovwiW0Ft3veqs7KQZmtRsds52DR-xBLP2cqXRY7NA5tlnQgWjCc626HLpjMeTMIue5nUiZs41Wxq8IFWcPTanA4by4p_yuJ1EzDI4_wM6ht7WzI-74wy5asEwfbbLSv6oR_OGoLuevQiqp4rS7EvalEdvZU0fz4Xgs5aM8ppLdHCqHX19oqAA')
if len(STRING_SESSION) != 0:
    try:
        userbot = Client(
            name='Userbot',
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=STRING_SESSION,
        ) 
        userbot.start()
        me = userbot.get_me()
        userbot.send_message(OWNER_ID, f"Userbot Bașlatıldı..\n\n**Premium Durumu**: {me.is_premium}\n**Ad**: {me.first_name}\n**id**: {me.id}")
        print("Userbot Başlatıldı..")
    except Exception as e:
        print(e)

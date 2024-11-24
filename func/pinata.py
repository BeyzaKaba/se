import requests

from pinata import Pinata
import json
from pyrogram import Client, filters

ap_key = "605f194154f72f4de5c3"
secret_key = "e1c61d210abceefb4cd02b9fde60625b8c0a4e8dc1048dfb95fe791da696793d"
access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySW5mb3JtYXRpb24iOnsiaWQiOiJhMTVhYjY2NC1kNDk3LTRjNmYtYmYxYi0zMTE1ODQ1ZjU3MzAiLCJlbWFpbCI6ImduY3JhbGkyMDA2QGdtYWlsLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJwaW5fcG9saWN5Ijp7InJlZ2lvbnMiOlt7ImlkIjoiRlJBMSIsImRlc2lyZWRSZXBsaWNhdGlvbkNvdW50IjoxfSx7ImlkIjoiTllDMSIsImRlc2lyZWRSZXBsaWNhdGlvbkNvdW50IjoxfV0sInZlcnNpb24iOjF9LCJtZmFfZW5hYmxlZCI6ZmFsc2UsInN0YXR1cyI6IkFDVElWRSJ9LCJhdXRoZW50aWNhdGlvblR5cGUiOiJzY29wZWRLZXkiLCJzY29wZWRLZXlLZXkiOiI2MDVmMTk0MTU0ZjcyZjRkZTVjMyIsInNjb3BlZEtleVNlY3JldCI6ImUxYzYxZDIxMGFiY2VlZmI0Y2QwMmI5ZmRlNjA2MjViOGMwYTRlOGRjMTA0OGRmYjk1ZmU3OTFkYTY5Njc5M2QiLCJpYXQiOjE2ODQ4Njg2NDZ9.q0qk577x9AI6ePTd-uMXHd0RcHJrTas2TBLYlzxGFcg"

@Client.on_message(filters.command('pinatasil')) 
async def pinatasil(bot, message):
    pinata = Pinata(ap_key, secret_key, access_token)

    response = pinata.get_pins()
    cidlist = response["data"]["results"]
    print(cidlist)
    say = 0
    if cidlist != []:
        for cid in cidlist:
            say += 1
            print(cid)
            sil = cid["pin"]["cid"]
            print(sil)
            pinata = Pinata(ap_key, secret_key, access_token)
            response = pinata.unpin_file(sil)
            print(response)
        await message.reply_text(f"{say} tane dosya silindi..")
    else:
        await message.reply_text("Hiç Pinata Dosyan yok..")
        
    
    

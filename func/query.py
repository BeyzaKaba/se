import json, sys
import configparser
import importlib
from func.basics import ip_info
from tabulate import tabulate

config = configparser.ConfigParser()
config.read('data/tokens/config.ini')

ap = []
all_p = []

turkey_config = dict(config.items('turkey'))
usa_config = dict(config.items('usa'))
uk_config = dict(config.items('uk'))
australia_config = dict(config.items('australia'))
greece_config = dict(config.items('greece'))
latom_config = dict(config.items('latom'))
int_config = dict(config.items('international'))

regions = [turkey_config,usa_config,latom_config,australia_config,int_config]

for r in range(len(regions)):
    for items in regions[r]:
        if "search" in items:
            all_p.append(items.split("_search")[0])
        if "search" in items and regions[r][items] == "1":
            ap.append(items.split("_search")[0])

for items in config:
    if "search" in config[items]:
        all_p.append(items)
        if config[items]["search"] == "1":
            ap.append(items)


async def query(title,season,ps,message,pltform):

    global widevine_server
    global platform
    global ci
    global ct
    global cid
    global title_function
    global ap
    
    ip_data = ip_info()
    
    if ps != "" and ps in all_p:
        ap = [ps]
    elif ps != "":
        ap = []
        for p in all_p:
            if ps in p:
                ap.append(p)
    
    if ap == []:
        await message.reply_text("[error] No platform selected")

    while True:
        
        await message.reply_text("[search] " + title + " on " + ", ".join(ap))
        
        at = []
        sr = {}
        di = {}
        ci = {}

        for i in ap:
            pl = "func.platforms." + i
            module = importlib.import_module(pl)
            await module.query(title,sr,at,ip_data,message)

        ## save diagnosis
        with open("data/diagnosis/available_titles.json", 'w') as outfile:
            json.dump(at, outfile, indent=4)
        with open("data/diagnosis/search_result.json", 'w') as outfile:
            json.dump(sr, outfile, indent=4)

        ## select content

        if len(at) == 0:
            await message.reply_text("No content found!")
            title = await message.chat.ask("Enter new title: ")
        elif len(at) == 1:
            if pltform == "mubi":
                platform = pltform
            else:
                platform = at[0]["platform"]
            print(at)
            if pltform == "mubi":
                cid = at[0][0]["id"]
            else:
                cid = at[0]["id"]
            break
        elif len(at) > 1:
            print("Search Results\n-----------")
            texx = ""
            if pltform == "mubi":
                at.sort()
                print(at)
                texx = ""
                m = ""
                for i in range(len(at)):
                    if i + 1 < 10:
                        m += "" + str(i + 1) + "- {at[i]['title']}/n"
                texx += m
                platform = pltform
                await message.reply_text(f"{texx}")
                srr = await message.chat.ask("Seç:")
                st = int(srr.text) - 1
                cid = at[st]["id"]
            else:
                at.sort(key=lambda t: t["title"])
                pt = []
                for i in range(len(at)):
                    tt = {}
                    tt["id"] = i + 1
                    for t in at[i]:
                        if t != "id":
                            tt[t] = at[i][t]
                    pt.append(tt)
                    pt[i]["meta"] = " ".join(pt[i]["meta"]).upper()
                print(pt)
                s = 0
                tx = ""
                for i in pt:
                    s += 1
                    tx += f"{s}- {i['title']} {i['meta']}\n"
                sa = await message.reply_text(f"{tx}")
                srr = await message.chat.ask("Seç:")
                st = int(srr.text) - 1
                await sa.delete()
                platform = at[st]["platform"]
                cid = at[st]["id"]
                print(cid)
            break

    pl = "func.platforms." + platform
    module = importlib.import_module(pl)
    if platform == "mubi":
        season = 1
        res = {}
        res["mubi"] = at[0]
        print(cid)
        module.select(res,ci,cid,season)
    else:
        module.select(ci,cid,season)
    title = module.title
    ct = module.ct
    if platform != "mubi":
        widevine_server = module.wv_server

    with open("data/diagnosis/content_information.json", 'w') as outfile:
        json.dump(ci, outfile, indent=4)

    title_function = title


import json, sys, requests
from slugify import slugify
import ipinfo
import configparser
from func.basics import *

config = configparser.ConfigParser()
config.read('data/tokens/config.ini')

def proxy(mc,p):

    global proxies

    http_proxy = config["proxy"]["http"]
    https_proxy = config["proxy"]["https"]
    nordvpn_user = config["general"]["nordvpn_user"]
    nordvpn_pass = config["general"]["nordvpn_pass"]

    no_nordvpn = ["beinturkey"]

    local_vpn = ["dazn"]
    if p in no_nordvpn and https_proxy != "":
        print("[" + p + "] Geo-Restriction, using given proxy...")
        proxies = {'http': http_proxy,'https': https_proxy}
        return proxies
    elif p in local_vpn and mc.lower() == "ca":
        print("[" + p + "] Geo-Restriction, using given proxy...")
        proxies = {'http': http_proxy,'https': https_proxy}
        return proxies                
    elif nordvpn_user == "":
        return {}
    
    print("[" + p + "] Geo-Restriction, using nordvpn...")

    country_list = requests.get("https://api.nordvpn.com/v1/servers/countries").json()
    
    for i in range(len(country_list)):
        if country_list[i]["code"].lower() == mc.lower():
            country_id = str(country_list[i]["id"])
            break

    params = "filters[country_id]=" + country_id + "&filters[servers_technologies][identifier]=proxy_ssl&limit=3"
    proxies = requests.get("https://api.nordvpn.com/v1/servers/recommendations?" + params).json()
    auth = nordvpn_user +  ":" + nordvpn_pass
    proxy_list = []
    
    for i in range(len(proxies)):
        if proxies[i]["status"] == "online": 
            cred = auth + "@" + proxies[i]["hostname"]  + ":89"
            proxy = {"https":"https://" + cred,"http":"https://" + cred}
            proxy_list.append(proxy)
    proxy_last = ""
    
    if p == "claro":
        test_api = "https://mfwkweb-api.clarovideo.net/services/search/predictive"
        error_text = "Access Denied"
    else:
        test_api = "https://api.ipify.org"
        error_text = "always_pass"

    for i in range(len(proxy_list)):
        try:
            connect = requests.get(test_api,proxies=proxy_list[i])
        except:
            print("[warning] Cannot connect nordpvn server, trying again...")
            continue
        else:
            if error_text not in connect.text:
                proxy_last = proxy_list[i]
                break
            else:
                continue

    if proxy_last == "":
        proxy_last = {}

    return proxy_last

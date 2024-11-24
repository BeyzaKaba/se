import sys

async def warning(p,s,ex,message):

    m = ["[warning]","[" + p + "]"]

    ## search module
    
    if s == "minquery":
        m.append("Minimum " + ex +" characters needed,")  
        m.append("skipping search")
    elif s == "ipblock":
        m.append("IP blocked,")
        m.append("skipping search")
    elif s == "noauth_proxy":
        m.append("Not available in")
        m.append(ex + ",")
        m.append("using proxy")
    elif s == "noconnection":
        m.append("Connection error,")
        m.append("skipping search")
    elif s == "noproxy":
        m.append("Proxy is not working,")
        m.append("skipping search")
    elif s == "intonly":
        m.append("No Turkish IP,")
        m.append("only getting international right content")




    ## download module

    elif s == "findres":
        m.append(str(ex) + "p is not available,")
        m.append("choosing closest resolution")
    elif s == "raredash":
        m.append("No dash on trt normally,")
        m.append("report developer")
    elif s == "nolang":
        if ex == "part1" or ex == "part3":
            m.append("No language, using undetermined")
        else:
            m.append("No language on part2, checking part3")



    ## decrypt module
    
    elif s == "buggykey":
        m.append("Buggy keys,")
        m.append("converting list")
    elif s == "oldmethod":
        m.append("Stop using bad method MP4Decrpyt")

    await message.reply_textt(" ".join(m))
    
async def error(p,s,ex,message):

    m = ["[error]","[" + p + "]"]


    ## search module

    if s == "noseason":
        m.append("No Season")  
        m.append(ex) 
    elif s == "noepisode":
        m.append("No Episode")  
    elif s == "nourl":
        m.append("No Video URL")
        t = ex[2]
        if t == "multiple":
            e = "Episode " + ex[0] 
            s = "Season " + ex[1] + ","
            m.append("for")
            m.append(s)
            m.append(e)
    elif s == "noauth":
        m.append("No Auth")       

    ## download module

    elif s == "derror":
        m.append("Download failed")
        m.append(", check debug info\n")
        m.append(ex)



    elif s == "nokey":
        m.append("No decryption key found for")
        m.append(ex)  

    elif s == "nokey":
        debug = ex[0]
        method = ex[1]
        m.append("Decryption failed")
        if ex[1] == "shaka":
            m.append(", check debug info\n")
            m.append(ex[0]) 
        else:
            m.append(", no debug info due to MP4Decrpyt usage")
    
    await message.reply_text(" ".join(m))

async def info(p,s,ex,message):

    m = ["[" + p + "]"]

    ## search module

    if s == "search":
        m.append(ex)

    ## download module

    elif s == "startd":
        m.append(ex[3])

        t = ex[2]
        if t == "multiple":
            e = "Episode " + ex[0] 
            s = "Season " + ex[1] +","
            m.append(s)
            m.append(e)
    elif s == "subd":

        if len(ex) > 1:
            for i in range(len(ex)):
                subs = ", ".join(ex[:-1])
                subs = subs + " and " + ex[-1]
                add = "subtitles"
        else:
            subs = ex[0]
            add = "subtitle"
        m.append(subs)
        m.append(add)
        m.append("downloaded")
    elif s =="audiod":
        m.append("Downloading")
        m.append(ex)
        m.append("audio")
    elif s =="videod":
        m.append("Downloading")
        m.append(ex)
        m.append("video")
    elif s =="drmd":
        m.append("Downloading")
        m.append("DRM file")
    elif s =="imaged":
        m.append("Downloading")
        m.append("cover image")
        
    elif s == "fixurl":
        m.append("Fixing video url via uploading siaksy")

    ## decrypt module

    elif s =="foundkey":
        m.append("Decryption key found on")
        m.append(ex + " database")
    elif s =="requestkey":
        m.append("Decryption key requested from widevine server")
    elif s =="start":
        m.append("Decrypting")
        m.append(ex)

    ## combine module
    
    elif s =="combine":
        m.append("Combining files to")
        m.append(ex)
    

    await message.reply_text(" ".join(m))


async def start(title,season,episode,platform,message,l):

    music_streaming = ["tidal"]

    mes = "\n[" + platform + "] " + title
    if episode != "" and platform not in music_streaming:
        mes = mes + ", Season " + season + ", Episode " + episode 
    elif platform in music_streaming:
        mes = mes + ", Track " + episode
    await message.reply_text(mes)

async def end(message):
    await message.reply_text("[combine] Deleting temporary files")







# Moduel Made By @ThiruXD

from bot import bot, user, config_dict
from pyrogram.handlers import MessageHandler
from pyrogram.filters import command
from pyrogram import *
import os
import asyncio
import requests
import feedparser
from bs4 import BeautifulSoup
from asyncio import sleep, create_task
from re import sub
from cloudscraper import create_scraper
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from bot.helper.telegram_helper.filters import CustomFilters
from bot.modules.mirror_leech import *
from bot.helper.ext_utils.bot_utils import new_task
import pymongo
from pymongo import MongoClient
from bot import DATABASE_URL, DATABASE_NAME

temp_urls = {}  # pls dont remove this
is_auto_leecher = True # if this variable false rss will not run
AA_DELAY = 5 # it makes delay 5 seconds for avoid floot wait. 
BB_DELAY = 7 # it makes delay 7 seconds for avoid floot wait. 
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'}
IMGBB_API_KEY = "7c555e92974a9049ac25c7e6f2afa652"

# Connect to MongoDB
client = MongoClient(DATABASE_URL)
db = client[DATABASE_NAME]
rss_domains = db['rss_domains']
collection = db['rss_col_data']
thumbs = db['thumbnails']

# Function to get single domain link from db
def get_link(name):
  tk = rss_domains.find_one({"name": name})
  if tk is not None:
    return tk['url']
  else:
    return tk

# Domains
Tamilmv_domain = get_link("tmv")
Tamilblaster_domain = get_link("tbl")

# RSS Links
# 1TamilMV rss
TAMILMV_HW = f"{Tamilmv_domain}/index.php?/forums/forum/17-hollywood-movies-in-multi-audios/all.xml"  
TAMILMV_TAMIL_HD = f"{Tamilmv_domain}/index.php?/forums/forum/11-web-hd-itunes-hd-bluray/all.xml" 
TAMILMV_TAMIL_CAM = f"{Tamilmv_domain}/index.php?/forums/forum/10-predvd-dvdscr-cam-tc/all.xml"
TAMILMV_TAMIL_PERDVD = f"{Tamilmv_domain}/index.php?/forums/forum/10-predvd-dvdscr-cam-tc/all.xml"
#TAMILMV_TAMIL_WEB_SERIES = f"{Tamilmv_domain}/index.php?/forums/forum/19-web-series-tv-shows/all.xml"
TAMILMV_TELEGU_HDRIP = f"{Tamilmv_domain}/index.php?/forums/forum/25-hd-rips-dvd-rips-br-rips/all.xml"
TAMILMV_TELEGU_WEBHD = f"{Tamilmv_domain}/index.php?/forums/forum/24-web-hd-itunes-hd-bluray/all.xml"
TAMILMV_HINDI_WEBHD = f"{Tamilmv_domain}/index.php?/forums/forum/58-web-hd-itunes-hd-bluray/all.xml"
TAMILMV_MALAY_WEBHD = f"{Tamilmv_domain}/index.php?/forums/forum/36-web-hd-itunes-hd-bluray/all.xml"
TAMILMV_MALAY_PreDVD = f"{Tamilmv_domain}/index.php?/forums/forum/35-web-hd-itunes-hd-bluray/all.xml"
TAMILMV_ENGLISH_WEBHD = f"{Tamilmv_domain}/index.php?/forums/forum/49-web-hd-itunes-hd-bluray/all.xml"
# 1TamilBlasters rss
TAMILBLASTER_TAMIL = f"{Tamilblaster_domain}/index.php?/forums/forum/7-tamil-new-movies-hdrips-bdrips-dvdrips-hdtv/all.xml" 
TAMILBLASTER_HW = f"{Tamilblaster_domain}/index.php?/forums/forum/9-tamil-dubbed-movies-bdrips-hdrips-dvdscr-hdcam-in-multi-audios/all.xml" 
# If You dont want anythig you can remove from here - made by ThiruXD from ThiruEmpire
rss_urls = [TAMILMV_HW, TAMILMV_TAMIL_HD, TAMILMV_TAMIL_CAM, TAMILMV_TAMIL_PERDVD, TAMILMV_TELEGU_HDRIP, TAMILMV_TELEGU_WEBHD, TAMILMV_HINDI_WEBHD, TAMILMV_MALAY_WEBHD, TAMILMV_MALAY_PreDVD, TAMILMV_ENGLISH_WEBHD, TAMILBLASTER_TAMIL, TAMILBLASTER_HW] # Add here your rss url variable

# To Set Domain from db
@new_task
async def setdomain(client, message):
    if '|' in message.text:
        get_1st_msg = message.text.split('|')[0]
        name = get_1st_msg.split(' ')[1]
        link = message.text.split('|')[1]
        link_data = {"url": link, "title": name}
        tk = insert_or_update_link(name, link_data)
        await message.reply_text(f"{tk}")
    else:
        await message.reply_text("You Entered Wrong Format, Must Follow The Format. \n\n - How To Use: /setd [keyword] | [Domain] \n\n - KeyWords: \n `tmv` - for 1tamilmv \n `tbl` - For tamilblasters \n\n Say Jay ThiruEmpire And Try Again.")

# To Get Domains from db
@new_task
async def getdomains(client, message):
    all_links = get_all_links()
    d_list = ""
    for link in all_links:
        d_list += f"{link['url']}\n"
    await message.reply_text(f"The Domains Are: \n\n{d_list}")

# Made By ThiruXD
def insert_or_update_link(name, link_data):
  result = rss_domains.update_one({"name": name}, {"$set": link_data}, upsert=True)
  if result.matched_count == 0:
    return f"Link '{name}' inserted."
  else:
    return f"Link '{name}' updated."
  return result.upserted_id if result.upserted_count > 0 else None

# Made By ThiruXD -
def get_all_links():
  return rss_domains.find({})

# it generates text to post link
def post_to_dpaste(content):
    try:
        response = requests.post(
            "https://dpaste.org/api/",
            data={
                "content": content,
                "syntax": "json",
                "expiry_days": "360"
            }
        )
        if response.status_code == 200:
            return response.text.strip()
        else:
            return f"Failed to post to dpaste.org: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error: {e}"

def upload_to_imgbb(image_path):
    with open(image_path, "rb") as file:
        response = requests.post(
            "https://api.imgbb.com/1/upload",
            params={"key": IMGBB_API_KEY},
            files={"image": file}
        )
        if response.status_code == 200:
            return response.json()['data']['url']
        return Non

# Made By ThiruXD - this module clone's database of sudo user to bot
async def clone_ThiruEmpire(bot, message):
    # Get Bot details
    bot_info = await bot.get_me()
    bot_id = bot_info.id
    bot_username = bot_info.username
    # Get Db details
    ml_db = client['thiruml'] # Replace Your Collection
    collection = ml_db[f'users.{bot_id}']
    # Get user id
    user_id = message.from_user.id
    try:
        document_to_clone = collection.find_one({'_id': user_id})
        
        if document_to_clone:
            document_to_clone.pop('_id', None)
            document_to_clone['_id'] = bot_id
        
            existing_document = collection.find_one({'_id': bot_id})
            if existing_document:
                collection.replace_one({'_id': bot_id}, document_to_clone)
                
                try: 
                    captian = document_to_clone['lcaption']
                except:
                    captian = "Not Available ❌"
                try: 
                    tk = document_to_clone['thumb']
                    thumb = "Thumnail Saved ✅"
                except:
                    thumb = "Not Available ❌"
                try: 
                    lprefix = document_to_clone['lprefix']
                except:
                    lprefix = "Not Available ❌"
                try: 
                    lsuffix = document_to_clone['lsuffix']
                except:
                    lsuffix = "Not Available ❌"
                try: 
                    thiru = document_to_clone['as_doc']
                    if thiru == True:
                        as_doc = "Document Type"
                    else:
                        as_doc = "Media Type"
                except:
                    as_doc = "Document Type"
                try: 
                    lremname = document_to_clone['lremname']
                except:
                    lremname = "Not Available ❌"
                try: 
                    ldump = document_to_clone['ldump']
                except:
                    ldump = "Not Available ❌"

                try: 
                    metadata = document_to_clone['metadata']
                except:
                    metadata = "Not Available ❌"
                    
                await message.reply_text(f"Document updated successfully with custom _id: <code>{bot_id}</code> \n\n Source : <code>{user_id}</code>\n Media Type : <code>{as_doc}</code> \n Captian : <code>{captian}</code> \n Thumnail : <code>{thumb}</code> \n Prefix : <code>{lprefix}</code> \n Suffix : <code>{lsuffix}</code> \n Rename : <code>{lremname}</code> \n Leech Dumb : <code>{ldump}</code> \n Leech MetaData : <code>{metadata}</code> \n\nSay Jai @ThiruEmpire")
            else:
                collection.insert_one(document_to_clone)
                try: 
                    captian = document_to_clone['lcaption']
                except:
                    captian = "Not Available ❌"
                try: 
                    tk = document_to_clone['thumb']
                    thumb = "Thumnail Saved ✅"
                except:
                    thumb = "Not Available ❌"
                try: 
                    lprefix = document_to_clone['lprefix']
                except:
                    lprefix = "Not Available ❌"
                try: 
                    lsuffix = document_to_clone['lsuffix']
                except:
                    lsuffix = "Not Available ❌"
                try: 
                    thiru = document_to_clone['as_doc']
                    if thiru == True:
                        as_doc = "Document Type"
                    else:
                        as_doc = "Media Type"
                except:
                    as_doc = "Document Type"
                try: 
                    lremname = document_to_clone['lremname']
                except:
                    lremname = "Not Available ❌"
                try: 
                    ldump = document_to_clone['ldump']
                except:
                    ldump = "Not Available ❌"

                try: 
                    metadata = document_to_clone['metadata']
                except:
                    metadata = "Not Available ❌"
                    
                await message.reply_text(f"Document cloned successfully with custom _id: <code>{bot_id}</code> \n\n Source : <code>{user_id}</code>\n Media Type : <code>{as_doc}</code> \n Captian : <code>{captian}</code> \n Thumnail : <code>{thumb}</code> \n Prefix : <code>{lprefix}</code> \n Suffix : <code>{lsuffix}</code> \n Rename : <code>{lremname}</code> \n Leech Dumb : <code>{ldump}</code> \n Leech MetaData : <code>{metadata}</code> \n\nSay Jai @ThiruEmpire")
        else:
            await message.reply_text("Document not found.")
    except Exception as e:
        await message.reply_text("An error occurred:", str(e))
    
    
# This the heart of our auto leech module
@new_task
async def RSS_auto_leecher():
    print("RSS Auto Leecher Started By @ThiruXD")
    while is_auto_leecher:
        await sleep(AA_DELAY)
        try:
            for rss_url in rss_urls:
                await sleep(BB_DELAY)
                if rss_url == TAMILMV_HW:
                    keyword = 'hollywood_1tmv'
                    await tamilmv(rss_url, keyword)

                elif rss_url == TAMILMV_TAMIL_PERDVD:
                    keyword = 'tamilmv_tamil_dvd'
                    await tamilmv(rss_url, keyword)
          
              #  elif rss_url == TAMILMV_TAMIL_WEB_SERIES:
               #     keyword = 'tamilmv_tamil_web_series'
                #    await tamilmv(rss_url, keyword)

                elif rss_url == TAMILMV_TAMIL_CAM:
                    keyword = 'tamilmv_tamil_cam_rip'
                    await tamilmv(rss_url, keyword)

                elif rss_url == TAMILMV_TELEGU_HDRIP:
                    keyword = 'tamilmv_telegu_hdrip'
                    await tamilmv(rss_url, keyword)

                elif rss_url == TAMILMV_TELEGU_WEBHD:
                    keyword = 'tamilmv_telegu_webhd'
                    await tamilmv(rss_url, keyword)

                elif rss_url == TAMILMV_HINDI_WEBHD:
                    keyword = 'tamilmv_hindi_webhd'
                    await tamilmv(rss_url, keyword)

                elif rss_url == TAMILMV_MALAY_WEBHD:
                    keyword = 'tamilmv_maly_webhd'
                    await tamilmv(rss_url, keyword)

                elif rss_url == TAMILMV_MALAY_PreDVD:
                    keyword = 'tamilmv_maly_predvd'
                    await tamilmv(rss_url, keyword)

                elif rss_url == TAMILMV_ENGLISH_WEBHD:
                    keyword = 'tamilmv_english_webhd'
                    await tamilmv(rss_url, keyword)
              
                elif rss_url == TAMILBLASTER_TAMIL:
                    keyword = 'tamil_tbl'
                    await tamilblaster(rss_url, keyword)
                  
                elif rss_url == TAMILBLASTER_HW:
                    keyword = 'hollywood_tbl'
                    await tamilblaster(rss_url, keyword)
                  
                else: # Default TAMILMV_TAMIL_HD
                    keyword = 'tamil_1tmv'
                    await tamilmv(rss_url, keyword)
        except Exception as e:
            print(f"Error occurred: {e}")

# it just reated to scrap torrent file name from given link (but now its inactive)
def get_filename_from_headers(response):
    cd = response.headers.get("Content-Disposition")
    if cd:
        fname = re.findall('filename="?(.+?)"?$', cd)
        if fname:
            return fname[0]
    return "file.torrent"

# it download torrent file from source and uploads in telegram
def download_torrent(url, file_name):
    scraper = create_scraper()
    try:
        response = scraper.get(url, allow_redirects=True)
        if response.status_code == 200 and b"announce" in response.content[:500]:
           # filename = get_filename_from_headers(response)
            with open(file_name, "wb") as f:
                f.write(response.content)
            return file_name
        else:
            print("❌ Not a valid torrent file or access denied.")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

# Made By ThiruXD - It scraps data from 1tamilmv
async def tamilmv(rss_url, keyword):
    bot_info = await bot.get_me()
    bot_id = bot_info.id
    feed = feedparser.parse(rss_url)
    data = thumbs.find_one({"_id": bot_id})
    if len(feed.entries) > 0:
        # it scrapes hollywood movie link
        first_entry = feed.entries[0]
        first_link = first_entry.link

        existing_url = collection.find_one({"keyword": keyword})
        if existing_url is None or existing_url.get("url") is None:
            tk = "Nhai-Illa"
            collection.insert_one({"keyword": keyword, "url": tk})

        if existing_url["url"] != first_link:
            cget = create_scraper().request
            post_resp = cget("GET", first_link, allow_redirects=False)
            post_soup = BeautifulSoup(post_resp.text, 'html.parser')
            mag = post_soup.select('a[href^="magnet:?xt=urn:btih:"]')
            tor = post_soup.select('a[data-fileext="torrent"]')
            parse_data = f"<b><u>{post_soup.title.string}</u></b>"

            post_title = await bot.send_message(config_dict['AUTO_LEECH_GRP_ID'], f"Movie Name: {parse_data} \n\n - Say Jai BYNF \n Made By @ThiruEmpire.")
            pt_id = post_title.id
            await bot.pin_chat_message(config_dict['AUTO_LEECH_GRP_ID'], pt_id)

            MT_list = []
            for no, (t, m) in enumerate(zip(tor, mag), start=1):
                filename = sub(r"www\S+|\- |\.torrent", '', t.string)
                p_text = f'''🧲 Magnet Name: {filename} --> \n\n <code>{m['href']}</code> \n\n 🗒️Torrent file --> <a href="{t['href']}"><b>Link</b></a>.'''
                MT_list.append([f"{filename}", f"{t['href']}", f"{p_text}"])

            for atl in MT_list:
                file_name = f"{atl[0]}.torrent"
                file_link = atl[1]
                paste_text = atl[2]
                paste_link = post_to_dpaste(paste_text)
                file_caption = f"🧲 Magnet Name: {file_name} \n\n 🧲 Magnet links:\n{paste_link}"
                if download_torrent(file_link, file_name):
                    filee = await bot.send_document(chat_id=config_dict['AUTO_LEECH_GRP_ID'], document=file_name, caption=file_caption)
                    os.remove(file_name)
                    if not data:
                        try:
                            leech_msg = await filee.reply_text("/qbleech")
                            await qb_leech(bot, leech_msg)
                            await asyncio.sleep(BB_DELAY)
                            await leech_msg.delete()
                        except Exception as e:
                            await filee.reply_text(f"❌ Error: {e}")
                            return None
                    else:
                        try:
                            leech_msg = await filee.reply_text(f"/qbleech -t {data['url']}")
                            await qb_leech(bot, leech_msg)
                            await asyncio.sleep(BB_DELAY)
                            await leech_msg.delete()
                        except Exception as e:
                            await filee.reply_text(f"❌ Error: {e}")
                            return None
                else:
                    await bot.send_message(f"❌ Failed to download torrent file. \n\n {file_caption}")
                  
            collection.update_one({"keyword": keyword}, {"$set": {"url": first_link}})
            end_sticker_id = "CAACAgUAAxkBAAIjxGY75nsXUSCCFO6LB-KiGRPC5kiuAAJzBgACJggpVXKB2uxzC9oxHgQ"
            await bot.send_sticker(config_dict['AUTO_LEECH_GRP_ID'], end_sticker_id)
    else:
        msg_del = await bot.send_message(config_dict['AUTO_LEECH_GRP_ID'], f"No entries found in the feed. RSS: {rss_url}")
        await asyncio.sleep(7)
        await msg_del.delete()


# Made By ThiruXD -  It scraps data from 1tamilblaster
async def tamilblaster(rss_url, keyword):
    bot_info = await bot.get_me()
    bot_id = bot_info.id
    data = thumbs.find_one({"_id": bot_id})
    feed = feedparser.parse(rss_url)
    if len(feed.entries) > 0:
        # it scrapes hollywood movie link
        first_entry = feed.entries[0]
        first_link = first_entry.link

        existing_url = collection.find_one({"keyword": keyword})
        if existing_url is None or existing_url.get("url") is None:
            tk = "Nhai-Illa"
            collection.insert_one({"keyword": keyword, "url": tk})

        if existing_url["url"] != first_link:
            cget = create_scraper().request
            post_resp = cget("GET", first_link, allow_redirects=False)
            post_soup = BeautifulSoup(post_resp.text, 'html.parser')
            mag = post_soup.select('a[href^="magnet:?xt=urn:btih:"]')
            tor = post_soup.select('a[data-fileext="torrent"]')
            parse_data = f"<b><u>{post_soup.title.string}</u></b>"

            post_title = await bot.send_message(config_dict['AUTO_LEECH_GRP_ID'], f"Movie Name: {parse_data} \n\n - Say Jai BYNF \n Made By @ThiruEmpire.")
            pt_id = post_title.id
            await bot.pin_chat_message(config_dict['AUTO_LEECH_GRP_ID'], pt_id)

            MT_list = []
            for no, (t, m) in enumerate(zip(tor, mag), start=1):
                filename = sub(r"www\S+|\- |\.torrent", '', t.string)
                p_text = f'''🧲 Magnet Name: {filename} --> \n\n <code>{m['href']}</code> \n\n 🗒️Torrent file --> <a href="{t['href']}"><b>Link</b></a>.'''
                MT_list.append([f"{filename}", f"{t['href']}", f"{p_text}"])

            for atl in MT_list:
                file_name = f"{atl[0]}.torrent"
                file_link = atl[1]
                paste_text = atl[2]
                paste_link = post_to_dpaste(paste_text)
                file_caption = f"🧲 Magnet Name: {file_name} \n\n 🧲 Magnet links:\n{paste_link}"
                if download_torrent(file_link, file_name):
                    filee = await bot.send_document(chat_id=config_dict['AUTO_LEECH_GRP_ID'], document=file_name, caption=file_caption)
                    os.remove(file_name)
                    if not data:
                        try:
                            leech_msg = await filee.reply_text("/qbleech")
                            await qb_leech(bot, leech_msg)
                            await asyncio.sleep(BB_DELAY)
                            await leech_msg.delete()
                        except Exception as e:
                            await filee.reply_text(f"❌ Error: {e}")
                            return None
                    else:
                        try:
                            leech_msg = await filee.reply_text(f"/qbleech -t {data['url']}")
                            await qb_leech(bot, leech_msg)
                            await asyncio.sleep(BB_DELAY)
                            await leech_msg.delete()
                        except Exception as e:
                            await filee.reply_text(f"❌ Error: {e}")
                            return None
                else:
                    await bot.send_message(f"❌ Failed to download torrent file. \n\n {file_caption}")
                
            collection.update_one({"keyword": keyword}, {"$set": {"url": first_link}})
            end_sticker_id = "CAACAgUAAxkBAAIjxGY75nsXUSCCFO6LB-KiGRPC5kiuAAJzBgACJggpVXKB2uxzC9oxHgQ"
            await bot.send_sticker(config_dict['AUTO_LEECH_GRP_ID'], end_sticker_id)
    else:
       msg_del = await bot.send_message(config_dict['AUTO_LEECH_GRP_ID'], f"No entries found in the feed. RSS: {rss_url}")
       await asyncio.sleep(7)
       await msg_del.delete()

      
# to add thumnail
@new_task
async def add_thumbnail(client, message):
    if not message.reply_to_message:
        return await message.reply("⚠️ Reply to a photo to set as thumbnail.")

    if not message.reply_to_message.photo:
        return await message.reply("⚠️ Reply to a photo to set as thumbnail.")

    bot_info = await bot.get_me()
    bot_id = bot_info.id
    file_path = await message.reply_to_message.download()
    
    url = upload_to_imgbb(file_path)
    os.remove(file_path)

    if not url:
        return await message.reply("❌ Failed to upload thumbnail to imgbb.")
    
    thumbs.update_one({"_id": bot_id}, {"$set": {"url": url}}, upsert=True)
    await message.reply(f"✅ Thumbnail added!\nURL: {url}")

# to get thumnail
@new_task
async def show_thumbnail(client, message):
    bot_info = await bot.get_me()
    bot_id = bot_info.id
    data = thumbs.find_one({"_id": bot_id})
    
    if not data:
        return await message.reply("❌ No thumbnail found.")
    
    await message.reply_photo(photo=data['url'], caption=f"📸 Your current thumbnail - {data['url']}")

# to delete thumnail
@new_task
async def delete_thumbnail(client, message):
    bot_info = await bot.get_me()
    bot_id = bot_info.id
    result = thumbs.delete_one({"_id": bot_id})
    
    if result.deleted_count == 0:
        return await message.reply("❌ No thumbnail to delete.")
    
    await message.reply("🗑️ Thumbnail deleted.")

# Made By ThiruXD
@new_task
async def mannual_scrape(client, message):
    bot_info = await bot.get_me()
    bot_id = bot_info.id
    data = thumbs.find_one({"_id": bot_id})
    if ' ' in message.text:
        get_url = message.text.split(' ')[1]
    else:
      return await message.reply(f"add any url....")
    cget = create_scraper().request
    post_resp = cget("GET", get_url, allow_redirects=False)
    post_soup = BeautifulSoup(post_resp.text, 'html.parser')
    mag = post_soup.select('a[href^="magnet:?xt=urn:btih:"]')
    tor = post_soup.select('a[data-fileext="torrent"]')
    parse_data = f"<b><u>{post_soup.title.string}</u></b>"

    post_title = await message.reply(f"Movie Name: {parse_data} \n\n - Say Jai BYNF \n Made By @ThiruEmpire.")

    MT_list = []
    for no, (t, m) in enumerate(zip(tor, mag), start=1):
      filename = sub(r"www\S+|\- |\.torrent", '', t.string)
      p_text = f'''🧲 Magnet Name: {filename} --> \n\n <code>{m['href']}</code> \n\n 🗒️Torrent file --> <a href="{t['href']}"><b>Link</b></a>.'''
      MT_list.append([f"{filename}", f"{t['href']}", f"{p_text}"])

    for atl in MT_list:
      file_name = f"{atl[0]}.torrent"
      file_link = atl[1]
      paste_text = atl[2]
      paste_link = post_to_dpaste(paste_text)
      file_caption = f"🧲 Magnet Name: {file_name} \n\n 🧲 Magnet links:\n{paste_link}"
      if download_torrent(file_link, file_name):
        await asyncio.sleep(3)
        filee = await bot.send_document(chat_id=config_dict['AUTO_LEECH_GRP_ID'], document=file_name, caption=file_caption)
        os.remove(file_name)
        if not data:
          try:
            leech_msg = await filee.reply_text("/qbleech")
            await qb_leech(bot, leech_msg)
            await asyncio.sleep(BB_DELAY)
            await leech_msg.delete()
          except Exception as e:
            await filee.reply_text(f"❌ Error: {e}")
            return None
        else:
          try:
            leech_msg = await filee.reply_text(f"/qbleech -t {data['url']}")
            await qb_leech(bot, leech_msg)
            await asyncio.sleep(BB_DELAY)
            await leech_msg.delete()
          except Exception as e:
            await filee.reply_text(f"❌ Error: {e}")
            return None
      else:
        await bot.send_message(f"❌ Failed to download torrent file. \n\n {file_caption}")



# Leech help command
@new_task
async def auto_leech_help(client, message):
    HELP_TEXT_AA = """<b>⌬ Auto Leech Commands:
Manual Leech Commands:
- /scrape <i>[url]</i> : to scrape magnet from 1TamilMv or 1TamilBlasters.

Steps To Activate Your Auto Leech:</b>
┠ Step No 1 :</b> Add an <i>AUTO_LEECH_GRP_ID</i> in config file or add in bot settings /bs and then restart the bot.

┠ <b>Step No 2 :</b> Add an supported website Url by using this command.
   - /setd <i>[keyword] | [Domain]</i>
   - /getd: <i>To get active domain list.</i>
   - <i>Supported website keyWords:
      - tmv : <i>for 1TamilMv</i>
      - tbl : <i>for 1TamilBlasters</i>
      - <i>Other websites comming soon request <a href="t.me/ThiruSupport">here</a>...</i>
   
┠ <b>Step No 3 :</b> Add caption, prefix, sufix and dump channel etc...
   - /us: <i>Set your leech setting.</i>
   
┠ <b>Step No 4 : </b> now set all changes to bot.
   - /setlbot: <i>After adding all datas in user settings.</i>

┠ <b>Step No 5 : </b> now set thumnail.
   - /add_thumb: <i>(reply to a image) To add new thumnail.</i>
   - /show_thumb: <i>To add see or get thumnail.</i>
   - /del_thumb: <i>To delete new thumnail.</i>
   
┖ <b>Finally :</b> That's all guys, if bot not works restart the bot and wait 5min and see the magic.

<b>Made By @ThiruXD - <a href="github.com/ThiruXD">GitHub</a>
Powered By @ThiruEmpire</b>
"""
    await message.reply_text(HELP_TEXT_AA)

  
# if any doubt contact @ThiruXD in telegram 
RSS_auto_leecher()
bot.add_handler(MessageHandler(auto_leech_help, filters=command("auto_leech") & CustomFilters.sudo))
bot.add_handler(MessageHandler(clone_ThiruEmpire, filters=command("setlbot") & CustomFilters.sudo))
bot.add_handler(MessageHandler(setdomain, filters=command("setd") & CustomFilters.sudo))
bot.add_handler(MessageHandler(getdomains, filters=command("getd") & CustomFilters.sudo))
bot.add_handler(MessageHandler(add_thumbnail, filters=command("add_thumb") & CustomFilters.sudo))
bot.add_handler(MessageHandler(show_thumbnail, filters=command("show_thumb") & CustomFilters.sudo))
bot.add_handler(MessageHandler(delete_thumbnail, filters=command("del_thumb") & CustomFilters.sudo))
bot.add_handler(MessageHandler(mannual_scrape, filters=command("scrape") & CustomFilters.sudo))

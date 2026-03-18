# Moduel Made By @ThiruXD

from bot import bot, user, config_dict, OWNER_ID
from pyrogram.handlers import MessageHandler
from pyrogram.filters import command
from pyrogram import *
import os
import re
import time
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
from bot.helper.ext_utils.bot_utils import new_task, sync_to_async
import pymongo
from pymongo import MongoClient
from bot import DATABASE_URL, DATABASE_NAME

# Shared scraper instance — created once, reused everywhere (saves memory/CPU)
_scraper = create_scraper()

temp_urls = {}  # pls dont remove this
is_auto_leecher = True  # if this variable false rss will not run
AA_DELAY = 5            # delay between full loop cycles (seconds)
BB_DELAY = 7            # delay between each feed / each leech dispatch (seconds)
PENDING_RETRY_INTERVAL = 120   # retry pending posts every 2 minutes
PENDING_MAX_AGE        = 3600  # drop pending posts after 1 hour
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'}
IMGBB_API_KEY = "7c555e92974a9049ac25c7e6f2afa652"

# Connect to MongoDB
client = MongoClient(DATABASE_URL)
db = client[DATABASE_NAME]
rss_domains = db['rss_domains']
collection  = db['rss_col_data']
thumbs      = db['thumbnails']

# ------------------------------------------------------------------
# Pending queue: posts where the site hasn't added torrent files yet
# { url: { 'title': str, 'keyword': str, 'added_at': float } }
# In-memory only — clears on bot restart (stale pending posts drop cleanly)
# ------------------------------------------------------------------
pending_posts = {}


# ── Domain helpers ─────────────────────────────────────────────────

def get_link(name):
    tk = rss_domains.find_one({"name": name})
    return tk['url'] if tk is not None else None

Tamilmv_domain    = get_link("tmv")
Tamilblaster_domain = get_link("tbl")

# RSS Links — 1TamilMV
TAMILMV_HW            = f"{Tamilmv_domain}/index.php?/forums/forum/17-hollywood-movies-in-multi-audios/all.xml"
TAMILMV_TAMIL_HD      = f"{Tamilmv_domain}/index.php?/forums/forum/11-web-hd-itunes-hd-bluray/all.xml"
TAMILMV_TAMIL_CAM     = f"{Tamilmv_domain}/index.php?/forums/forum/10-predvd-dvdscr-cam-tc/all.xml"
TAMILMV_TAMIL_WEB_SERIES = f"{Tamilmv_domain}/index.php?/forums/forum/19-web-series-tv-shows/all.xml"
TAMILMV_TELEGU_HDRIP  = f"{Tamilmv_domain}/index.php?/forums/forum/25-hd-rips-dvd-rips-br-rips/all.xml"
TAMILMV_TELEGU_WEBHD  = f"{Tamilmv_domain}/index.php?/forums/forum/24-web-hd-itunes-hd-bluray/all.xml"
TAMILMV_HINDI_WEBHD   = f"{Tamilmv_domain}/index.php?/forums/forum/58-web-hd-itunes-hd-bluray/all.xml"
TAMILMV_MALAY_WEBHD   = f"{Tamilmv_domain}/index.php?/forums/forum/36-web-hd-itunes-hd-bluray/all.xml"
TAMILMV_MALAY_PreDVD  = f"{Tamilmv_domain}/index.php?/forums/forum/35-web-hd-itunes-hd-bluray/all.xml"
TAMILMV_ENGLISH_WEBHD = f"{Tamilmv_domain}/index.php?/forums/forum/49-web-hd-itunes-hd-bluray/all.xml"
# RSS Links — 1TamilBlasters
TAMILBLASTER_TAMIL = f"{Tamilblaster_domain}/index.php?/forums/forum/7-tamil-new-movies-hdrips-bdrips-dvdrips-hdtv/all.xml"
TAMILBLASTER_HW    = f"{Tamilblaster_domain}/index.php?/forums/forum/9-tamil-dubbed-movies-bdrips-hdrips-dvdscr-hdcam-in-multi-audios/all.xml"

# Removed duplicate TAMILMV_TAMIL_PERDVD (was identical URL to TAMILMV_TAMIL_CAM)
# Added TAMILMV_TAMIL_HD which was missing from the list before
rss_urls = [
    TAMILMV_HW, TAMILMV_TAMIL_HD, TAMILMV_TAMIL_CAM,
    TAMILMV_TELEGU_HDRIP, TAMILMV_TELEGU_WEBHD, TAMILMV_HINDI_WEBHD,
    TAMILMV_MALAY_WEBHD, TAMILMV_MALAY_PreDVD, TAMILMV_ENGLISH_WEBHD,
    TAMILBLASTER_TAMIL, TAMILBLASTER_HW, TAMILMV_TAMIL_WEB_SERIES
]


# ── Domain commands ────────────────────────────────────────────────

@new_task
async def setdomain(client, message):
    if '|' in message.text:
        name = message.text.split('|')[0].split(' ')[1].strip()
        link = message.text.split('|')[1].strip()
        tk = insert_or_update_link(name, {"url": link, "title": name})
        await message.reply_text(f"{tk}")
    else:
        await message.reply_text(
            "Wrong format!\n\nHow To Use: /setd [keyword] | [Domain]\n\n"
            "KeyWords:\n  tmv - for 1tamilmv\n  tbl - For tamilblasters"
        )

@new_task
async def getdomains(client, message):
    d_list = "".join(f"{l['url']}\n" for l in get_all_links())
    await message.reply_text(f"The Domains Are:\n\n{d_list or 'None set.'}")

def insert_or_update_link(name, link_data):
    result = rss_domains.update_one({"name": name}, {"$set": link_data}, upsert=True)
    return f"Link '{name}' {'inserted' if result.matched_count == 0 else 'updated'}."

def get_all_links():
    return rss_domains.find({})


# ── Utility functions ──────────────────────────────────────────────

def post_to_dpaste(content):
    try:
        r = requests.post("https://dpaste.org/api/",
                          data={"content": content, "syntax": "json", "expiry_days": "360"})
        return r.text.strip() if r.status_code == 200 else f"dpaste error: {r.status_code}"
    except Exception as e:
        return f"Error: {e}"

def upload_to_imgbb(image_path):
    with open(image_path, "rb") as f:
        r = requests.post("https://api.imgbb.com/1/upload",
                          params={"key": IMGBB_API_KEY}, files={"image": f})
    return r.json()['data']['url'] if r.status_code == 200 else None

def download_torrent(url, file_name):
    try:
        r = _scraper.get(url, allow_redirects=True)
        if r.status_code == 200 and b"announce" in r.content[:500]:
            with open(file_name, "wb") as f:
                f.write(r.content)
            return file_name
        print("❌ Not a valid torrent or access denied.")
        return None
    except Exception as e:
        print(f"❌ download_torrent error: {e}")
        return None

def scrape_links(post_url):
    """Fetch post page, return (tor, mag, title). Returns (None, None, None) on error."""
    try:
        r = _scraper.request("GET", post_url, allow_redirects=True)
        soup = BeautifulSoup(r.text, 'html.parser')
        mag  = soup.select('a[href^="magnet:?xt=urn:btih:"]')
        tor  = soup.select('a[data-fileext="torrent"]')
        title = soup.title.string if soup.title else post_url
        return tor, mag, title
    except Exception as e:
        print(f"❌ scrape_links error for {post_url}: {e}")
        return None, None, None


# ── MT_list builder (fixes the zip bug) ───────────────────────────

def build_mt_list(tor, mag):
    """
    Build MT_list from torrent and magnet links independently.
    Old code used zip(tor, mag) which produced an empty list whenever
    a post had only torrent links (common for web series) — now fixed.
    """
    MT_list = []

    # Torrent links — pair with magnet at same index if one exists
    for i, t in enumerate(tor):
        filename = sub(r"www\S+|\- |\.torrent", '', t.string or '').strip()
        if not filename:
            continue
        if i < len(mag):
            m = mag[i]
            p_text = (f'🧲 Magnet Name: {filename} -->\n\n'
                      f'<code>{m["href"]}</code>\n\n'
                      f'🗒️ Torrent --> <a href="{t["href"]}"><b>Link</b></a>.')
        else:
            p_text = f'🗒️ Torrent: {filename} --> <a href="{t["href"]}"><b>Link</b></a>.'
        MT_list.append([filename, t['href'], p_text, 'torrent'])

    # Excess magnet-only links (more magnets than torrents)
    for i, m in enumerate(mag):
        if i < len(tor):
            continue
        raw  = m['href'].split('dn=')[-1].split('&')[0]
        name = requests.utils.unquote(raw).replace('+', ' ').strip() or f"magnet_{i+1}"
        p_text = f'🧲 Magnet: {name}\n\n<code>{m["href"]}</code>'
        MT_list.append([name, m['href'], p_text, 'magnet'])

    return MT_list


# ── Leech dispatcher ───────────────────────────────────────────────

async def leech_mt_list(MT_list):
    owner_user = await bot.get_users(OWNER_ID)
    for atl in MT_list:
        file_name  = os.path.basename(atl[0]) + ".torrent"
        file_link  = atl[1]
        link_type  = atl[3]
        paste_link = await sync_to_async(post_to_dpaste, atl[2])
        caption    = f"🗒️ Name: {atl[0]}\n\n🔗 Links:\n{paste_link}"
        try:
            if link_type == 'magnet':
                leech_msg = await bot.send_message(
                    chat_id=config_dict['AUTO_LEECH_GRP_ID'],
                    text=f"/qbleech {file_link}\nTag: @{owner_user.username} {OWNER_ID}"
                )
                leech_msg.from_user = owner_user
                await qb_leech(bot, leech_msg)
                await asyncio.sleep(BB_DELAY)
                await leech_msg.delete()
            else:
                if await sync_to_async(download_torrent, file_link, file_name):
                    filee = await bot.send_document(
                        chat_id=config_dict['AUTO_LEECH_GRP_ID'],
                        document=file_name, caption=caption
                    )
                    os.remove(file_name)
                    leech_msg = await filee.reply_text(
                        f"/qbleech\nTag: @{owner_user.username} {OWNER_ID}"
                    )
                    leech_msg.from_user = owner_user
                    await qb_leech(bot, leech_msg)
                    await asyncio.sleep(BB_DELAY)
                    await leech_msg.delete()
                else:
                    await bot.send_message(
                        chat_id=config_dict['AUTO_LEECH_GRP_ID'],
                        text=f"❌ Failed to download torrent.\n\n{caption}"
                    )
        except Exception as e:
            await bot.send_message(
                chat_id=config_dict['AUTO_LEECH_GRP_ID'],
                text=f"❌ Error leeching {atl[0]}: {e}"
            )
        await asyncio.sleep(BB_DELAY)


# ── Pending queue worker ───────────────────────────────────────────

@new_task
async def pending_queue_worker():
    """
    Background task that re-checks posts which had no torrent links when
    first seen. 1TamilMV sometimes posts the page before uploading the
    torrent files (can be 10–30 mins delayed).

    - Retries every PENDING_RETRY_INTERVAL seconds (default: 2 mins)
    - Drops posts older than PENDING_MAX_AGE seconds (default: 1 hour)
    - Once links appear: announces, updates DB, leeches, removes from queue
    """
    print("⏳ Pending queue worker started")
    while True:
        await sleep(PENDING_RETRY_INTERVAL)
        if not pending_posts:
            continue

        now = time.time()
        to_delete = []

        for post_url, meta in list(pending_posts.items()):
            age = now - meta['added_at']

            # Give up after max age
            if age > PENDING_MAX_AGE:
                print(f"🗑️ Dropping stale pending post ({int(age//60)}m old): {post_url}")
                to_delete.append(post_url)
                await bot.send_message(
                    chat_id=config_dict['AUTO_LEECH_GRP_ID'],
                    text=(f"⚠️ Gave up waiting for torrent links after {PENDING_MAX_AGE//60} mins:\n"
                          f"<b>{meta['title']}</b>\n\n{post_url}")
                )
                continue

            # Re-scrape the page
            tor, mag, title = await sync_to_async(scrape_links, post_url)
            if tor is None:
                continue  # network error, retry next cycle

            MT_list = build_mt_list(tor, mag)
            if not MT_list:
                print(f"⏳ Still no links for '{meta['title']}' ({int(age//60)}m elapsed)")
                continue

            # Links appeared — leech it now
            print(f"✅ Pending post now has links: {post_url}")
            try:
                post_title = await bot.send_message(
                    chat_id=config_dict['AUTO_LEECH_GRP_ID'],
                    text=(f"✅ Torrent links ready (was pending {int(age//60)} mins)!\n"
                          f"Movie Name: <b><u>{title}</u></b>\n\nMade By @ThiruEmpire.")
                )
                try:
                    await bot.pin_chat_message(config_dict['AUTO_LEECH_GRP_ID'], post_title.id)
                except Exception:
                    pass

                # Update DB so main RSS loop skips it from now on
                await sync_to_async(collection.update_one,
                    {"keyword": meta['keyword']},
                    {"$set": {"url": post_url}},
                    upsert=True
                )

                await leech_mt_list(MT_list)

                end_sticker_id = "CAACAgUAAxkBAAIjxGY75nsXUSCCFO6LB-KiGRPC5kiuAAJzBgACJggpVXKB2uxzC9oxHgQ"
                await bot.send_sticker(config_dict['AUTO_LEECH_GRP_ID'], end_sticker_id)

            except Exception as e:
                print(f"❌ Error leeching pending post {post_url}: {e}")

            to_delete.append(post_url)

        for url in to_delete:
            pending_posts.pop(url, None)


# ── Main RSS scrapers ──────────────────────────────────────────────

async def _process_feed(rss_url, keyword):
    """Shared logic for both tamilmv and tamilblaster."""
    feed = await sync_to_async(feedparser.parse, rss_url)
    if len(feed.entries) == 0:
        msg = await bot.send_message(
            config_dict['AUTO_LEECH_GRP_ID'],
            f"No entries found in the feed. RSS: {rss_url}"
        )
        await asyncio.sleep(7)
        await msg.delete()
        return

    first_link = feed.entries[0].link

    # Already pending — worker handles it, skip
    if first_link in pending_posts:
        return

    existing = await sync_to_async(collection.find_one, {"keyword": keyword})
    if existing is None or existing.get("url") is None:
        await sync_to_async(collection.insert_one, {"keyword": keyword, "url": "Nhai-Illa"})
        existing = {"url": "Nhai-Illa"}

    # Already seen and leeched — nothing to do
    if existing["url"] == first_link:
        return

    tor, mag, title = await sync_to_async(scrape_links, first_link)
    if tor is None:
        return  # network error

    MT_list = build_mt_list(tor, mag)

    if not MT_list:
        # Page exists but torrent files not uploaded yet — add to pending queue
        print(f"⏳ No links yet for '{title}', queuing: {first_link}")
        pending_posts[first_link] = {
            'title':    title,
            'keyword':  keyword,
            'added_at': time.time()
        }
        await bot.send_message(
            chat_id=config_dict['AUTO_LEECH_GRP_ID'],
            text=(f"⏳ New post detected but no torrent links yet.\n"
                  f"Movie Name: <b><u>{title}</u></b>\n\n"
                  f"Will auto-leech when links appear "
                  f"(checking every {PENDING_RETRY_INTERVAL // 60} mins, giving up after {PENDING_MAX_AGE // 60} mins).")
        )
        # Do NOT update DB — so if bot restarts the post isn't lost
        return

    # Links found immediately — announce, update DB, leech
    post_title = await bot.send_message(
        config_dict['AUTO_LEECH_GRP_ID'],
        f"Movie Name: <b><u>{title}</u></b>\n\n - Say Jai BYNF\n Made By @ThiruEmpire."
    )
    try:
        await bot.pin_chat_message(config_dict['AUTO_LEECH_GRP_ID'], post_title.id)
    except Exception:
        pass

    await sync_to_async(collection.update_one, {"keyword": keyword}, {"$set": {"url": first_link}})
    await leech_mt_list(MT_list)

    end_sticker_id = "CAACAgUAAxkBAAIjxGY75nsXUSCCFO6LB-KiGRPC5kiuAAJzBgACJggpVXKB2uxzC9oxHgQ"
    await bot.send_sticker(config_dict['AUTO_LEECH_GRP_ID'], end_sticker_id)


async def tamilmv(rss_url, keyword):
    await _process_feed(rss_url, keyword)

async def tamilblaster(rss_url, keyword):
    await _process_feed(rss_url, keyword)


# ── Main RSS loop ──────────────────────────────────────────────────

@new_task
async def RSS_auto_leecher():
    print("RSS Auto Leecher Started By @ThiruXD")
    while is_auto_leecher:
        await sleep(AA_DELAY)
        try:
            for rss_url in rss_urls:
                await sleep(BB_DELAY)
                if   rss_url == TAMILMV_HW:            await tamilmv(rss_url, 'hollywood_1tmv')
                elif rss_url == TAMILMV_TAMIL_HD:       await tamilmv(rss_url, 'tamilmv_tamil_hd')
                elif rss_url == TAMILMV_TAMIL_CAM:      await tamilmv(rss_url, 'tamilmv_tamil_cam_rip')
                elif rss_url == TAMILMV_TAMIL_WEB_SERIES: await tamilmv(rss_url, 'tamilmv_tamil_web_series')
                elif rss_url == TAMILMV_TELEGU_HDRIP:   await tamilmv(rss_url, 'tamilmv_telegu_hdrip')
                elif rss_url == TAMILMV_TELEGU_WEBHD:   await tamilmv(rss_url, 'tamilmv_telegu_webhd')
                elif rss_url == TAMILMV_HINDI_WEBHD:    await tamilmv(rss_url, 'tamilmv_hindi_webhd')
                elif rss_url == TAMILMV_MALAY_WEBHD:    await tamilmv(rss_url, 'tamilmv_maly_webhd')
                elif rss_url == TAMILMV_MALAY_PreDVD:   await tamilmv(rss_url, 'tamilmv_maly_predvd')
                elif rss_url == TAMILMV_ENGLISH_WEBHD:  await tamilmv(rss_url, 'tamilmv_english_webhd')
                elif rss_url == TAMILBLASTER_TAMIL:     await tamilblaster(rss_url, 'tamil_tbl')
                elif rss_url == TAMILBLASTER_HW:        await tamilblaster(rss_url, 'hollywood_tbl')
        except Exception as e:
            print(f"Error occurred: {e}")


# ── Clone settings ─────────────────────────────────────────────────

async def clone_ThiruEmpire(bot, message):
    bot_id  = bot.me.id
    col     = client['thiruml'][f'users.{bot_id}']
    user_id = message.from_user.id
    try:
        doc = col.find_one({'_id': user_id})
        if not doc:
            return await message.reply_text("Document not found.")

        doc.pop('_id', None)
        doc['_id'] = bot_id
        action = "updated" if col.find_one({'_id': bot_id}) else "cloned"
        if action == "updated":
            col.replace_one({'_id': bot_id}, doc)
        else:
            col.insert_one(doc)

        s = {
            'captian':  doc.get('lcaption', 'Not Available ❌'),
            'thumb':    'Thumbnail Saved ✅' if doc.get('thumb') else 'Not Available ❌',
            'lprefix':  doc.get('lprefix',  'Not Available ❌'),
            'lsuffix':  doc.get('lsuffix',  'Not Available ❌'),
            'as_doc':   'Document Type' if doc.get('as_doc', True) else 'Media Type',
            'lremname': doc.get('lremname', 'Not Available ❌'),
            'ldump':    doc.get('ldump',    'Not Available ❌'),
            'metadata': doc.get('metadata', 'Not Available ❌'),
        }
        await message.reply_text(
            f"Document {action} with _id: <code>{bot_id}</code>\n\n"
            f" Source: <code>{user_id}</code>\n"
            f" Media Type: <code>{s['as_doc']}</code>\n"
            f" Caption: <code>{s['captian']}</code>\n"
            f" Thumbnail: <code>{s['thumb']}</code>\n"
            f" Prefix: <code>{s['lprefix']}</code>\n"
            f" Suffix: <code>{s['lsuffix']}</code>\n"
            f" Rename: <code>{s['lremname']}</code>\n"
            f" Leech Dump: <code>{s['ldump']}</code>\n"
            f" Metadata: <code>{s['metadata']}</code>\n\n"
            f"Say Jai @ThiruEmpire"
        )
    except Exception as e:
        await message.reply_text(f"An error occurred: {e}")


# ── Thumbnail commands ─────────────────────────────────────────────

@new_task
async def add_thumbnail(client, message):
    if not message.reply_to_message or not message.reply_to_message.photo:
        return await message.reply("⚠️ Reply to a photo to set as thumbnail.")
    bot_id    = bot.me.id
    file_path = await message.reply_to_message.download()
    url       = upload_to_imgbb(file_path)
    os.remove(file_path)
    if not url:
        return await message.reply("❌ Failed to upload thumbnail to imgbb.")
    thumbs.update_one({"_id": bot_id}, {"$set": {"url": url}}, upsert=True)
    await message.reply(f"✅ Thumbnail added!\nURL: {url}")

@new_task
async def show_thumbnail(client, message):
    data = thumbs.find_one({"_id": bot.me.id})
    if not data:
        return await message.reply("❌ No thumbnail found.")
    await message.reply_photo(photo=data['url'], caption=f"📸 Current thumbnail - {data['url']}")

@new_task
async def delete_thumbnail(client, message):
    result = thumbs.delete_one({"_id": bot.me.id})
    if result.deleted_count == 0:
        return await message.reply("❌ No thumbnail to delete.")
    await message.reply("🗑️ Thumbnail deleted.")


# ── Manual scrape ──────────────────────────────────────────────────

@new_task
async def mannual_scrape(client, message):
    if ' ' not in message.text:
        return await message.reply("add any url....")
    get_url = message.text.split(' ')[1]

    tor, mag, title = await sync_to_async(scrape_links, get_url)
    if tor is None:
        return await message.reply("❌ Failed to fetch the page.")

    await message.reply(f"Movie Name: <b><u>{title}</u></b>\n\n - Say Jai BYNF\n Made By @ThiruEmpire.")

    MT_list = build_mt_list(tor, mag)
    if not MT_list:
        return await message.reply("❌ No torrent or magnet links found on this page.")

    await leech_mt_list(MT_list)


# ── Help ───────────────────────────────────────────────────────────

@new_task
async def auto_leech_help(client, message):
    await message.reply_text("""<b>⌬ Auto Leech Commands:
Manual Leech Commands:
- /scrape <i>[url]</i> : to scrape magnet from 1TamilMv or 1TamilBlasters.

Steps To Activate Your Auto Leech:</b>
┠ <b>Step No 1 :</b> Add an <i>AUTO_LEECH_GRP_ID</i> in config file or add in bot settings /bs and then restart the bot.

┠ <b>Step No 2 :</b> Add supported website URL:
   - /setd <i>[keyword] | [Domain]</i>
   - /getd: <i>To get active domain list.</i>
   - Keywords: tmv (1TamilMv), tbl (1TamilBlasters)

┠ <b>Step No 3 :</b> Add caption, prefix, suffix and dump channel etc...
   - /us: <i>Set your leech setting.</i>

┠ <b>Step No 4 :</b> Apply settings to bot.
   - /setlbot: <i>After adding all data in user settings.</i>

┠ <b>Step No 5 :</b> Set thumbnail.
   - /add_thumb: <i>(reply to image) Add thumbnail.</i>
   - /show_thumb: <i>View thumbnail.</i>
   - /del_thumb: <i>Delete thumbnail.</i>

┖ <b>Finally :</b> Restart the bot and wait 5 mins.

<b>Made By @ThiruXD - <a href="github.com/ThiruXD">GitHub</a>
Powered By @ThiruEmpire</b>""")


# ── Start workers and register handlers ───────────────────────────

RSS_auto_leecher()
pending_queue_worker()  # background worker for posts with delayed torrent uploads

bot.add_handler(MessageHandler(auto_leech_help,   filters=command("auto_leech") & CustomFilters.sudo))
bot.add_handler(MessageHandler(clone_ThiruEmpire, filters=command("setlbot")    & CustomFilters.sudo))
bot.add_handler(MessageHandler(setdomain,         filters=command("setd")       & CustomFilters.sudo))
bot.add_handler(MessageHandler(getdomains,        filters=command("getd")       & CustomFilters.sudo))
bot.add_handler(MessageHandler(add_thumbnail,     filters=command("add_thumb")  & CustomFilters.sudo))
bot.add_handler(MessageHandler(show_thumbnail,    filters=command("show_thumb") & CustomFilters.sudo))
bot.add_handler(MessageHandler(delete_thumbnail,  filters=command("del_thumb")  & CustomFilters.sudo))
bot.add_handler(MessageHandler(mannual_scrape,    filters=command("scrape")     & CustomFilters.sudo))

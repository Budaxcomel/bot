#ULAH DI BEREKEUN DEUI KA SASAHA
#KODE CREATE AAGIN
#COPYRIGHT 2023
#ULAH DI UPLOAD ULANG KNTL
import sqlite3
import os.path
import os
import asyncio
from statistics import mean, stdev
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telethon import TelegramClient, events
from ping3 import ping
from dotenv import dotenv_values
from utils import speedtest

scheduler = AsyncIOScheduler()
scheduler.start()

config = dotenv_values("config.env")
API_ID = config["API_ID"]
API_HASH = config["API_HASH"]
BOT_TOKEN = config["BOT_TOKEN"]
GROUP_ID = int(config["GROUP_ID"])
ADMIN_ID = int(config["ADMIN_ID"])

bot = TelegramClient('immanvpn', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

if not os.path.isfile('database.db'):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT,
            domain TEXT
        )
    ''')

    conn.commit()
    conn.close()

emoticon_up = "\U0001F7E2"
emoticon_down = "\U0001F534"

server_status = {} 

async def send_notification(ip, domain, avg_latency, jitter):
    global server_status

    if avg_latency == float('inf') and jitter == float('inf'):
        # Server dalam kondisi jelek (PING mengembalikan nilai inf)
        message = f"**__SERVER__** :{ip}\n"
        message += f"**__DOMAIN__** :{domain}\n"
        message += f"__Sedang Down__ ❌\n"
        message += f"▰▱▰▱▰▱▰▱▰▱▰▱\n\n"
        message += f"    ⚡**Latency**: {avg_latency}\n"
        message += f"    ⚡**Jitter**: {jitter}\n"
        message += f"     {emoticon_down}\n"
        message += f"▰▱▰▱▰▱▰▱▰▱▰▱\n"
        await bot.send_message(GROUP_ID, message)
        server_status[ip] = "down"
    elif server_status.get(ip) != "down" and (avg_latency > 100 or jitter > 10):
        # Server dalam kondisi jelek (PING mengembalikan nilai terukur)
        message = f"**__SERVER__** :{ip}\n"
        message += f"**__DOMAIN__** :{domain}\n"
        message += f"__Sedang Down__ ❌\n"
        message += f"▰▱▰▱▰▱▰▱▰▱▰▱\n\n"
        message += f"    ⚡**Latency**: {avg_latency:.2f} ms\n"
        message += f"    ⚡**Jitter**: {jitter:.2f} ms\n"
        message += f"     {emoticon_down}\n"
        message += f"▰▱▰▱▰▱▰▱▰▱▰▱\n"
        await bot.send_message(GROUP_ID, message)
        server_status[ip] = "down"
    elif server_status.get(ip) == "down" and avg_latency <= 100 and jitter <= 10:
        # Server kembali dalam kondisi baik setelah sebelumnya jelek
        message = f"**__SERVER__** :{ip}\n"
        message += f"**__DOMAIN__** :{domain}\n"
        message += f"__Kembali Normal__ ✅\n"
        message += f"▰▱▰▱▰▱▰▱▰▱▰▱\n\n"
        message += f"    ⚡**Latency**: {avg_latency:.2f} ms\n"
        message += f"    ⚡**Jitter**: {jitter:.2f} ms\n"
        message += f"     {emoticon_up}\n"
        message += f"▰▱▰▱▰▱▰▱▰▱▰▱\n"
        await bot.send_message(GROUP_ID, message)
        server_status[ip] = "up"

@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    await event.reply("Hai, saya Bot Ping All Server")

@bot.on(events.NewMessage(pattern='/speedtest'))
async def speedtest_handler_wrapper(event):
    await speedtest.speedtest_handler(event)

@bot.on(events.NewMessage(pattern='/list_ip'))
async def list_ip_handler(event):
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT ip, domain FROM ips')
        results = cursor.fetchall()
        conn.close()

        if len(results) > 0:
            message = "**Daftar IP dan Domain**:\n\n"
            for row in results:
                ip = row[0]
                domain = row[1]
                message += f"- IP: {ip}, Domain: {domain}\n"

            await event.reply(message)
        else:
            await event.reply("Tidak ada IP dan domain yang tersimpan dalam database.")

    except Exception as e:
        await event.reply(f"Terjadi kesalahan saat mengambil daftar IP dan domain: {str(e)}")

@bot.on(events.NewMessage(pattern='/add_ip'))
async def add_ip_handler(event):
    try:
        if event.sender_id != ADMIN_ID:
            await event.reply("Hanya admin yang dapat menambahkan IP dan domain.")
            return

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        ip_domain = event.raw_text.split('/add_ip ')[1].strip()
        if not ip_domain:
            await event.reply("Mohon berikan IP dan domain dalam format yang benar.")
            return

        ip, domain = ip_domain.split()

        cursor.execute('INSERT INTO ips (ip, domain) VALUES (?, ?)', (ip, domain))
        conn.commit()
        conn.close()

        await event.reply(f"IP {ip} dengan domain {domain} berhasil ditambahkan ke database.")
    except Exception as e:
        await event.reply(f"Terjadi kesalahan saat menambahkan IP ke database: {str(e)}")

@bot.on(events.NewMessage(pattern='/remove_ip'))
async def remove_ip_handler(event):
    try:
        if event.sender_id != ADMIN_ID:
            await event.reply("Hanya admin yang dapat menghapus IP atau domain.")
            return

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        command = event.raw_text.split('/remove_ip ')[1].strip()
        if not command:
            await event.reply("Mohon berikan IP atau domain yang akan dihapus.")
            return

        if command.replace('.', '').isdigit():
            cursor.execute('DELETE FROM ips WHERE ip = ?', (command,))
            await event.reply(f"IP {command} berhasil dihapus dari database.")
        else:
            cursor.execute('DELETE FROM ips WHERE domain = ?', (command,))
            await event.reply(f"Domain {command} berhasil dihapus dari database.")

        conn.commit()
        conn.close()
    except Exception as e:
        await event.reply(f"Terjadi kesalahan saat menghapus IP atau domain dari database: {str(e)}")

async def ping_servers():
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT ip, domain FROM ips')
        server_ips = cursor.fetchall()
        conn.close()

        for server in server_ips:
            ip = server[0]
            domain = server[1]
            ping_results = []

            for _ in range(4):  # Ubah jumlah ping sesuai kebutuhan
                ping_time = ping(ip, unit="ms")
                if ping_time is not None:
                    ping_results.append(ping_time)
                else:
                    ping_results.append(float('inf'))

                await asyncio.sleep(1)  

            if float('inf') in ping_results:
                await send_notification(ip, domain, float('inf'), float('inf'))
            else:
                avg_latency = mean(ping_results)
                jitter = stdev(ping_results)

                if avg_latency > 100 or jitter > 10:
                    await send_notification(ip, domain, avg_latency, jitter)
                else:
                    if server_status.get(ip) == "down":
                        await send_notification(ip, domain, avg_latency, jitter)

    except Exception as e:
        print(f"Terjadi kesalahan: {str(e)}")

scheduler.add_job(ping_servers, 'interval', minutes=3)

bot.run_until_disconnected()

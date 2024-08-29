import sqlite3
import speedtest
import matplotlib.pyplot as plt
import os
from dotenv import dotenv_values
import datetime

config = dotenv_values("config.env")

async def speedtest_handler(event):
    try:
        message = await event.reply("Melakukan speedtest...")

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, ip, domain FROM ips')
        server_data = cursor.fetchall()
        conn.close()

        st = speedtest.Speedtest()

        for server in server_data:
            server_id = server[0]
            server_ip = server[1]
            server_domain = server[2]

            st.get_servers()
            st.get_best_server()

            st.download()
            st.upload()
            result = st.results

            download_speed = result.download / 10**6  # Mengonversi ke Mbps
            upload_speed = result.upload / 10**6  # Mengonversi ke Mbps
            ping_latency = result.ping

            # Membuat plot
            plt.figure(figsize=(8, 6))
            plt.subplot(2, 1, 1)
            plt.bar(['Download', 'Upload'], [download_speed, upload_speed], color=['#0077FF', '#FF8800'])
            plt.ylabel('Speed (Mbps)')
            plt.title(f'SPEEDTEST UNTUK SERVER: {server_domain} ({server_ip})')

            plt.subplot(2, 1, 2)
            plt.bar(['Ping Latency'], [ping_latency], color=['#FF4444'])
            plt.ylabel('Latency (ms)')
            plt.ylim(0, max(ping_latency, 100) + 20)

            # Menyimpan plot sebagai gambar
            filename = f"hasil_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.png"
            plt.savefig(filename, bbox_inches='tight')
            plt.close()

            caption = f"**__Hasil Speedtest Dari__**: {server_domain} ({server_ip})\n"
            caption += f"▰▱▰▱▰▱▰▱▰▱▰▱\n"
            caption += f"    ⬇️ **Download Speed**: {download_speed:.2f} Mbps\n"
            caption += f"    ⬆️ **Upload Speed**: {upload_speed:.2f} Mbps\n"
            caption += f"    ⏱️ **Ping Latency**: {ping_latency:.2f} ms\n"
            caption += f"▰▱▰▱▰▱▰▱▰▱▰▱\n\n"

            await event.reply(caption, file=filename)

            os.remove(filename)

        await message.delete()
        await event.edit(buttons=None)
    except Exception as e:
        await event.reply(f"Terjadi kesalahan saat menjalankan speedtest: {str(e)}")


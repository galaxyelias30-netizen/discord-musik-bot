import discord
from discord.ext import commands
import yt_dlp
import asyncio

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

ydl_opts = {'format': 'bestaudio/best', 'quiet': True, 'noplaylist': True}

queue = []
volume_level = 0.5

@bot.event
async def on_ready():
    print(f'✅ {bot.user} ist ONLINE! Fix Version')

radios = {
    "dasding": "https://liveradio.swr.de/d9zadj3/dasding/",
    "1live": "http://wdr-1live-live.icecast.wdr.de/wdr/1live/live/mp3/128/stream.mp3",
    "phonk": "https://stream.laut.fm/phonk",
    "lofi": "https://stream.laut.fm/lofi",
    "chill": "https://stream.laut.fm/chill",
    "rap": "https://stream.laut.fm/rap",
}

async def play_next(ctx):
    if not queue:
        return
    query = queue.pop(0)
    try:
        await ctx.send("⏳ Lade Song...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            if 'entries' in info:
                info = info['entries'][0]
            url = info['url']
            title = info.get('title', 'Unbekannter Song')
        
        vc = ctx.voice_client
        source = discord.FFmpegPCMAudio(url, before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', options='-vn')
        source = discord.PCMVolumeTransformer(source, volume=volume_level)
        vc.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
        await ctx.send(f'🎵 **Jetzt läuft:** {title}')
    except Exception as e:
        await ctx.send(f"❌ Abspielfehler: {e}")
        await play_next(ctx)

@bot.command()
async def play(ctx, *, search: str):
    if not ctx.author.voice:
        return await ctx.send("❌ Du musst in einem Voice-Channel sein!")

    vc = ctx.voice_client or await ctx.author.voice.channel.connect()

    await ctx.send(f"🔍 Suche: **{search}**")
    
    if "http" in search:
        queue.append(search)
    else:
        queue.append(f"ytsearch:{search}")

    if not vc.is_playing():
        await play_next(ctx)

@bot.command()
async def radio(ctx, station: str = None):
    if not ctx.author.voice:
        return await ctx.send("❌ Du musst in einem Voice-Channel sein!")
    
    vc = ctx.voice_client or await ctx.author.voice.channel.connect()

    if station is None:
        return await ctx.send(f"Verfügbare Sender: `{', '.join(radios.keys())}`")

    station = station.lower()
    if station not in radios:
        return await ctx.send("Sender nicht gefunden.")

    url = radios[station]
    await ctx.send(f"📻 **{station.upper()}** läuft jetzt!")

    try:
        source = discord.FFmpegPCMAudio(url, before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5')
        source = discord.PCMVolumeTransformer(source, volume=volume_level)
        vc.play(source)
    except Exception as e:
        await ctx.send(f"Fehler: {e}")

@bot.command()
async def volume(ctx, vol: int):
    global volume_level
    if 0 <= vol <= 200:
        volume_level = vol / 100
        if ctx.voice_client and ctx.voice_client.source:
            ctx.voice_client.source.volume = volume_level
        await ctx.send(f"🔊 Lautstärke auf **{vol}%**")
    else:
        await ctx.send("Nur 0-200!")

@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭️ Übersprungen.")

@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        queue.clear()
        await ctx.send("🛑 Gestoppt.")

import os
bot.run(os.getenv('DISCORD_TOKEN'))

import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

ydl_opts = {
    'format': 'bestaudio/best',
    'quiet': True,
    'noplaylist': True,
    'ignoreerrors': True,
    'no_warnings': True,
}

queue = []
volume_level = 0.5

@bot.event
async def on_ready():
    print(f'✅ {bot.user} ist ONLINE! Stabile Radio Version')

radios = {
    "dasding": "https://liveradio.swr.de/d9zadj3/dasding/",
    "1live": "http://wdr-1live-live.icecast.wdr.de/wdr/1live/live/mp3/128/stream.mp3",
    "phonk": "https://stream.laut.fm/phonk",
    "lofi": "https://stream.laut.fm/lofi",
    "deutschrap": "https://stream.laut.fm/deutschrap",
    "chill": "https://stream.laut.fm/chill",
    "rap": "https://stream.laut.fm/rap",
}

async def play_next(ctx):
    if not queue:
        return
    query = queue.pop(0)
    try:
        await ctx.send("⏳ Lade...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            if not info or 'url' not in info:
                return await ctx.send("❌ Konnte Audio nicht laden (YouTube Block). Nutze direkten Link.")
            url = info['url']
            title = info.get('title', 'Song')
        vc = ctx.voice_client
        source = discord.FFmpegPCMAudio(url, before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', options='-vn')
        source = discord.PCMVolumeTransformer(source, volume=volume_level)
        vc.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
        await ctx.send(f'🎵 **Jetzt läuft:** {title}')
    except Exception as e:
        await ctx.send(f"❌ Fehler: {str(e)[:100]}")
        await play_next(ctx)

@bot.command()
async def play(ctx, *, link: str):
    if not ctx.author.voice:
        return await ctx.send("❌ Du musst im Voice sein!")
    if ctx.voice_client is None:
        await ctx.author.voice.channel.connect()
    await ctx.send(f"🔍 Lade: **{link}**")
    queue.append(link)
    if not ctx.voice_client.is_playing():
        await play_next(ctx)

@bot.command()
async def radio(ctx, station: str = "dasding"):
    if not ctx.author.voice:
        return await ctx.send("❌ Du musst im Voice sein!")
    if ctx.voice_client is None:
        await ctx.author.voice.channel.connect()
    url = radios.get(station.lower(), radios["dasding"])
    await ctx.send(f"📻 **{station.upper()}** läuft!")
    try:
        source = discord.FFmpegPCMAudio(url, before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5')
        source = discord.PCMVolumeTransformer(source, volume=volume_level)
        ctx.voice_client.play(source)
    except Exception as e:
        await ctx.send(f"Fehler: {e}")

@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        queue.clear()
        await ctx.send("🛑 Gestoppt.")

bot.run(os.getenv('DISCORD_TOKEN'))

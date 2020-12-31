## adapted from https://www.freecodecamp.org/news/create-a-discord-bot-with-python/
import discord
import os
import redis
import datetime as dt
from discord.ext import commands
## adapted from https://github.com/Rapptz/discord.py/blob/master/examples/basic_voice.py
import asyncio

import youtube_dl

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

bot = commands.Bot(command_prefix='$')
## load these from env once Redis is hosted somewhere
r = redis.StrictRedis('127.0.0.1', 6379, charset="utf-8", decode_responses=True)
## there's probably a better way...
general = None

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)



@bot.command(name="walkup-set", help="LIGMA")
async def _walkup_set(ctx, *args):
    save = " ".join(args)
    r.set(ctx.author.id, save)


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game("HYYYYYPE MAAAAAAAN"))


def has_just_joined(before, after):
    return before.channel is None and after.channel is not None


def get_general(member):
    global general
    if general is None:
        general_channel = list(filter(lambda x: x.name == "general", bot.get_all_channels()))
        general = general_channel[0] if general_channel is not None else None


async def play_song(url, voice_channel):
    global general
    await general.send(f"Playing a song {url}")

    connxn = await voice_channel.connect()
    ## what if we're already connected?
    player = await YTDLSource.from_url(url, loop=connxn.loop, stream=True)
    ## play for 30 seconds/set some timeout...
    connxn.play(player, after=lambda e: print('Player error: %s' % e) if e else None)


@bot.event
async def on_voice_state_update(member, before, after):
    if has_just_joined(before, after):
        play = False
        old_time = r.get(f"{member.id}_timestamp")
        if old_time is None:
            play = True
        else:
            old_time = dt.datetime.strptime(old_time, "%Y-%m-%dT%H:%M:%S")
            now = dt.datetime.now()
            if now - old_time > dt.timedelta(minutes=30):
                play = True
        new_time = r.set(f"{member.id}_timestamp", dt.datetime.now().replace(microsecond=0).isoformat())
        song = r.get(member.id)
        get_general(member)
        global general
        if song is None:
            await general.send("Add a walkup song:\n$walkup-set https://www.youtube.com/watch?v=D7Y-nhksmcY")
        elif play:
            await play_song(song, after.channel)
    else:
        return

bot.run(os.getenv("WALKUP_TOKEN"))
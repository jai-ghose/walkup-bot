## adapted from https://www.freecodecamp.org/news/create-a-discord-bot-with-python/
import discord
import os
import redis
import datetime as dt
from discord.ext import commands

bot = commands.Bot(command_prefix='$')
r = redis.StrictRedis('127.0.0.1', 6379, charset="utf-8", decode_responses=True) ## host this bihhh
general = None

@bot.command(name="walkup-set", help="LIGMA")
async def _walkup_set(ctx, *args):
    save = " ".join(args)
    r.set(ctx.author.id, save)


@bot.event
async def on_ready():
    await bot.change_presence(activity = discord.Game("Getting y'all bitches HYYYYYPE"))


def has_just_joined(before, after):
    return before.channel is None and after.channel is not None

def get_general(member):
    global general
    if general is None:
        general_channel = list(filter(lambda x: x.name == "general", bot.get_all_channels()))
        general = general_channel[0] if general_channel is not None else None

@bot.event
async def on_voice_state_update(member, before, after):
    if has_just_joined(before, after):
        play = False
        old_time = r.get(f"{member.id}_timestamp")
        if old_time is None:
            play = True
        else:
            old_time = dt.datetime.strptime(old_time, "%Y-%m-%dT%H:%M:%S")
            if new_time - old_time > dt.timedelta(minutes=30):
                play = True
        new_time = r.set(f"{member.id}_ts", dt.datetime.now().replace(microsecond=0).isoformat())
        song = r.get(member.id)
        get_general(member)
        global general
        if song is None:
            await general.send("Add a walkup song:\n$walkup-set Mix IT - Juicy J")
        elif play:
            ## Rhythom won't listen to my bot commands, so I'll figure this out later...
            ## TODO: implement a lib like this: https://github.com/Rapptz/discord.py/blob/master/examples/basic_voice.py
            await general.send(f"+play {song}")
    else:
        return


bot.run(os.getenv("WALKUP_TOKEN"))


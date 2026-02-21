import discord
import os
from dotenv import load_dotenv
import logging
from discord.ext import commands
import csv
from datetime import timezone
import time
import asyncio

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
client = commands.Bot(command_prefix="!", intents=intents)


TOKEN = os.getenv("TOKEN")
if TOKEN is None:
    raise RuntimeError("TOKEN is not set")


@client.event
async def on_ready():
    print(f"{client.user} has connected to Discord!")


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    print("saw message:", message.content)
    await client.process_commands(message)

    if message.content.startswith("hello"):
        await message.channel.send("Hello!")


@client.command()
async def ping(ctx):
    await ctx.send("Pong!")

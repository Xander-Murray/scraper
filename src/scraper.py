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


@client.command(name="csv")
@commands.guild_only()
async def export_csv(ctx: commands.Context):
    guild = ctx.guild
    assert guild is not None

    me = guild.me
    perms = ctx.channel.permissions_for(me)
    if not (perms.view_channel and perms.read_message_history):
        await ctx.send("I need View Channel + Read Message History in this channel.")
        return

    status = await ctx.send("Starting export…")
    filename = f"message_log_{ctx.channel.id}.csv"

    count = 0
    last_update = time.time()

    async with ctx.typing():
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "channel_name",
                    "message_id",
                    "author_username",
                    "author_display_name",
                    "created_at_iso",
                    "content",
                ]
            )

            async for msg in ctx.channel.history(limit=None, oldest_first=True):
                created_iso = msg.created_at.replace(tzinfo=timezone.utc).isoformat()

                writer.writerow(
                    [
                        str(ctx.channel),
                        str(msg.id),
                        str(msg.author),
                        getattr(msg.author, "display_name", ""),
                        created_iso,
                        msg.content,
                    ]
                )

                count += 1

                if count % 1000 == 0:
                    await asyncio.sleep(0.5)

                if time.time() - last_update > 7:
                    await status.edit(content=f"Exporting… {count} messages")
                    last_update = time.time()

    await status.edit(content=f"Done! Exported {count} messages. Uploading CSV…")
    await ctx.send(file=discord.File(filename))


client.run(TOKEN, log_handler=handler, log_level=logging.DEBUG)

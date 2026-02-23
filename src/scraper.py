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

HELP_TEXT = """
    **!csv** - Export messages in the current channel to a CSV file.

    **Flags:**
    - `--not_bot`: Exclude bot messages from the export. (must pass bool value after the flag, e.g. `--not_bot true`)
    - `--no_attachments`: Exclude attatchment URLs from the export.(must pass bool value after the flag, e.g. `--no_attachments true`)
    - `--limit <number>`: Limit the number of messages to export (default is all messages).
    """


TOKEN = os.getenv("TOKEN")
if TOKEN is None:
    raise RuntimeError("TOKEN is not set")


@client.event
async def on_ready():
    print(f"{client.user} has connected to Discord!")


@client.command(name="helpme")
async def help_command(ctx: commands.Context):
    await ctx.send(HELP_TEXT)


# Create flags to better support user options
class Flags(commands.FlagConverter, delimiter=" ", prefix="--"):
    not_bot: bool = commands.flag(default=False, description="Exclude bot messages")
    no_attachments: bool = commands.flag(
        default=False, description="Exclude attachment URLs"
    )
    limit: int | None = commands.flag(
        default=None,
        description="Limit the number of messages to export (default is all messages)",
    )


CSV_HEADER = [
    "channel_name",
    "message_id",
    "author_username",
    "author_display_name",
    "created_at_iso",
    "content",
    "is_bot",
    "attachments",
]


def message_to_row(channel, msg, *, flags):
    created_iso = msg.created_at.replace(tzinfo=timezone.utc).isoformat()
    attachments = (
        "" if flags.no_attachments else ";".join(a.url for a in msg.attachments)
    )

    return [
        str(channel),
        str(msg.id),
        str(msg.author),
        getattr(msg.author, "display_name", ""),
        created_iso,
        msg.content,
        str(msg.author.bot),
        attachments,
    ]


def should_skip(msg: discord.Message, *, flags: Flags) -> bool:
    if not msg.content:  # skip messages that have attachments only mostly
        return True
    if flags.not_bot and msg.author.bot:
        return True
    return False


async def export_channel_to_csv(
    channel: discord.abc.Messageable,
    filename: str,
    *,
    flags: Flags,
    progress_cb=None,
    throttle_every: int = 1000,
    throttle_sleep: float = 0.5,
):
    count = 0
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADER)

        async for msg in channel.history(limit=flags.limit, oldest_first=True):
            if should_skip(msg, flags=flags):
                continue

            writer.writerow(message_to_row(channel, msg, flags=flags))
            count += 1

            if throttle_every and count % throttle_every == 0:
                await asyncio.sleep(throttle_sleep)

            if progress_cb:
                await progress_cb(count)

    return count


@client.command(name="csv")
@commands.guild_only()
async def csv_export(ctx: commands.Context, *, flags: Flags = Flags()):
    # permissions
    guild = ctx.guild
    assert guild is not None
    me = guild.me
    perms = ctx.channel.permissions_for(me)
    if not (perms.view_channel and perms.read_message_history):
        await ctx.send("I need View Channel + Read Message History in this channel.")
        return

    folder_path = "./"
    csv_count = sum(
        1
        for file in os.scandir(folder_path)
        if file.is_file() and file.name.endswith(".csv")
    )

    filename = f"message_log_{ctx.channel.id}.csv"
    if os.path.exists(f"./{filename}"):
        csv_count += 1
        filename = f"message_log_{ctx.channel.id}_{csv_count}.csv"

    status = await ctx.send("Starting export…")
    last_update = 0.0

    async def progress(count: int):
        nonlocal last_update
        now = time.time()
        if now - last_update > 7:
            await status.edit(content=f"Exporting… {count} messages")
            last_update = now

    async with ctx.typing():
        count = await export_channel_to_csv(
            ctx.channel,
            filename,
            flags=flags,
            progress_cb=progress,
            throttle_every=1000,
            throttle_sleep=0.5,
        )

    await status.edit(content=f"Done! Exported {count} messages. Uploading CSV…")
    await ctx.send(file=discord.File(filename))


client.run(TOKEN, log_handler=handler, log_level=logging.DEBUG)

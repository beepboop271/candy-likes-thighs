import os
from typing import Dict, List

import discord
import dotenv

from Game import Game

dotenv.load_dotenv()

client = discord.Client()

games: Dict[int, Game] = {}


@client.event
async def on_ready():
    print("logged in")


@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return

    if len(message.content) == 0:
        return

    maybe_game = games.get(message.channel.id)

    if message.content[0] == "$":
        args: List[str] = message.content[1:].split()
        if args[0] == "start":
            if maybe_game is not None:
                await message.channel.send("A game is already taking place in this channel")
                return

            if len(args) == 2:
                try:
                    new_game = Game(message.channel.id, int(args[1]))
                except ValueError:
                    await message.channel.send(f"Unknown argument: {args[1]}")
                    return
            elif len(args) == 3:
                try:
                    new_game = Game(message.channel.id, int(args[1]), int(args[2]))
                except ValueError:
                    await message.channel.send(f"At least one unknown argument: {args[1]}, {args[2]}")
                    return
            elif len(args) == 4:
                try:
                    new_game = Game(message.channel.id, int(args[1]), int(args[2]), int(args[3]))
                except ValueError:
                    await message.channel.send(f"At least one unknown argument: {args[1]}, {args[2]}, {args[3]}")
                    return
            else:
                new_game = Game(message.channel.id)

            games[message.channel.id] = new_game
            buf = new_game.start_round()
            buf.seek(0)
            await message.channel.send(
                f"Round 1: {new_game.current_radius*2} x {new_game.current_radius*2}",
                file=discord.File(buf, "canned_thighs.png"),
            )
            buf.close()
        elif args[0] == "expand":
            if maybe_game is None:
                await message.channel.send("No game is taking place in this channel")
                return

            buf = maybe_game.get_help()
            buf.seek(0)
            await message.channel.send(
                f"{maybe_game.current_radius*2} x {maybe_game.current_radius*2}:",
                file=discord.File(buf, "canned_thighs.png"),
            )
            buf.close()
    elif maybe_game is not None:
        if maybe_game.verify_answer(message.content):
            lines = message.content.split("\n")
            quote = "\n".join((f"> {line}" for line in lines))
            await message.channel.send(f"{quote}\n<@{message.author.id}> got the answer")

            maybe_buf = maybe_game.end_round(message.author.id)
            if maybe_buf is None:
                await message.channel.send("Game over")
                del games[message.channel.id]
            else:
                maybe_buf.seek(0)
                await message.channel.send(
                    f"Round {maybe_game.round}: {maybe_game.current_radius*2} x {maybe_game.current_radius*2}",
                    file=discord.File(maybe_buf, "canned_thighs.png"),
                )
                maybe_buf.close()


client.run(os.getenv("DISCORD_BOT_TOKEN"))

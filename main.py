import asyncio
import os
from typing import BinaryIO, Dict, List

import discord
import dotenv
dotenv.load_dotenv()

from cannedthighs.Game import Game

client = discord.Client()

games: Dict[int, Game] = {}


async def send_message_and_image(
    channel: discord.channel.TextChannel,
    buf: BinaryIO,
    content: str,
) -> None:
    buf.seek(0)
    await channel.send(content, file=discord.File(buf, "canned_thighs.png"))
    buf.close()


async def end_game(
    channel: discord.channel.TextChannel,
    game: Game,
) -> None:
    # game.scores: ((player_id_1, score_1), (player_id_2, score_2), ...)
    # sort from highest score to lowest
    # enumerate with first place, second place, ...
    # ((1, (player_id_1, score_1)), (2, (player_id_2, score_2)), ...)
    scores = enumerate(sorted(game.scores, key=lambda x: x[1], reverse=True), 1)
    score_str = "\n".join([
        f"#{place} <@{player}>: {score} points" for place, (player, score) in scores
    ])

    await channel.send(f"Game Over:\n{score_str}")
    del games[channel.id]


@client.event
async def on_ready():
    print("logged in")


@client.event
async def on_message(msg: discord.Message):
    if msg.author == client.user:
        return

    if len(msg.content) == 0:
        return

    maybe_game = games.get(msg.channel.id)

    if msg.content[0] == "&" and len(msg.content) > 1:
        args: List[str] = msg.content[1:].split()
        if args[0] == "start" or args[0] == "s":
            if maybe_game is not None:
                await msg.channel.send("A game is already taking place in this channel")
                return

            if len(args) == 2:
                try:
                    new_game = Game(int(args[1]))
                except ValueError:
                    await msg.channel.send(f"Unknown argument: {args[1]}")
                    return
            elif len(args) == 3:
                try:
                    new_game = Game(int(args[1]), float(args[2]))
                except ValueError:
                    await msg.channel.send(f"At least one unknown argument: {args[1]}, {args[2]}")
                    return
            elif len(args) == 4:
                try:
                    new_game = Game(int(args[1]), float(args[2]), float(args[3]))
                except ValueError:
                    await msg.channel.send(f"At least one unknown argument: {args[1]}, {args[2]}, {args[3]}")
                    return
            else:
                new_game = Game()

            games[msg.channel.id] = new_game
            await send_message_and_image(
                msg.channel,
                new_game.start_round(),
                "Round 1:",
            )
        elif args[0] == "reset" or args[0] == "r":
            if maybe_game is None:
                await msg.channel.send("No game is taking place in this channel")
                return

            await send_message_and_image(
                msg.channel,
                maybe_game.reset_round(),
                f"Round {maybe_game.current_round}:",
            )
        elif args[0] == "expand" or args[0] == "e":
            if maybe_game is None:
                await msg.channel.send("No game is taking place in this channel")
                return

            if maybe_game.expand_lock.locked():
                return

            async with maybe_game.expand_lock:
                await send_message_and_image(
                    msg.channel,
                    maybe_game.get_help(),
                    "",
                )
                # maintain the lock for 1 second
                await asyncio.sleep(1)
        elif args[0] == "quit" or args[0] == "q":
            if maybe_game is None:
                await msg.channel.send("No game is taking place in this channel")
                return

            await end_game(msg.channel, maybe_game)
    elif maybe_game is not None:
        if maybe_game.verify_answer(msg.content):
            maybe_buf = maybe_game.end_round(msg.author.id)

            quote = "\n".join((f"> {line}" for line in msg.content.split("\n")))
            await msg.channel.send(f"{quote}\n<@{msg.author.id}> got the answer")
            if maybe_buf is None:
                await end_game(msg.channel, maybe_game)
            else:
                await send_message_and_image(
                    msg.channel,
                    maybe_buf,
                    f"Round {maybe_game.current_round}:",
                )


client.run(os.getenv("DISCORD_BOT_TOKEN"))

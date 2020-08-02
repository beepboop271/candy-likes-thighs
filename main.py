import os
from typing import BinaryIO, Dict, List

import discord
import dotenv

from cannedthighs.Game import Game

dotenv.load_dotenv()

client = discord.Client()

games: Dict[int, Game] = {}


async def send_message_and_image(
    channel: discord.channel.TextChannel,
    content: str,
    buf: BinaryIO
) -> None:
    buf.seek(0)
    await channel.send(content, file=discord.File(buf, "canned_thighs.png"))
    buf.close()


async def end_game(
    channel: discord.channel.TextChannel,
    game: Game
) -> None:
    # game.scores: ((player_id_1, score_1), (player_id_2, score_2), ...)
    # sort from highest score to lowest
    # enumerate with first place, second place, ...
    # ((1, (player_id_1, score_1)), (2, (player_id_2, score_2)), ...)
    score_tuples = enumerate(sorted(game.scores, key=lambda x: x[1], reverse=True), 1)
    scores = "\n".join([
        f"#{place} <@{player}>: {score} points" for place, (player, score) in score_tuples
    ])

    await channel.send(f"Game Over:\n{scores}")
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

    if msg.content[0] == "$":
        args: List[str] = msg.content[1:].split()
        if args[0] == "start":
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
                    new_game = Game(int(args[1]), int(args[2]))
                except ValueError:
                    await msg.channel.send(f"At least one unknown argument: {args[1]}, {args[2]}")
                    return
            elif len(args) == 4:
                try:
                    new_game = Game(int(args[1]), int(args[2]), int(args[3]))
                except ValueError:
                    await msg.channel.send(f"At least one unknown argument: {args[1]}, {args[2]}, {args[3]}")
                    return
            else:
                new_game = Game()

            games[msg.channel.id] = new_game
            await send_message_and_image(
                msg.channel,
                f"Round 1: {new_game.current_radius*2} x {new_game.current_radius*2}",
                new_game.start_round(),
            )
        elif args[0] == "reset":
            if maybe_game is None:
                await msg.channel.send("No game is taking place in this channel")
                return
            
            await send_message_and_image(
                msg.channel,
                f"Round {maybe_game.current_round}: {maybe_game.current_radius*2} x {maybe_game.current_radius*2}",
                maybe_game.reset_round()
            )
        elif args[0] == "expand":
            if maybe_game is None:
                await msg.channel.send("No game is taking place in this channel")
                return

            await send_message_and_image(
                msg.channel,
                f"{maybe_game.current_radius*2} x {maybe_game.current_radius*2}:",
                maybe_game.get_help(),
            )
        elif args[0] == "quit":
            if maybe_game is None:
                await msg.channel.send("No game is taking place in this channel")
                return

            await end_game(msg.channel, maybe_game)
    elif maybe_game is not None:
        if maybe_game.verify_answer(msg.content):
            quote = "\n".join((f"> {line}" for line in msg.content.split("\n")))
            await msg.channel.send(f"{quote}\n<@{msg.author.id}> got the answer")

            maybe_buf = maybe_game.end_round(msg.author.id)
            if maybe_buf is None:
                await end_game(msg.channel, maybe_game)
            else:
                await send_message_and_image(
                    msg.channel,
                    f"Round {maybe_game.current_round}: {maybe_game.current_radius*2} x {maybe_game.current_radius*2}",
                    maybe_buf,
                )


client.run(os.getenv("DISCORD_BOT_TOKEN"))

import asyncio
from typing import BinaryIO, Dict, List

import discord

import cannedthighs
from cannedthighs.Game import Game


client = discord.Client()

games: Dict[int, Game] = {}


async def send_message_and_image(
    channel: discord.channel.TextChannel,
    buf: BinaryIO,
    content: str,
) -> None:
    await channel.send(content, file=discord.File(buf, cannedthighs.FILE_NAME))
    buf.close()


async def end_game(
    channel: discord.channel.TextChannel,
    game: Game,
) -> None:
    await channel.send(f"Game Over:\n{str(game)}")
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
                    await msg.channel.send(
                        f"At least one unknown argument: {args[1]}, {args[2]}"
                    )
                    return
            elif len(args) == 4:
                try:
                    new_game = Game(int(args[1]), float(args[2]), float(args[3]))
                except ValueError:
                    await msg.channel.send(
                        f"At least one unknown argument: {args[1]}, {args[2]}, {args[3]}"
                    )
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
        elif args[0] == "view" or args[0] == "v":
            if maybe_game is None:
                await msg.channel.send("No game is taking place in this channel")
                return

            await send_message_and_image(
                msg.channel,
                maybe_game.view_image(),
                "",
            )
        elif args[0] == "score":
            if maybe_game is None:
                await msg.channel.send("No game is taking place in this channel")
                return

            await msg.channel.send(str(maybe_game))
    elif maybe_game is not None:
        if maybe_game.verify_answer(msg.content):
            maybe_buf = maybe_game.end_round(msg.author.id)

            first_line = msg.content.split("\n", 1)[0]
            await msg.channel.send(f"> {first_line}\n<@{msg.author.id}> got the answer")
            if maybe_buf is None:
                await end_game(msg.channel, maybe_game)
            else:
                await send_message_and_image(
                    msg.channel,
                    maybe_buf,
                    f"Round {maybe_game.current_round}:",
                )


client.run(cannedthighs.DISCORD_BOT_TOKEN)

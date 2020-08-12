import asyncio
from typing import Callable, Dict, FrozenSet, List

import discord

import cannedthighs
from cannedthighs.Game import Game


client = discord.Client()

games: Dict[int, Game] = {}

commands: FrozenSet[str] = frozenset((
    "start", "s",
    "expand", "e",
    "view", "v",
    "score",
    "quit", "q",
))


async def send_message_and_image(
    channel: discord.channel.TextChannel,
    image_file: discord.File,
    content: str,
) -> None:
    # await channel.send(content, file=discord.File(buf, cannedthighs.FILE_NAME))
    await channel.send(content, file=image_file)
    image_file.close()
    image_file.fp.close()


async def maybe_render(
    channel: discord.channel.TextChannel,
    render_lock: asyncio.Lock,
    renderer: Callable[[], discord.File],
) -> None:
    if render_lock.locked():
        return

    async with render_lock:
        await send_message_and_image(
            channel,
            renderer(),
            "",
        )
        # maintain the lock for 1 second
        # so nobody else can spam render calls
        await asyncio.sleep(1)


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
        args: List[str] = msg.content[1:].lower().split()

        # leave immediately on invalid commands
        if args[0] not in commands:
            await msg.channel.send("Unknown command")
            return

        # process start command first
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
                if args[2] not in cannedthighs.FILE_FORMATS:
                    await msg.channel.send(f"Unknown argument: {args[2]}")
                    return
                try:
                    new_game = Game(int(args[1]), image_mode=args[2])
                except ValueError:
                    await msg.channel.send(f"Unknown argument: {args[1]}")
                    return
            else:
                new_game = Game()

            games[msg.channel.id] = new_game
            await send_message_and_image(
                msg.channel,
                new_game.start_round(),
                "Round 1:",
            )
            return

        # by now, args[0] must be expand, view, score, or quit:
        # all of which require a valid game
        if maybe_game is None:
            await msg.channel.send("No game is taking place in this channel")
            return

        if args[0] == "expand" or args[0] == "e":
            await maybe_render(
                msg.channel,
                maybe_game.render_lock,
                maybe_game.get_help,
            )
        elif args[0] == "view" or args[0] == "v":
            await maybe_render(
                msg.channel,
                maybe_game.render_lock,
                maybe_game.view_image,
            )
        elif args[0] == "score":
            await msg.channel.send(str(maybe_game))
        elif args[0] == "quit" or args[0] == "q":
            await end_game(msg.channel, maybe_game)
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

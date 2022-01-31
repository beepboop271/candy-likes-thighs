import crypto from "crypto";
import fs from "fs";
import ioredis from "ioredis";
import fetch, { Response } from "node-fetch";
import url from "url";

import { redis } from "./constants";
import {
  ChatReceiveMessage,
  CorrectGuessMessage,
  GameData,
  GameSettings,
  NewImageMessage,
  RawChatReceiveMessage,
  RoundEndMessage,
  RoundStartMessage,
} from "./interfaces";
import { sleep, toNumberValues } from "./utils";

const buildSetMap = (jsonData: GameData): Map<string, Set<string>> => {
  const map: Map<string, Set<string>> = new Map();
  for (const [charId, data] of Object.entries(jsonData)) {
    map.set(charId, new Set([data.en_name, ...data.aliases]));
  }
  return map;
};

const charIdFromUrl = (link: url.URL): string => {
  const first = link.pathname.substring(link.pathname.lastIndexOf("/")+1);
  return first.substring(0, first.lastIndexOf("_"));
};

const gameData = buildSetMap(JSON.parse(
  fs.readFileSync("gamedata/ak_data.json", "utf-8"),
) as GameData);

export class Game {
  private readonly name: string;
  private readonly gameKey: string;
  private readonly settings: GameSettings;
  private readonly instance: number;
  private readonly sub: ioredis.Redis;
  private readonly ready: Promise<void>;

  public constructor(name: string, settings: GameSettings, instance: number) {
    this.name = name;
    this.gameKey = `game:${name}`;
    this.settings = settings;
    this.instance = instance;
    this.sub = new ioredis({ lazyConnect: true });
    this.ready = this.sub.connect();
  }

  private static getScore(msElapsed: number): number {
    // todo: not hardcode?
    return Math.floor((Math.exp(-msElapsed/20000 + 6) + 100)/10)*10;
  }

  public async play(): Promise<void> {
    await this.ready;
    await this.sub.subscribe(`${this.name}:raw`);

    let round = Number(await redis.hget(this.gameKey, "currentRound") ?? 0);
    if (round > this.settings.rounds) {
      await redis.hset(this.gameKey, "currentRound", 0);
      round = 0;
    }

    for (; round < this.settings.rounds; ++round) {
      await this.playRound(round);
    }
  }

  private async playRound(round: number): Promise<void> {
    await this.consistency();
    const startBroadcast: RoundStartMessage = {
      message: "round-start",
      data: {
        number: round,
      },
    };
    await redis.pipeline()
      .expire(`${this.gameKey}:alive`, this.settings.interval*2)
      .publish(this.name, JSON.stringify(startBroadcast))
      .exec();

    const newRes = await fetch(
      // todo: use difficulty, charset, and move origin to config
      "http://localhost:5000/new",
      { redirect: "manual" },
    );
    const link = newRes.headers.get("Location");
    if (link === null) {
      throw new Error("get image /new had no Location header");
    }
    const firstUrl = new url.URL(link);
    const charId = charIdFromUrl(firstUrl);
    let nextUrl: string | undefined = firstUrl.toString();

    // players who have already correctly guessed this round.
    // don't need to persist because only one web instance is
    // necessary to do the round management (just make some
    // api and database calls). if the game instance fails
    // then there is no point remembering who had guessed that
    // round since the round would need to be restarted
    // anyways
    const guessed: Set<string> = new Set();

    await redis.set(`${this.gameKey}:answer`, charId);
    const roundStartTime = Date.now();
    this.sub.on("message", async (_channel: string, msgStr: string): Promise<void> => {
      const msg = JSON.parse(msgStr) as RawChatReceiveMessage;
      const didGuess = guessed.has(msg.data.author);
      if (didGuess || !(gameData.get(charId)?.has(msg.data.text.trim()) ?? false)) {
        await redis.publish(
          this.name,
          JSON.stringify({
            message: "chat-receive",
            data: {
              ...msg.data,
              guessed: didGuess,
            },
          } as ChatReceiveMessage),
        );
      } else {
        guessed.add(msg.data.author);
        await redis.pipeline()
          .hincrby(
            `${this.gameKey}:scores`,
            msg.data.author,
            Game.getScore(Date.now() - roundStartTime),
            // can get the new score if needed from here
          )
          .publish(
            this.name,
            JSON.stringify({
              message: "correct-guess",
              data: {
                player: msg.data.author,
              },
            } as CorrectGuessMessage),
          )
          .exec();
      }
    });

    while (nextUrl !== undefined) {
      const startTime = Date.now();

      const code = crypto.randomUUID();
      const broadcast: NewImageMessage = {
        message: "new-image",
        data: {
          code,
        },
      };
      await redis.pipeline()
        .expire(`${this.gameKey}:alive`, this.settings.interval*2)
        .set(`images:${code}`, nextUrl, "EX", this.settings.interval*2)
        .publish(this.name, JSON.stringify(broadcast))
        .exec();

      // interesting ts can't infer this (because of the loop?)
      const res: Response = await fetch(nextUrl);

      const next = res.headers.get("Link")
                     ?.match(/<([^>]+)>; rel="next"/)
                     ?.[1];
      // if next is undefined, res contains the last image of
      // the round (end round after this call's timer is over)
      nextUrl = next === undefined ? undefined : firstUrl.origin + next;

      const delay = startTime + this.settings.interval*1000 - Date.now();
      if (delay < 0) {
        throw new Error("behind!");
      }
      await sleep(delay);
      await this.consistency();
    }

    this.sub.removeAllListeners("message");
    await redis.unlink(`${this.gameKey}:answer`);

    const endBroadcast: RoundEndMessage = {
      message: "round-end",
      data: toNumberValues(await redis.hgetall(`${this.gameKey}:scores`)),
    };
    await redis.pipeline()
      .expire(`${this.gameKey}:alive`, this.settings.interval*2)
      .publish(this.name, JSON.stringify(endBroadcast))
      .exec();
  }

  private async consistency(): Promise<void> | never {
    if (this.instance !== Number(await redis.get(`${this.gameKey}:alive`))) {
      throw new Error("attempted to play expired round or not started by self");
    }
  }
}

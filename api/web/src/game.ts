import crypto from "crypto";
import fetch, { Response } from "node-fetch";
import url from "url";

import { redis } from "./constants";
import { GameSettings, NewImageMessage, RoundEndMessage, RoundStartMessage } from "./interfaces";
import { sleep, toNumberValues } from "./utils";

export class Game {
  public readonly name: string;
  public readonly gameKey: string;
  public readonly settings: GameSettings;
  public readonly instance: number;

  public constructor(name: string, settings: GameSettings, instance: number) {
    this.name = name;
    this.gameKey = `game:${name}`;
    this.settings = settings;
    this.instance = instance;
  }

  public async play(): Promise<void> {
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
    const charId = firstUrl.pathname.substring(firstUrl.pathname.lastIndexOf("/")+1);
    let nextUrl: string | undefined = firstUrl.toString();

    await redis.set(`${this.gameKey}:answer`, charId);

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

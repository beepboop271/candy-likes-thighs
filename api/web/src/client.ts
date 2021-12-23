import { EventEmitter } from "events";
import ioredis from "ioredis";
import websocket from "ws";

import { debug, redis } from "./constants";
import { ClientMessage, ServerMessage, Session } from "./interfaces";

export class Client extends EventEmitter {
  public readonly ws: websocket;
  public readonly sub: ioredis.Redis;
  public readonly gameName: string;
  public readonly playerName: string;

  public constructor(ws: websocket, req: Session) {
    super();
    this.ws = ws;
    this.sub = new ioredis();
    this.sub.on("ready", this.enterGame.bind(this));

    this.gameName = req.session.gameName;
    this.playerName = req.session.playerName;

    this.sub.on("message", (_channel: string, msg: string): void => {
      debug(`${this.playerName} received pubsub: ${msg}`);
      this.message(msg);
    });

    this.ws.on("close", async (_code, _reason): Promise<void> => {
      debug(`${this.playerName} closed connection`);
      // don't destroy their data, in case they lost connection
      // and want to join back to the game
      await this.broadcast({
        message: "player-disappear",
        data: {
          player: this.playerName,
        },
      });

      // only re-assign the host
      // maybe find a way to cache host? might be called a lot
      // if (this.playerName === await redis.hget(`game:${this.gameName}`, "host")) {
      //
      // }

      await this.terminate();
    });

    this.ws.on("message", async (data): Promise<void> => {
      debug(`${this.playerName} received browser: ${data.toString()}`);
      const msg = JSON.parse(data.toString()) as ClientMessage;
      debug(msg.message);
      switch (msg.message) {
        case "chat-send":
          await this.broadcast({
            message: "chat-receive",
            data: {
              author: this.playerName,
              text: msg.data.text,
            },
          });
          break;
        default:
          // unknown type
          await this.close(1008);
      }
    });
  }

  public async close(code: number): Promise<void> {
    this.ws.close(code);
    await this.sub.quit();
    this.emit("end");
  }
  public async terminate(): Promise<void> {
    this.ws.terminate();
    await this.sub.quit();
    this.emit("end");
  }

  private async enterGame(): Promise<void> {
    // subscribe before getting list of existing players.
    // you can't make a transaction consisting of smembers
    // followed immediately by subscribe (at least i don't
    // think you can), which means it's possible for a sadd/pub
    // to happen between smembers and subscribe. by subbing
    // first, we choose to deal with possible duplicates
    // instead of possible lost information.
    await this.sub.subscribe(this.gameName);

    const scoreKey = `game:${this.gameName}:scores`;
    await redis
      .pipeline()
      .hgetall(scoreKey, (err, scores): void => {
        if (err !== null) {
          throw err;
        }
        this.message({
          message: "init-player-list",
          data: Object.fromEntries(Object.entries(scores).map(
            ([player, score]): [string, number] => [player, Number(score)],
          )),
        });
      })
      // set their score to 0 if joining for first time
      // retain their last score if a player lost connection
      .hsetnx(scoreKey, this.playerName, 0, async (err, res): Promise<void> => {
        if (err !== null) {
          throw err;
        }
        const score =
          res === 1
          ? 0  // the key did not exit, so the score must have been set to 0
          : Number(await redis.hget(scoreKey, this.playerName));  // the key exists
        await this.broadcast({
          message: "player-enter",
          data: {
            player: this.playerName,
            score,
          },
        });
      })
      .exec();
  }

  private message(message: string | ServerMessage): void {
    if (typeof message === "string") {
      this.ws.send(message);
    } else {
      this.ws.send(JSON.stringify(message));
    }
  }
  private async broadcast(message: string | ServerMessage): Promise<void> {
    if (typeof message === "string") {
      await redis.publish(this.gameName, message);
    } else {
      await redis.publish(this.gameName, JSON.stringify(message));
    }
  }
}

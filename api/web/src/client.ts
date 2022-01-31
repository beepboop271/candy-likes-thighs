import { EventEmitter } from "events";
import ioredis from "ioredis";
import websocket from "ws";

import { debug, redis } from "./constants";
import { ClientMessage, RawChatReceiveMessage, ServerMessage, Session } from "./interfaces";
import { toNumberValues } from "./utils";

export class Client extends EventEmitter {
  public readonly ws: websocket;
  public readonly sub: ioredis.Redis;
  public readonly gameName: string;
  public readonly playerName: string;
  private guessed: boolean;

  public constructor(ws: websocket, req: Session) {
    super();
    this.ws = ws;
    this.sub = new ioredis();
    this.sub.on("ready", this.enterGame.bind(this));

    this.gameName = req.session.gameName;
    this.playerName = req.session.playerName;
    this.guessed = false;

    this.sub.on("message", (_channel: string, msg: string): void => {
      debug(`${this.playerName} received pubsub: ${msg}`);

      const msgObj = JSON.parse(msg) as ServerMessage;
      switch (msgObj.message) {
        case "new-host":
          if (msgObj.data.player === this.playerName) {
            this.message({
              message: "you-are-host",
              // looks like ts needs this to infer type.
              // doesn't matter, since JSON.stringify will
              // get rid of it
              data: undefined,
            });
          }
          break;
        case "correct-guess":
          if (msgObj.data.player === this.playerName) {
            this.guessed = true;
          }
          this.message(msg);
          break;
        case "round-end":
          this.guessed = false;
          this.message(msg);
          break;
        case "chat-receive":
          if (msgObj.data.guessed && !this.guessed) {
            // if the sender guessed but this player hasn't,
            // don't deliver the message
            break;
          }
          this.message(msg);
          break;
        default:
          this.message(msg);
      }
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

      await redis.zadd(`game:${this.gameName}:players`, "+inf", this.playerName);

      // only re-assign the host
      // maybe find a way to cache host? might be called a lot
      const hostName = await redis.hget(`game:${this.gameName}`, "host");
      if (this.playerName === hostName) {
        // maybe make a redis script so that nobody will join
        // between zrange and hdel and be host-less
        const newHost = await redis.zrangebyscore(
          `game:${this.gameName}:players`,
          "-inf", Date.now(),
          "WITHSCORES",
          "LIMIT", 0, 1,
        );
        if (newHost.length > 0) {
          await redis.hset(`game:${this.gameName}`, "host", newHost[0]);
          await this.broadcast({
            message: "new-host",
            data: {
              player: newHost[0],
            },
          });
        } else {
          await redis.hdel(`game:${this.gameName}`, "host");
          console.log("game dead");
        }
      }

      await this.terminate();
    });

    this.ws.on("message", async (data): Promise<void> => {
      debug(`${this.playerName} received browser: ${data.toString()}`);
      const msg = JSON.parse(data.toString()) as ClientMessage;
      debug(msg.message);
      switch (msg.message) {
        case "chat-send":
          await redis.publish(
            `${this.gameName}:raw`,
            JSON.stringify({
              message: "raw-chat-receive",
              data: {
                author: this.playerName,
                text: msg.data.text,
              },
            } as RawChatReceiveMessage),
          );
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
          data: toNumberValues(scores),
        });
      })
      // joining player is host when they are first to join a
      // new lobby or join back after everyone left
      .hsetnx(`game:${this.gameName}`, "host", this.playerName, async (err, res): Promise<void> => {
        if (err !== null) {
          throw err;
        }
        if (res === 1) {
          // host did not exist, must be what we set
          this.message({
            message: "you-are-host",
            data: undefined,
          });
        } else {
          // host must exist
          const host = (await redis.hget(`game:${this.gameName}`, "host"))!;
          this.message({
            message: "new-host",
            data: {
              player: host,
            },
          });
        }
      })
      // @ts-expect-error - types for ioredis suck
      .zadd(`game:${this.gameName}:players`, Date.now(), this.playerName, async (err, res): Promise<void> => {
        if (err !== null) {
          throw err;
        }
        const score =
          res === 1
          ? 0  // player did not exist, score must be 0
          : Number(await redis.hget(scoreKey, this.playerName));
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

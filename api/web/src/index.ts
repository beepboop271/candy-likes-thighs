import connectRedis from "connect-redis";
import express from "express";
import expressSession from "express-session";
import http from "http";
import type net from "net";
import websocket from "ws";

import { Client } from "./client";
import { debug, origin, port, redis, sessionSecret } from "./constants";
import {
  EnterGameRequest,
  MaybeSession,
  Session,
} from "./interfaces";
import * as utils from "./utils";

const app = express();

app.use(express.urlencoded());

const redisStore = connectRedis(expressSession);
const sessionParser = expressSession({
  // cookie: {
  //   sameSite: "none",
  // },
  name: "sessionId",
  secret: sessionSecret,
  store: new redisStore({
    client: redis,
  }),
});

app.use(sessionParser);

const fail = (res: express.Response, code: number, message: string): void => {
  debug(message);
  res.status(code)
    .header("Access-Control-Allow-Origin", origin)
    // .header("Access-Control-Allow-Origin", "*")
    .header("Access-Control-Allow-Credentials", "true")
    .json({
      message,
      status: "error",
    });
};

const success = (res: express.Response): void => {
  debug("success");
  res
    .header("Access-Control-Allow-Origin", origin)
    // .header("Access-Control-Allow-Origin", "*")
    .header("Access-Control-Allow-Credentials", "true")
    .json({ status: "ok" });
};

app.post("/enter", async (req, res): Promise<void> => {
  let { gameName, playerName } = req.body as EnterGameRequest;

  if (playerName === undefined) {
    fail(res, 422, "Missing arguments");
    return;
  }

  playerName = playerName.trim();
  if (!utils.filterName(playerName)) {
    fail(res, 422, "Bad player name");
    return;
  }

  if (gameName === undefined || gameName === "") {
    gameName = utils.getGameName();
  } else if (!utils.filterId(gameName)) {
    fail(res, 422, "Bad game name");
    return;
  }

  const gameKey = `game:${gameName}`;

  // setup the game by setting currentRound = 0
  // if the currentRound key already exists on the requested
  // hash that means the game already exists, so join it
  // (use hsetnx instead of an exists...hset so that it is atomic)
  if (await redis.hsetnx(gameKey, "currentRound", 0) === 0) {
    if (await redis.sadd(`${gameKey}:players`, playerName) === 0) {
      fail(res, 422, "Game exists, name taken");
      return;
    }

    req.session.gameName = gameName;
    req.session.playerName = playerName;
    success(res);
    return;
  }

  req.session.gameName = gameName;
  req.session.playerName = playerName;
  success(res);

  await redis.pipeline()
    .hset(gameKey, "numRounds", 10, "host", playerName)
    .sadd(`${gameKey}:players`, playerName)
    .exec();
});

const server = http.createServer(app);
const wsServer = new websocket.Server({
  clientTracking: false,
  noServer: true,
});

server.on(
  "upgrade",
  (req: http.IncomingMessage, sock: net.Socket, head: Buffer): void => {
    if (req.headers.origin !== undefined && req.headers.origin !== origin) {
      sock.destroy();
      return;
    }

    // sessionParser doesn't use the attributes actually
    // provided by express.Request, which is a subclass of
    // http.IncomingMessage (what our req actually is), so
    // it's okay to cast, and it doesn't use the response
    // at all.
    sessionParser(req as express.Request, { } as express.Response, (): void => {
      const session = (req as MaybeSession).session;

      if (
        session === undefined
        || session.gameName === undefined
        || session.playerName === undefined
      ) {
        sock.destroy();
        return;
      }

      wsServer.handleUpgrade(req, sock, head, (client): void => {
        wsServer.emit("connection", client, req);
      });
    });
  },
);

wsServer.on("connection", (ws, req: Session): void => {
  debug("websocket success");
  const client = new Client(ws, req);
  client.on("end", (): void => { console.log("end"); });
});

server.listen(port, (): void => { console.log("started"); });

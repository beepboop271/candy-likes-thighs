import connectRedis from "connect-redis";
import * as dotenv from "dotenv-safe";
import express from "express";
import expressSession from "express-session";
import http from "http";
import Redis from "ioredis";
import type net from "net";
import websocket from "ws";

dotenv.config({ example: ".web.env.example", path: ".web.env" });

const redis = new Redis();

const app = express();

const origin = process.env.ORIGIN!;

app.get("/", (_, res): void => {
  res.end("Hi");
});

// only use middleware on /new and /join
app.use(express.urlencoded());

const redisStore = connectRedis(expressSession);
const sessionParser = expressSession({
  name: "sessionId",
  secret: process.env.SESSION_SECRET!,
  store: new redisStore({
    client: redis,
  }),
});

app.use(sessionParser);

const fail = (res: express.Response, code: number, message: string): void => {
  console.log(message);
  res.status(code)
    .header("Access-Control-Allow-Origin", origin)
    // .header("Access-Control-Allow-Origin", "*")
    .json({
      message,
      status: "error",
    });
};

const success = (res: express.Response): void => {
  console.log("SUCCESS");
  res
    .header("Access-Control-Allow-Origin", origin)
    // .header("Access-Control-Allow-Origin", "*")
    .json({ status: "ok" });
};

const filterId = (id: string): boolean =>
  id.length < 50 && /^[a-zA-Z0-9\-_]+$/.test(id);
const filterName = (name: string): boolean =>
  name.length < 50 && /^[a-zA-Z0-9\-_ ]+$/.test(name);

interface IJoinGameRequest {
  playerName?: string;
}
interface INewGameRequest extends IJoinGameRequest {
  gameName?: string;
}

app.post("/new", async (req, res): Promise<void> => {
  if (req.session === undefined) {
    // never happens?
    fail(res, 500, "help");
    return;
  }

  const body = req.body as INewGameRequest;

  if (body.gameName === undefined || body.playerName === undefined) {
    fail(res, 422, "Missing arguments");
    return;
  }

  if (!filterId(body.gameName)) {
    fail(res, 422, "Bad game name");
    return;
  }
  if (!filterName(body.playerName)) {
    fail(res, 422, "Bad player name");
    return;
  }

  const key = `game:${body.gameName}`;

  // setup the game by setting currentRound = 0
  // if the currentRound key already exists on the requested
  // hash that means the game already exists, so quit.
  // (use hsetnx instead of an exists...hset so that it is atomic)
  if (await redis.hsetnx(key, "currentRound", 0) === 0) {
    fail(res, 422, "Game already exists");
    return;
  }

  req.session.gameName = body.gameName;
  req.session.playerName = body.playerName;

  success(res);

  await redis.pipeline()
    .hset(key, "numRounds", 10)
    .sadd(`${key}:players`, body.playerName)
    .exec();
});

app.post("/:gameName/join", async (req, res): Promise<void> => {
  if (req.session === undefined) {
    // never happens?
    fail(res, 500, "help");
    return;
  }

  const body = req.body as IJoinGameRequest;

  if (body.playerName === undefined) {
    fail(res, 422, "Missing arguments");
    return;
  }

  if (!filterName(body.playerName)) {
    fail(res, 422, "Bad player name");
    return;
  }

  const { gameName } = req.params;

  if (await redis.exists(`game:${gameName}`) === 0) {
    fail(res, 404, "No such game");
    return;
  }

  if (await redis.sadd(`game:${gameName}:players`, body.playerName) === 0) {
    fail(res, 422, "Name taken");
  } else {
    req.session.gameName = gameName;
    req.session.playerName = body.playerName;

    success(res);
  }
});

const server = http.createServer(app);
const wsServer = new websocket.Server({
  clientTracking: false,
  noServer: true,
});

interface IMaybeSession extends http.IncomingMessage {
  session?: {
    gameName?: string;
    playerName?: string;
  };
}
interface ISession extends http.IncomingMessage {
  session: {
    gameName: string;
    playerName: string;
  };
}

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
      const session = (req as IMaybeSession).session;

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

wsServer.on("connection", (ws, req: ISession): void => {
  console.log(req.session);
  console.log("WS CONNECTION WAS ALLOWED");
  ws.close();
});

server.listen(process.env.PORT!, (): void => { console.log("started"); });

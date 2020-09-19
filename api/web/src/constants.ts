import Debug from "debug";
import * as dotenv from "dotenv-safe";
import ioredis from "ioredis";

dotenv.config({ example: ".web.env.example", path: ".web.env" });

export const debug = Debug("canned-thighs");

export const redis = new ioredis();

export const origin = process.env.ORIGIN!;
export const sessionSecret = process.env.SESSION_SECRET!;
export const port = process.env.PORT!;

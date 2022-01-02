import type http from "http";

export interface EnterGameRequest {
  gameName?: string;
  playerName?: string;
}

export interface MaybeSession extends http.IncomingMessage {
  session?: {
    gameName?: string;
    playerName?: string;
  };
}
export interface Session extends http.IncomingMessage {
  session: {
    gameName: string;
    playerName: string;
  };
}

export interface GameSettings {
  rounds: number;
  difficulty: number;
  interval: number;
  charset: number;
}

interface Message {
  message: string;
  data: unknown;
}

interface ChatSendMessage extends Message {
  message: "chat-send";
  data: {
    text: string;
  };
}

// messages only sent from the client
export type ClientMessage =
  | ChatSendMessage;

interface ChatReceiveMessage extends Message {
  message: "chat-receive";
  data: {
    author: string;
    text: string;
  };
}

interface InitPlayerListMessage extends Message {
  message: "init-player-list";
  data: {
    [playerName: string]: number;
  };
}

interface PlayerEnterMessage extends Message {
  message: "player-enter";
  data: {
    player: string;
    score: number;
  };
}

interface PlayerDisappearMessage extends Message {
  message: "player-disappear";
  data: {
    player: string;
  };
}

interface NewHostMessage extends Message {
  message: "new-host";
  data: {
    player: string;
  };
}

export interface RoundStartMessage extends Message {
  message: "round-start";
  data: {
    number: number;
  };
}

export interface NewImageMessage extends Message {
  message: "new-image";
  data: {
    code: string;
  };
}

export interface RoundEndMessage extends Message {
  message: "round-end";
  data: {
    [playerName: string]: number;
  };
}

// messages only sent from the server
export type ServerMessage =
  | NewHostMessage
  | ChatReceiveMessage
  | PlayerDisappearMessage
  | InitPlayerListMessage
  | RoundStartMessage
  | NewImageMessage
  | RoundEndMessage
  | PlayerEnterMessage;

declare module "express-session" {
  interface SessionData {
      gameName?: string;
      playerName?: string;
  }
}

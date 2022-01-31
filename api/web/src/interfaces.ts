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

export interface RawChatReceiveMessage extends Message {
  message: "raw-chat-receive";
  data: {
    author: string;
    text: string;
  };
}

export interface ChatReceiveMessage extends Message {
  message: "chat-receive";
  data: {
    author: string;
    text: string;
    guessed: boolean;
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

export interface YouAreHostMessage extends Message {
  message: "you-are-host";
}

export interface CorrectGuessMessage extends Message {
  message: "correct-guess";
  data: {
    player: string;
    // todo: could emit the new score but then it would be a
    // bit hard to do score changes at the end of the round
    // especially for someone who joins mid round, idk
  };
}

// messages only sent from the server
export type ServerMessage =
  | NewHostMessage
  | RawChatReceiveMessage
  | ChatReceiveMessage
  | PlayerDisappearMessage
  | InitPlayerListMessage
  | RoundStartMessage
  | NewImageMessage
  | RoundEndMessage
  | YouAreHostMessage
  | CorrectGuessMessage
  | PlayerEnterMessage;

declare module "express-session" {
  interface SessionData {
      gameName?: string;
      playerName?: string;
  }
}

export interface GameData {
  [charId: string]: {
    en_name: string;
    aliases: string[];
  };
}

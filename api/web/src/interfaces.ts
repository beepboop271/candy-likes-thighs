import type http from "http";

export interface IEnterGameRequest {
  gameName?: string;
  playerName?: string;
}

export interface IMaybeSession extends http.IncomingMessage {
  session?: {
    gameName?: string;
    playerName?: string;
  };
}
export interface ISession extends http.IncomingMessage {
  session: {
    gameName: string;
    playerName: string;
  };
}

// messages that one client sends to the server
// and the server relays back to everyone
type BroadcastMessage =
  | "chat-message"
  | "start"
  | "transfer-host"
  | "change-settings";

// messages only found from the client
type ClientMessage =
  | BroadcastMessage;

// messages only found from the server
type ServerMessage =
  | BroadcastMessage
  | "player-disappear"
  | "init-player-list"
  | "player-enter";

export interface IClientMessage {
  data: unknown;
  message: ClientMessage;
}

export interface IServerMessage {
  data: unknown;
  message: ServerMessage;
}

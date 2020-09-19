const title = document.getElementById("title");
const playerList = document.getElementById("player-list");
const chatMessages = document.getElementById("messages");
const chatBox = document.getElementById("chat-box");

const scores = new Map();
const ws = new WebSocket("ws://127.0.0.1:8000");
ws.onerror = () => {
  title.innerText = "Error connecting to game server. Are you in a game?";
};
ws.onopen = () => {
  ws.onerror = () => {
    title.innerText = "WebSocket error sending/receiving data with game server";
  };
};

chatBox.onkeyup = function (ev) {
  if (ev.key == "Enter" && !ev.shiftKey) {
    const msg = this.value.trim();
    this.value = "";
    if (msg.length > 0) {
      ws.send(JSON.stringify({
        data: msg,
        message: "chat-message",
      }));
    }
  }
}

function cleanPlayer(player) {
  return player.replace(/ +/g, ".");
}

function addNewPlayer(player, score) {
  playerList.innerHTML += `<div id="player-${cleanPlayer(player)}" style="order:${score};">${player}:<br>${score} points</div>`;
  scores.set(player, score);
}

function updatePlayer(player, score) {
  const element = document.getElementById(`player-${cleanPlayer(player)}`);
  element.style.order = score;
  element.innerHTML = `${player}:<br>${score} points`;
  scores.set(player, score);
}

function removePlayer(player) {
  document
    .getElementById(`player-${cleanPlayer(player)}`)
    .remove();
  scores.delete(player);
}

// max number of message history
const maxMessages = 100;
// pixels from bottom before autoscrolling down
const autoScrollThreshold = 100;

function addMessage(msg) {
  if (chatMessages.childElementCount >= maxMessages) {
    chatMessages.firstElementChild.remove();
  }
  chatMessages.innerHTML += `<div class="message">${msg.author}: ${msg.text}</div>`;

  if (
    chatMessages.scrollTop+chatMessages.clientHeight+autoScrollThreshold
    > chatMessages.scrollHeight
  ) {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }
}

ws.onmessage = function(e) {
  const msg = JSON.parse(e.data);
  if (msg.message === undefined) {
    throw Error("invalid websocket message received");
  }
  switch (msg.message) {
    case "chat-message":
      addMessage(msg.data);
      break;
    case "init-player-list":
      scores.clear();
      for (const [player, score] of Object.entries(msg.data)) {
        addNewPlayer(player, score);
      }
      break;
    case "player-enter":
      const [player, score] = Object.entries(msg.data)[0];
      const localScore = scores.get(player);
      if (localScore !== undefined && localScore !== score) {
        updatePlayer(player, score);
      } else {
        addNewPlayer(player, score);
      }
      break;
    case "player-disappear":
      removePlayer(msg.data);
      break;
  }
}

const api = "127.0.0.1:8000";

const title = document.getElementById("title");
const playerList = document.getElementById("player-list");
const chatMessages = document.getElementById("messages");
const chatBox = document.getElementById("chat-box");
const canvas = document.getElementById("canvas");
canvas.width = 600;
canvas.height = 600;
const ctx = canvas.getContext("2d");

const scores = new Map();
const ws = new WebSocket(`ws://${api}`);
ws.onerror = () => {
  title.innerHTML = "<h1>Error connecting to game server. Are you in a game?</h1>\n<a href=..>Return to homepage</a>";
};
ws.onopen = () => {
  ws.onerror = () => {
    title.innerText = "WebSocket error sending/receiving data with game server";
  };
};

chatBox.onkeydown = function (ev) {
  if (ev.key == "Enter" && !ev.shiftKey) {
    ev.preventDefault()
    const msg = this.value.trim();
    this.value = "";
    if (msg.length > 0) {
      ws.send(JSON.stringify({
        message: "chat-send",
        data: { text: msg },
      }));
    }
  }
}

function addNewPlayer(player, score) {
  playerList.innerHTML += `<div id="player-${player}" style="order:${score};">${player}:<br>${score} points</div>`;
  scores.set(player, score);
}

function updatePlayer(player, score) {
  const element = document.getElementById(`player-${player}`);
  element.style.order = score;
  element.innerHTML = `${player}:<br>${score} points`;
  scores.set(player, score);
}

function removePlayer(player) {
  document
    .getElementById(`player-${player}`)
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
  if (msg.author === "") {
    chatMessages.innerHTML += `<div class="message">${msg.text}</div>`;
  } else {
    chatMessages.innerHTML += `<div class="message">${msg.author}: ${msg.text}</div>`;
  }

  if (
    chatMessages.scrollTop+chatMessages.clientHeight+autoScrollThreshold
    > chatMessages.scrollHeight
  ) {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }
}

function updateImage(code) {
  const im = new Image();
  im.onload = function (ev) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(
      im,
      Math.floor(canvas.width/2)-Math.floor(im.width/2),
      Math.floor(canvas.height/2)-Math.floor(im.height/2),
      im.width,
      im.height,
    );
  }
  im.src = `http://${api}/images/${code}`;
}

function numberWithSign(n) {
  return (n >= 0 ? "+" : "") + n.toString()
}

function updateScores(newScores) {
  const changes = [];
  for (const [player, newScore] of Object.entries(newScores)) {
    const oldScore = scores.get(player);
    if (oldScore !== undefined) {
      changes.push([newScore - oldScore, player]);
      updatePlayer(player, newScore);
    } else {
      console.log("unexpected new score appeared??");
      addNewPlayer(player, newScore);
    }
  }
  changes.sort((a, b) => a[0] - b[0]);
  addMessage({
    author: "",
    text: `Score Changes:<br>${changes.map(v => `${v[1]}: ${numberWithSign(v[0])}`).join("<br>")}<hr>`,
  });
}

ws.onmessage = function(e) {
  const msg = JSON.parse(e.data);
  if (msg.message === undefined) {
    throw Error("invalid websocket message received");
  }
  console.log(msg);
  switch (msg.message) {
    case "chat-receive":
      addMessage(msg.data);
      break;
    case "init-player-list":
      scores.clear();
      for (const [player, score] of Object.entries(msg.data)) {
        addNewPlayer(player, score);
      }
      break;
    case "player-enter":
      const {player, score} = msg.data;
      const localScore = scores.get(player);
      if (localScore !== undefined) {
        if (localScore !== score) {
          updatePlayer(player, score);
        }
      } else {
        addNewPlayer(player, score);
      }
      break;
    case "player-disappear":
      removePlayer(msg.data.player);
      break;
    case "new-image":
      updateImage(msg.data.code);
      break;
    case "round-start":
      addMessage({ author: "", text: `Round ${msg.data.number} Start!`});
      break;
    case "round-end":
      addMessage({ author: "", text: "<hr>Round Over!" });
      updateScores(msg.data);
      break;
  }
}

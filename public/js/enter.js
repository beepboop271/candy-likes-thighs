// perform client side validation so that
// most users won't ever need the server to
// yell at them for having symbols in their
// names
let gameNameBad = false;
const gameErrorSpan = document.getElementById("game-name-error");

let playerNameBad = true;
const playerErrorSpan = document.getElementById("player-name-error");

const submitButton = document.getElementById("form-submit");

function maybeSubmit(ev) {
  submitButton.disabled = gameNameBad || playerNameBad;

  if (!submitButton.disabled && ev.key == "Enter" && !ev.shiftKey) {
    submitButton.click();
  }
}

if (document.getElementById("game-name") !== null) {
  document.getElementById("game-name").onkeyup = function (ev) {
    const id = this.value;
    gameNameBad = true;

    if (id.length < 4) {
      gameErrorSpan.textContent = "Name is too short";
      submitButton.disabled = true;
      return;
    }
    if (id.length > 50) {
      gameErrorSpan.textContent = "Name is too long";
      submitButton.disabled = true;
      return;
    }
    if (!(/^[a-zA-Z0-9\-_]*$/.test(id))) {
      gameErrorSpan.textContent = "Name contains invalid characters";
      submitButton.disabled = true;
      return;
    }
    // no error
    gameNameBad = false;
    gameErrorSpan.textContent = "";
    maybeSubmit(ev);
  }
}

if (document.getElementById("player-name") !== null) {
  document.getElementById("player-name").onkeyup = function (ev) {
    const id = this.value.trim();
    playerNameBad = true;

    if (id.length < 1) {
      playerErrorSpan.textContent = "Name is too short";
      submitButton.disabled = true;
      return;
    }
    if (id.length > 50) {
      playerErrorSpan.textContent = "Name is too long";
      submitButton.disabled = true;
      return;
    }
    if (!(/^[a-zA-Z0-9\-_]+$/.test(id))) {
      playerErrorSpan.textContent = "Name contains invalid characters";
      submitButton.disabled = true;
      return;
    }
    // no error
    playerNameBad = false;
    playerErrorSpan.textContent = "";
    maybeSubmit(ev);
  }
}

// perform form submissions and handle
// errors displayed by the server
async function handleResponse(json) {
  if (json.status === undefined) {
    alert("wtf");
    return;
  }

  if (json.status === "error") {
    if (json.message === "help") {
      alert("If this shows up something very weird has happened.. maybe try again?");
      return;
    }
    if (
      json.message === "Missing arguments"
      || json.message === "Bad player name"
      || json.message === "Bad game name"
    ) {
      // all issues that *should* have been
      // prevented client-side
      alert(json.message);
      return;
    }
    if (json.message === "Game exists, name taken") {
      // this is the only error a typical user should see
      document.getElementById("submit-error").textContent = "Someone in the game already has this name, try a different one"
      return;
    }
    alert("Server replied with unknown error message");
    return;
  }
  if (json.status === "ok") {
    window.location.href = "/game.html"
    return;
  }
  alert("Server replied with unknown status");
}

async function enter() {
  if (submitButton.disabled) {
    return;
  }

  const resp = await fetch(
    "http://127.0.0.1:8000/enter",
    {
      body: new URLSearchParams(new FormData(document.getElementById("enter-form"))),
      credentials: "include",
      method: "POST",
    },
  );

  handleResponse(await resp.json());
}

async function enterInvite() {
  if (submitButton.disabled) {
    return;
  }

  // invite links are like /invite?gameName=hello
  // so we need to extract the parameter to
  // construct the full form body that the
  // api needs
  const inviteLink = new URL(window.location.href);
  const form = new URLSearchParams(new FormData(document.getElementById("enter-form")));
  form.append("gameName", inviteLink.searchParams.get("gameName"));

  const resp = await fetch(
    "http://127.0.0.1:8000/enter",
    {
      body: form,
      credentials: "include",
      method: "POST",
    },
  );

  console.log(resp);

  handleResponse(await resp.json());
}

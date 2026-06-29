// Chat with the EdgeSentry agent via POST /api/chat.
(function () {
  const messages = document.getElementById("messages");
  const input = document.getElementById("input");
  const send = document.getElementById("send");

  function addMessage(text, who, extraClass = "") {
    const el = document.createElement("div");
    el.className = `msg ${who} ${extraClass}`.trim();
    el.textContent = text;
    messages.appendChild(el);
    messages.scrollTop = messages.scrollHeight;
    return el;
  }

  async function ask(question) {
    addMessage(question, "user");
    input.value = "";
    send.disabled = true;
    const thinking = addMessage("EdgeSentry is thinking…", "bot", "thinking");

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: question }),
      });
      const data = await res.json();
      thinking.remove();
      addMessage(data.answer || data.error || "No response.", "bot");
    } catch (err) {
      thinking.remove();
      addMessage("Could not reach the agent: " + err.message, "bot");
    } finally {
      send.disabled = false;
      input.focus();
    }
  }

  send.addEventListener("click", () => {
    const q = input.value.trim();
    if (q) ask(q);
  });
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") send.click();
  });
  document.querySelectorAll(".chip").forEach((chip) =>
    chip.addEventListener("click", () => ask(chip.textContent))
  );
})();

import { FormEvent, useState } from "react";

import { api } from "../api";

type Message = { role: "user" | "assistant"; content: string };
type RecognitionEvent = { results: { [index: number]: { [index: number]: { transcript: string } } } };
type Recognition = {
  lang: string;
  interimResults: boolean;
  onresult: ((event: RecognitionEvent) => void) | null;
  onerror: (() => void) | null;
  start: () => void;
};
type RecognitionWindow = Window & {
  SpeechRecognition?: new () => Recognition;
  webkitSpeechRecognition?: new () => Recognition;
};

export function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [listening, setListening] = useState(false);

  async function send(event: FormEvent) {
    event.preventDefault();
    const text = input.trim();
    if (!text || busy) return;
    setInput("");
    setMessages((current) => [...current, { role: "user", content: text }]);
    setBusy(true);
    setError("");
    try {
      const response = await api.chat(text);
      setMessages((current) => [...current, { role: "assistant", content: response.message }]);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "TutorAI could not respond.");
    } finally {
      setBusy(false);
    }
  }

  function speak(text: string) {
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(new SpeechSynthesisUtterance(text));
    }
  }

  function listen() {
    const speechWindow = window as RecognitionWindow;
    const Recognition =
      speechWindow.SpeechRecognition ?? speechWindow.webkitSpeechRecognition;
    if (!Recognition) {
      setError("Voice input is not supported by this browser.");
      return;
    }
    const recognition = new Recognition();
    recognition.lang = navigator.language;
    recognition.interimResults = false;
    recognition.onresult = (event) => {
      setInput(event.results[0][0].transcript);
      setListening(false);
    };
    recognition.onerror = () => {
      setListening(false);
      setError("Voice input could not be captured.");
    };
    setListening(true);
    recognition.start();
  }

  return (
    <section className="panel chat-panel" aria-labelledby="chat-title">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Ask anything</p>
          <h2 id="chat-title">Your tutor</h2>
        </div>
        <span className="status-pill">Local workspace</span>
      </div>
      <div className="message-list" aria-live="polite">
        {messages.length === 0 && <p className="muted empty-state">Ask a question about your current topic to begin.</p>}
        {messages.map((message, index) => (
          <article className={`message ${message.role}`} key={`${message.role}-${index}`}>
            <strong>{message.role === "user" ? "You" : "TutorAI"}</strong>
            <p>{message.content}</p>
            {message.role === "assistant" && (
              <button className="text-button" onClick={() => speak(message.content)}>Read aloud</button>
            )}
          </article>
        ))}
        {busy && <p className="muted">TutorAI is thinking...</p>}
      </div>
      {error && <p className="error-message" role="alert">{error}</p>}
      <form className="chat-form" onSubmit={send}>
        <label className="sr-only" htmlFor="chat-input">Message TutorAI</label>
        <textarea id="chat-input" value={input} onChange={(event) => setInput(event.target.value)} placeholder="What would you like to understand?" rows={2} />
        <button type="button" className="secondary-button" onClick={listen} disabled={busy || listening}>{listening ? "Listening..." : "Voice input"}</button>
        <button className="primary-button" disabled={busy || !input.trim()}>Send</button>
      </form>
    </section>
  );
}

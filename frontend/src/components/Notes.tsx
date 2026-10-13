import { FormEvent, useState } from "react";

import { api } from "../api";
import type { Note } from "../types";

export function Notes() {
  const [notes, setNotes] = useState<Note[]>([]);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");

  async function save(event: FormEvent) {
    event.preventDefault();
    if (!title.trim() || !content.trim()) return;
    const note = await api.createNote(title.trim(), content.trim());
    setNotes((current) => [note, ...current]);
    setTitle("");
    setContent("");
  }

  return (
    <section className="panel notes-panel" aria-labelledby="notes-title">
      <p className="eyebrow">Remember more</p>
      <h2 id="notes-title">Notes</h2>
      <form onSubmit={save} className="note-form">
        <input aria-label="Note title" value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Note title" />
        <textarea aria-label="Note content" value={content} onChange={(event) => setContent(event.target.value)} placeholder="Capture an insight..." rows={3} />
        <button className="secondary-button">Save note</button>
      </form>
      <div className="notes-list">
        {notes.map((note) => <article key={note.id}><strong>{note.title}</strong><p>{note.content}</p></article>)}
      </div>
    </section>
  );
}

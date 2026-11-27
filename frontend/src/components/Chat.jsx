import { useEffect, useRef, useState } from 'react'

export default function Chat({ messages, me, canSend, onSend }) {
  const [text, setText] = useState('')
  const endRef = useRef(null)

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const submit = (e) => {
    e.preventDefault()
    if (!canSend || !text.trim()) return
    onSend(text)
    setText('')
  }

  return (
    <div className="chat">
      <div className="log">
        {messages.map((m, i) => (
          <div key={i} className={m.player === me ? 'msg mine' : 'msg'}>
            <b>Player {m.player}{m.player === me ? ' (you)' : ''}:</b> {m.text}
          </div>
        ))}
        <div ref={endRef} />
      </div>
      <form onSubmit={submit}>
        <input value={text} maxLength={500} disabled={!canSend}
               placeholder={canSend ? 'Type a message…' : 'Discussion closed'}
               onChange={(e) => setText(e.target.value)} />
        <button disabled={!canSend}>Send</button>
      </form>
    </div>
  )
}
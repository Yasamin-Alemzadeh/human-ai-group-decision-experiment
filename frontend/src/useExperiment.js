import { useCallback, useEffect, useReducer, useRef } from 'react'

const WS_URL =
  import.meta.env.VITE_WS_URL ?? `ws://${location.hostname}:8000/ws`

const initial = {
  status: 'connecting',            // connecting | open | closed
  player: null,
  phase: 'waiting',
  round: 0,
  endsAt: null,
  offset: 0,                       // serverTime - clientTime (ms)
  waiting: null,                   // {joined, needed}
  messages: [],
  feedback: null,                  // {round, counts}
  myVote: null,
  result: null,
}

function reducer(s, a) {
  switch (a.type) {
    case 'open':  return { ...s, status: 'open' }
    case 'close': return { ...s, status: 'closed' }
    case 'voted': return { ...s, myVote: a.target }
    case 'event': {
      const ev = a.ev
      switch (ev.type) {
        case 'waiting':
          return { ...s, waiting: { joined: ev.joined, needed: ev.needed } }
        case 'welcome':            // identity only; the state event decides the phase
          return { ...s, player: ev.player }
        case 'state':
          return {
            ...s,
            phase: ev.phase,
            round: ev.round,
            endsAt: ev.ends_at,
            offset: ev.server_now * 1000 - Date.now(),
            result: ev.result,
            myVote: ev.phase === 'voting' ? null : s.myVote,
          }
        case 'message':
          return { ...s, messages: [...s.messages,
            { player: ev.player, text: ev.text, round: s.round }] }
        case 'feedback':
          return { ...s, feedback: { round: ev.round, counts: ev.counts } }
        default: return s
      }
    }
    default: return s
  }
}

export function useExperiment() {
  const [s, dispatch] = useReducer(reducer, initial)
  const wsRef = useRef(null)

  useEffect(() => {
    const ws = new WebSocket(WS_URL)
    wsRef.current = ws
    ws.onopen = () => dispatch({ type: 'open' })
    ws.onclose = () => dispatch({ type: 'close' })
    ws.onmessage = (e) => dispatch({ type: 'event', ev: JSON.parse(e.data) })
    return () => ws.close()
  }, [])

  const send = useCallback((obj) => {
    const ws = wsRef.current
    if (ws?.readyState === WebSocket.OPEN) ws.send(JSON.stringify(obj))
  }, [])

  const sendMessage = useCallback((text) => send({ type: 'message', text }), [send])
  const vote = useCallback((target) => {
    send({ type: 'vote', target })
    dispatch({ type: 'voted', target })   // optimistic; the first vote is final on the server
  }, [send])

  return { ...s, sendMessage, vote }
}
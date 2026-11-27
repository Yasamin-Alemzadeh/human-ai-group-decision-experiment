import { useEffect, useState } from 'react'

export default function Timer({ endsAt, offset }) {
  const [now, setNow] = useState(Date.now())
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 250)
    return () => clearInterval(id)
  }, [])
  if (!endsAt) return null
  const left = Math.max(0, Math.ceil((endsAt * 1000 - (now + offset)) / 1000))
  return <span className="timer">{left}s</span>
}
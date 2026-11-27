import { useExperiment } from './useExperiment'
import Waiting from './components/Waiting'
import Timer from './components/Timer'
import Chat from './components/Chat'
import Voting from './components/Voting'
import Results from './components/Results'

export default function App() {
  const x = useExperiment()

  if (x.phase === 'results' && x.result) return <Results result={x.result} me={x.player} />
  if (x.status === 'closed') return <div className="card center">Connection lost. Please reload.</div>
  if (x.phase === 'waiting') return <Waiting />

  const voting = x.phase === 'voting'
  return (
    <main className="card">
      <header>
        <span>You are <b>Player {x.player}</b></span>
        <span>Round {x.round} · {voting ? 'Voting' : 'Discussion'} <Timer endsAt={x.endsAt} offset={x.offset} /></span>
      </header>

      {x.feedback && (
        <p className="note">
          Round {x.feedback.round} votes: {Object.entries(x.feedback.counts)
            .map(([p, n]) => `${p}=${n}`).join(', ')}
        </p>
      )}

      <Chat messages={x.messages} me={x.player}
            canSend={x.phase === 'discussion'} onSend={x.sendMessage} />
      {voting && <Voting me={x.player} myVote={x.myVote} onVote={x.vote} />}
    </main>
  )
}
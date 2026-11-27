export default function Voting({ me, myVote, onVote }) {
  return (
    <div className="card">
      <h3>Who should be the Decision Maker?</h3>
      <div className="row">
        {['A', 'B', 'C'].map((p) => (
          <button key={p} disabled={!!myVote}
                  className={myVote === p ? 'picked' : ''}
                  onClick={() => onVote(p)}>
            Player {p}{p === me ? ' (you)' : ''}
          </button>
        ))}
      </div>
      {myVote && <p>Vote recorded. Waiting for others…</p>}
    </div>
  )
}
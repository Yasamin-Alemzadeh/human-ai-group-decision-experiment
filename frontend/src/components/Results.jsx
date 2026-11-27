const TIE = {
  none: '',
  cumulative: 'Tie in the final round, resolved by total votes across rounds.',
  random: 'Tie in all rounds, resolved by random draw.',
}

export default function Results({ result, me }) {
  return (
    <div className="card center">
      <h2>Decision Maker: Player {result.winner}{result.winner === me ? ' (you)' : ''}</h2>
      <ul>
        {Object.entries(result.counts).map(([p, n]) => (
          <li key={p}>Player {p}: {n} vote{n === 1 ? '' : 's'}</li>
        ))}
      </ul>
      {TIE[result.tie_break] && <p className="note">{TIE[result.tie_break]}</p>}
    </div>
  )
}
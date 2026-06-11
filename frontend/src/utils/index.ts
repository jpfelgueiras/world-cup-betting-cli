export function cn(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ')
}

export function formatOdds(odds: number): string {
  return odds.toFixed(2)
}

export function formatProbability(prob: number): string {
  return `${(prob * 100).toFixed(1)}%`
}

export function formatEV(ev: number): string {
  const sign = ev >= 0 ? '+' : ''
  return `${sign}${ev.toFixed(1)}%`
}

export function formatDate(dateString: string | null): string {
  if (!dateString) return 'TBD'
  return new Date(dateString).toLocaleDateString('en-US', {
    weekday: 'short',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function getConfidenceColor(confidence: number): string {
  if (confidence >= 70) return 'text-success'
  if (confidence >= 60) return 'text-warning'
  return 'text-danger'
}

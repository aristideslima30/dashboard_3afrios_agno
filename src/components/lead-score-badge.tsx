import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

interface LeadScoreBadgeProps {
  score: number
  className?: string
}

export function LeadScoreBadge({ score, className }: LeadScoreBadgeProps) {
  const getScoreColor = (score: number) => {
    if (score >= 8) return 'bg-green-500 hover:bg-green-600'
    if (score >= 5) return 'bg-yellow-500 hover:bg-yellow-600'
    if (score >= 3) return 'bg-orange-500 hover:bg-orange-600'
    return 'bg-red-500 hover:bg-red-600'
  }

  const getScoreLabel = (score: number) => {
    if (score >= 8) return 'Quente'
    if (score >= 5) return 'Morno'
    if (score >= 3) return 'Frio'
    return 'Gelado'
  }

  return (
    <Badge 
      className={cn(
        'text-white font-medium',
        getScoreColor(score),
        className
      )}
    >
      {score}/10 - {getScoreLabel(score)}
    </Badge>
  )
}
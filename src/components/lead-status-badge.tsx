import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

interface LeadStatusBadgeProps {
  status: 'novo' | 'interessado' | 'pronto_para_comprar'
  className?: string
}

export function LeadStatusBadge({ status, className }: LeadStatusBadgeProps) {
  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'novo':
        return { color: 'bg-blue-500 hover:bg-blue-600', label: 'Novo' }
      case 'interessado':
        return { color: 'bg-yellow-500 hover:bg-yellow-600', label: 'Interessado' }
      case 'pronto_para_comprar':
        return { color: 'bg-green-500 hover:bg-green-600', label: 'Pronto p/ Comprar' }
      default:
        return { color: 'bg-gray-500 hover:bg-gray-600', label: 'Desconhecido' }
    }
  }

  const config = getStatusConfig(status)

  return (
    <Badge 
      className={cn(
        'text-white font-medium',
        config.color,
        className
      )}
    >
      {config.label}
    </Badge>
  )
}
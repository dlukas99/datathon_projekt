import {
  Baby,
  Blocks,
  Bus,
  Flame,
  Footprints,
  Map as MapIcon,
  Pill,
  Scale,
  Search,
  Recycle,
  School,
  Shapes,
  ShoppingBasket,
  Stethoscope,
  Sun,
  Trees,
  Volume2,
  Waves,
  Wind,
  type LucideIcon,
} from 'lucide-react'

const ICONS: Record<string, LucideIcon> = {
  flood: Waves,
  air: Wind,
  green: Trees,
  noise: Volume2,
  fire: Flame,
  solar: Sun,
  car_free: Footprints,
  transit: Bus,
  kindergarten: Blocks,
  school: School,
  doctor: Stethoscope,
  pediatrician: Baby,
  pharmacy: Pill,
  grocery: ShoppingBasket,
  playground: Shapes,
  recycling: Recycle,
  compare: Scale,
  find: Search,
  map: MapIcon,
}

/** Decorative icon for a category; the text next to it always carries the meaning. */
export function CategoryIcon({ id, size = 20 }: { id: string; size?: number }) {
  const Icon = ICONS[id]
  if (!Icon) return null
  return <Icon size={size} strokeWidth={1.75} aria-hidden="true" focusable="false" />
}

export default function NiktoLogo({ size = 32, animated = false }: { size?: number; animated?: boolean }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={animated ? 'animate-pulse-glow' : ''}
    >
      <rect width="32" height="32" rx="8" fill="#22c55e" fillOpacity="0.15" />
      <path
        d="M16 4L28 12V20L16 28L4 20V12L16 4Z"
        stroke="#22c55e"
        strokeWidth="1.5"
        fill="#22c55e"
        fillOpacity="0.1"
      />
      <path
        d="M16 8L24 13.5V18.5L16 24L8 18.5V13.5L16 8Z"
        stroke="#22c55e"
        strokeWidth="1"
        fill="#22c55e"
        fillOpacity="0.05"
      />
      <circle cx="16" cy="16" r="3" fill="#22c55e" />
      <circle cx="16" cy="16" r="1.5" fill="#030712" />
    </svg>
  )
}

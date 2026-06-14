export default function TypingIndicator() {
  return (
    <div className="flex items-start gap-3 animate-fade-in px-4">
      <div className="w-8 h-8 rounded-full bg-nikto-green/20 flex items-center justify-center flex-shrink-0">
        <svg width="16" height="16" viewBox="0 0 32 32" fill="none">
          <circle cx="16" cy="16" r="3" fill="#22c55e" />
        </svg>
      </div>
      <div className="flex items-center gap-1 py-3">
        <span className="w-2 h-2 bg-nikto-green rounded-full animate-typing" style={{ animationDelay: '0s' }} />
        <span className="w-2 h-2 bg-nikto-green rounded-full animate-typing" style={{ animationDelay: '0.2s' }} />
        <span className="w-2 h-2 bg-nikto-green rounded-full animate-typing" style={{ animationDelay: '0.4s' }} />
      </div>
    </div>
  )
}

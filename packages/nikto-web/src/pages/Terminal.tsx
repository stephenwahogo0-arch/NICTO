import { useState, useRef, useEffect } from 'react'

const API = 'http://127.0.0.1:4890'

export default function Terminal() {
  const [lines, setLines] = useState<string[]>([
    'Nikto Terminal v0.1.0',
    'Type /help for commands',
    '---',
  ])
  const [input, setInput] = useState('')
  const [mode, setMode] = useState<'plan' | 'build'>('build')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => { bottomRef.current?.scrollIntoView() }, [lines])

  const send = async () => {
    if (!input.trim()) return
    const cmd = input
    setInput('')
    setLines(prev => [...prev, `> ${cmd}`])

    if (cmd === '/help') {
      setLines(prev => [...prev, '/help, /mode, /clear, /status, /agents'])
      return
    }
    if (cmd === '/clear') { setLines([]); return }
    if (cmd === '/mode') {
      const m = mode === 'plan' ? 'build' : 'plan'
      setMode(m)
      setLines(prev => [...prev, `Mode: ${m}`])
      return
    }

    try {
      const res = await fetch(`${API}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: cmd, mode }),
      })
      const data = await res.json()
      setLines(prev => [...prev, data.response || JSON.stringify(data)])
    } catch (e: any) {
      setLines(prev => [...prev, `Error: ${e.message}`])
    }
  }

  return (
    <div className="p-6 h-full flex flex-col">
      <div className="flex items-center gap-3 mb-4">
        <h1 className="text-xl font-bold text-white">Terminal</h1>
        <span className={`text-xs px-2 py-0.5 rounded ${mode === 'build' ? 'bg-green-900 text-green-400' : 'bg-blue-900 text-blue-400'}`}>
          {mode}
        </span>
      </div>
      <div className="flex-1 bg-black rounded-xl p-4 font-mono text-sm overflow-auto" style={{ maxHeight: 'calc(100vh - 200px)' }}>
        {lines.map((l, i) => (
          <div key={i} className={`mb-1 ${l.startsWith('>') ? 'text-green-400' : 'text-gray-300'}`}>
            {l}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
      <div className="flex mt-2 gap-2">
        <input
          className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-gray-100 outline-none focus:border-cyan-500"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && send()}
          placeholder="Type a command..."
        />
        <button onClick={send} className="bg-cyan-600 hover:bg-cyan-500 px-4 py-2 rounded-lg text-white font-medium">
          Send
        </button>
      </div>
    </div>
  )
}

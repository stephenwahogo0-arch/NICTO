export default function Security() {
  const tools = ['Nmap', 'Gobuster', 'SQLMap', 'Nikto', 'Hashcat', 'Hydra', 'Metasploit', 'Searchsploit', 'Amass', 'Wireshark', 'John the Ripper', 'FFUF']

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-white mb-6">Security Arsenal</h1>
      <div className="grid grid-cols-4 gap-3">
        {tools.map((t, i) => (
          <div key={i} className="bg-gray-900 border border-gray-800 rounded-xl p-4 hover:border-cyan-700 transition-colors cursor-pointer">
            <div className="text-cyan-400 font-medium text-sm">{t}</div>
            <div className="text-gray-500 text-xs mt-1">Tool wrapper ready</div>
          </div>
        ))}
      </div>
    </div>
  )
}

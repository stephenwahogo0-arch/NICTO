export default function Crypto() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-white mb-6">Crypto Dashboard</h1>
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="text-gray-400 text-sm mb-1">Wallet Balance</div>
          <div className="text-3xl font-bold text-yellow-400">0.000 BTC</div>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="text-gray-400 text-sm mb-1">Mining Hashrate</div>
          <div className="text-3xl font-bold text-cyan-400">0 H/s</div>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="text-gray-400 text-sm mb-1">Total Earned</div>
          <div className="text-3xl font-bold text-green-400">$0.00</div>
        </div>
      </div>
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
        <h2 className="text-white font-semibold mb-3">Earning Tasks</h2>
        <div className="space-y-2 text-sm text-gray-400">
          <div className="flex justify-between"><span>Faucet Claims</span><span>0 / day</span></div>
          <div className="flex justify-between"><span>Browser Mining</span><span>Inactive</span></div>
          <div className="flex justify-between"><span>CAPTCHA Solving</span><span>Not configured</span></div>
          <div className="flex justify-between"><span>Trading Bot</span><span>Disabled</span></div>
        </div>
      </div>
    </div>
  )
}

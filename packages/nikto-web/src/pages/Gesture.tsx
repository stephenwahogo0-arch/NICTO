import React, { useEffect, useState } from 'react'
import { Hand, Activity, Moon, Users, Zap, Settings, Volume2, Minimize, Camera, AlertTriangle, Maximize } from 'lucide-react'
import { useGesture, useEffectOverlay } from '../gesture-ui/useGesture'
import { visualEffects, DEFAULT_BINDINGS, type EffectBinding, type VisualEffect } from '../gesture-ui/VisualEffects'

const EFFECT_ICONS: Record<string, any> = {
  minimize: Minimize, maximize: Maximize, close: AlertTriangle,
  screenshot: Camera, volume_up: Volume2, volume_down: Volume2,
  mute: Volume2, next_track: Zap, prev_track: Zap, play_pause: Zap,
  scroll_up: Zap, scroll_down: Zap, cursor_click: Zap,
  cursor_double_click: Zap, snap_left: Zap, snap_right: Zap,
}

const GESTURE_EMOJIS: Record<string, string> = {
  wave: '\u{1F44B}', swipe_left: '\u{2B05}\u{FE0F}', swipe_right: '\u{27A1}\u{FE0F}',
  swipe_up: '\u{2B06}\u{FE0F}', swipe_down: '\u{2B07}\u{FE0F}',
  push: '\u{1F449}', pull: '\u{1F448}', circle_cw: '\u{1F504}', circle_ccw: '\u{1F503}',
  tap: '\u{1F446}', double_tap: '\u{1F446}\u{1F446}', unknown: '\u{2753}',
}

function StateCard({ icon: Icon, label, value, color, emoji }: {
  icon: any; label: string; value: string; color: string; emoji?: string
}) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-1">
        <Icon size={16} className={color} />
        <span className="text-gray-400 text-xs">{label}</span>
      </div>
      <div className="flex items-center gap-2">
        {emoji && <span className="text-xl">{emoji}</span>}
        <div className="text-lg font-bold text-white">{value}</div>
      </div>
    </div>
  )
}

export default function GesturePage() {
  const { gesture, movement, connected, effect } = useGesture()
  const { activeEffect, show } = useEffectOverlay()
  const [engineOn, setEngineOn] = useState(true)
  const [bindings, setBindings] = useState<EffectBinding[]>(DEFAULT_BINDINGS)

  useEffect(() => { visualEffects.start() }, [])
  useEffect(() => {
    if (engineOn) visualEffects.start()
    else visualEffects.stop()
  }, [engineOn])
  useEffect(() => {
    if (effect) show(effect)
  }, [effect, show])

  const updateBinding = (idx: number, eff: VisualEffect) => {
    setBindings(prev => prev.map((b, i) => i === idx ? { ...b, effect: eff } : b))
  }

  return (
    <div className="p-6 relative">
      {activeEffect && (
        <div className="fixed inset-0 pointer-events-none z-50 flex items-center justify-center" style={{ opacity: activeEffect.opacity }}>
          <div className="bg-cyan-500/20 border border-cyan-400/40 rounded-2xl p-8 backdrop-blur-xl text-center animate-ping">
            {React.createElement(EFFECT_ICONS[activeEffect.effect.effect] || Zap, { size: 48, className: 'text-cyan-400 mx-auto mb-2' })}
            <div className="text-cyan-300 font-bold text-xl">{activeEffect.effect.effect.replace(/_/g, ' ')}</div>
            <div className="text-cyan-400/70 text-sm mt-1">{activeEffect.effect.description}</div>
          </div>
        </div>
      )}

      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Hand className="text-cyan-400" /> Gesture Control
        </h1>
        <div className="flex items-center gap-3">
          <span className={`text-sm px-3 py-1 rounded-full ${connected ? 'bg-green-900/50 text-green-400' : 'bg-red-900/50 text-red-400'}`}>
            {connected ? '\u{1F7E2} Connected' : '\u{1F534} Disconnected'}
          </span>
          <button
            onClick={() => setEngineOn(!engineOn)}
            className={`px-3 py-1 rounded-lg text-sm ${engineOn ? 'bg-cyan-600/20 text-cyan-400' : 'bg-gray-800 text-gray-500'}`}
          >
            {engineOn ? 'Engine ON' : 'Engine OFF'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-5 gap-3 mb-6">
        <StateCard icon={Activity} label="Movement" value={movement?.movement ?? '---'} color="text-cyan-400" />
        <StateCard icon={Users} label="People" value={String(movement?.num_people ?? '---')} color="text-green-400" />
        <StateCard icon={Moon} label="Sleep Stage" value={movement?.sleep_stage ?? '---'} color="text-purple-400" />
        <StateCard icon={Activity} label="Breathing" value={movement ? `${movement.breathing_bpm} BPM` : '---'} color="text-pink-400" />
        <StateCard icon={Zap} label="Last Gesture" value={gesture ? `${(gesture.confidence * 100).toFixed(0)}%` : '---'} emoji={gesture ? GESTURE_EMOJIS[gesture.gesture] || '\u{2753}' : undefined} color="text-yellow-400" />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <h2 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
            <Zap size={18} className="text-yellow-400" /> Live Gesture Log
          </h2>
          <div className="space-y-2 max-h-80 overflow-auto">
            {gesture ? (
              <div className="bg-gray-800/50 rounded-lg p-3 border border-gray-700/50">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">{GESTURE_EMOJIS[gesture.gesture] || '\u{2753}'}</span>
                  <span className="text-white font-medium capitalize">{gesture.gesture.replace(/_/g, ' ')}</span>
                  <span className="text-gray-400 text-xs ml-auto">{(gesture.confidence * 100).toFixed(1)}%</span>
                </div>
                {gesture.velocity > 0 && (
                  <div className="text-gray-500 text-xs mt-1">Velocity: {gesture.velocity.toFixed(1)} m/s</div>
                )}
              </div>
            ) : (
              <div className="text-gray-500 text-sm">Waiting for gesture events...</div>
            )}
          </div>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <h2 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
            <Settings size={18} className="text-cyan-400" /> Gesture → Effect Bindings
          </h2>
          <div className="space-y-2 max-h-80 overflow-auto">
            {bindings.map((b, i) => {
              const Icon = EFFECT_ICONS[b.effect] || Zap
              return (
                <div key={b.gesture} className="flex items-center gap-3 bg-gray-800/30 rounded-lg px-3 py-2 border border-gray-700/30">
                  <span className="text-xl">{GESTURE_EMOJIS[b.gesture] || '\u{2753}'}</span>
                  <span className="text-gray-300 text-sm w-24 capitalize">{b.gesture.replace(/_/g, ' ')}</span>
                  <Icon size={16} className="text-cyan-400" />
                  <select
                    value={b.effect}
                    onChange={e => updateBinding(i, e.target.value as VisualEffect)}
                    className="flex-1 bg-gray-800 border border-gray-700 rounded text-gray-200 text-xs px-2 py-1"
                  >
                    {Object.keys(EFFECT_ICONS).map(e => (
                      <option key={e} value={e}>{e.replace(/_/g, ' ')}</option>
                    ))}
                  </select>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}

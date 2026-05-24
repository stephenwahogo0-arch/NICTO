import { useState, useEffect, useCallback, useRef } from 'react'
import { gestureClient, type GestureEvent, type MovementState, type GestureCallback, type MovementCallback } from './GestureClient'
import { visualEffects, lookupEffect, type EffectBinding } from './VisualEffects'

export function useGesture() {
  const [gesture, setGesture] = useState<GestureEvent | null>(gestureClient.getLastGesture())
  const [movement, setMovement] = useState<MovementState | null>(gestureClient.getLastState())
  const [connected, setConnected] = useState(false)
  const [effect, setEffect] = useState<EffectBinding | null>(null)

  useEffect(() => {
    gestureClient.connect()
    setConnected(true)
    const onG: GestureCallback = (ev) => {
      setGesture(ev)
      const binding = visualEffects.trigger(ev.gesture, ev.velocity)
      if (binding) setEffect(binding)
    }
    const onM: MovementCallback = (st) => setMovement(st)
    gestureClient.onGesture(onG)
    gestureClient.onMovement(onM)
    return () => {
      gestureClient.offGesture(onG)
      gestureClient.offMovement(onM)
    }
  }, [])

  const triggerManual = useCallback((gesture: string) => {
    const binding = visualEffects.trigger(gesture)
    if (binding) setEffect(binding)
  }, [])

  return { gesture, movement, connected, effect, triggerManual }
}

export function useEffectOverlay(duration: number = 800) {
  const [activeEffect, setActiveEffect] = useState<{ effect: EffectBinding; opacity: number } | null>(null)
  const timer = useRef<ReturnType<typeof setTimeout>>()

  const show = useCallback((binding: EffectBinding) => {
    if (timer.current) clearTimeout(timer.current)
    setActiveEffect({ effect: binding, opacity: 1 })
    timer.current = setTimeout(() => {
      setActiveEffect(null)
    }, duration)
  }, [duration])

  return { activeEffect, show }
}

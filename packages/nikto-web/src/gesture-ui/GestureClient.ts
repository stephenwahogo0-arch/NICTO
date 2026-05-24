export interface GestureEvent {
  gesture: string
  confidence: number
  velocity: number
  timestamp: number
}

export interface MovementState {
  movement: string
  num_people: number
  activity_confidence: number
  sleep_stage: string
  breathing_bpm: number
  rssi: number
  variance: number
}

export type GestureCallback = (event: GestureEvent) => void
export type MovementCallback = (state: MovementState) => void

export class GestureClient {
  private ws: WebSocket | null = null
  private gestureCbs: GestureCallback[] = []
  private movementCbs: MovementCallback[] = []
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private lastState: MovementState | null = null
  private lastGesture: GestureEvent | null = null

  constructor(private url: string = 'ws://127.0.0.1:4891/gesture') {}

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN) return
    try {
      this.ws = new WebSocket(this.url)
      this.ws.onmessage = (msg) => {
        try {
          const data = JSON.parse(msg.data)
          if (data.gesture) {
            const ev: GestureEvent = {
              gesture: data.gesture,
              confidence: data.gesture_confidence ?? 1,
              velocity: data.gesture_velocity ?? 0,
              timestamp: data.timestamp ?? Date.now(),
            }
            this.lastGesture = ev
            this.gestureCbs.forEach(cb => cb(ev))
          }
          if (data.movement) {
            const st: MovementState = {
              movement: data.movement,
              num_people: data.num_people ?? 0,
              activity_confidence: data.activity_confidence ?? 0,
              sleep_stage: data.sleep_stage ?? 'awake',
              breathing_bpm: data.breathing_bpm ?? 0,
              rssi: data.rssi ?? 0,
              variance: data.variance ?? 0,
            }
            this.lastState = st
            this.movementCbs.forEach(cb => cb(st))
          }
        } catch { /* ignore malformed frames */ }
      }
      this.ws.onclose = () => {
        this.ws = null
        this.reconnectTimer = setTimeout(() => this.connect(), 3000)
      }
      this.ws.onerror = () => this.ws?.close()
    } catch { /* ignore */ }
  }

  disconnect() {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer)
    this.ws?.close()
    this.ws = null
  }

  onGesture(cb: GestureCallback) { this.gestureCbs.push(cb) }
  offGesture(cb: GestureCallback) { this.gestureCbs = this.gestureCbs.filter(c => c !== cb) }
  onMovement(cb: MovementCallback) { this.movementCbs.push(cb) }
  offMovement(cb: MovementCallback) { this.movementCbs = this.movementCbs.filter(c => c !== cb) }

  getLastGesture() { return this.lastGesture }
  getLastState() { return this.lastState }
}

export const gestureClient = new GestureClient()

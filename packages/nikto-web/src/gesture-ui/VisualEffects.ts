export type VisualEffect =
  | 'minimize'
  | 'maximize'
  | 'close'
  | 'screenshot'
  | 'volume_up'
  | 'volume_down'
  | 'mute'
  | 'next_track'
  | 'prev_track'
  | 'play_pause'
  | 'scroll_up'
  | 'scroll_down'
  | 'cursor_click'
  | 'cursor_double_click'
  | 'snap_left'
  | 'snap_right'

export interface EffectBinding {
  gesture: string
  effect: VisualEffect
  label: string
  description: string
}

export const DEFAULT_BINDINGS: EffectBinding[] = [
  { gesture: 'wave', effect: 'minimize', label: 'Wave', description: 'Minimize active window' },
  { gesture: 'swipe_left', effect: 'prev_track', label: 'Swipe Left', description: 'Previous track / tab' },
  { gesture: 'swipe_right', effect: 'next_track', label: 'Swipe Right', description: 'Next track / tab' },
  { gesture: 'swipe_up', effect: 'volume_up', label: 'Swipe Up', description: 'Volume up' },
  { gesture: 'swipe_down', effect: 'volume_down', label: 'Swipe Down', description: 'Volume down' },
  { gesture: 'push', effect: 'screenshot', label: 'Push', description: 'Take screenshot' },
  { gesture: 'pull', effect: 'maximize', label: 'Pull', description: 'Maximize window' },
  { gesture: 'circle_cw', effect: 'scroll_up', label: 'Circle CW', description: 'Scroll up' },
  { gesture: 'circle_ccw', effect: 'scroll_down', label: 'Circle CCW', description: 'Scroll down' },
  { gesture: 'tap', effect: 'cursor_click', label: 'Tap', description: 'Left click' },
  { gesture: 'double_tap', effect: 'cursor_double_click', label: 'Double Tap', description: 'Double click' },
]

export function lookupEffect(gesture: string, bindings: EffectBinding[] = DEFAULT_BINDINGS): EffectBinding | undefined {
  return bindings.find(b => b.gesture === gesture)
}

function executeSystemCommand(effect: VisualEffect) {
  const commands: Record<VisualEffect, string> = {
    minimize: 'powershell -command "(new-object -com shell.application).minimizeall()"',
    maximize: 'powershell -command "$w=Get-Process | Where {$_.MainWindowHandle -ne 0} | Select -Last 1; Add-Type @\" [DllImport(\"user32.dll\")] public static extern bool ShowWindowAsync(IntPtr hWnd, int nCmdShow); \"@; [ShowWindowAsync]::ShowWindowAsync($w.MainWindowHandle, 3)"',
    close: '',
    screenshot: 'powershell -command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait(\"{PRTSC}\")"',
    volume_up: 'powershell -command "(new-object -com wscript.shell).SendKeys([char]175)"',
    volume_down: 'powershell -command "(new-object -com wscript.shell).SendKeys([char]174)"',
    mute: 'powershell -command "(new-object -com wscript.shell).SendKeys([char]173)"',
    next_track: 'powershell -command "(new-object -com wscript.shell).SendKeys([char]176)"',
    prev_track: 'powershell -command "(new-object -com wscript.shell).SendKeys([char]177)"',
    play_pause: 'powershell -command "(new-object -com wscript.shell).SendKeys([char]179)"',
    scroll_up: 'powershell -command "[System.Windows.Forms.SendKeys]::SendWait(\"{UP}\")"',
    scroll_down: 'powershell -command "[System.Windows.Forms.SendKeys]::SendWait(\"{DOWN}\")"',
    cursor_click: '',
    cursor_double_click: '',
    snap_left: 'powershell -command "$w=Get-Process | Where {$_.MainWindowHandle -ne 0 -and $_.MainWindowTitle -ne \"\"} | Select -First 1; Add-Type @\" [DllImport(\"user32.dll\")] public static extern bool ShowWindowAsync(IntPtr hWnd, int nCmdShow); [DllImport(\"user32.dll\")] public static extern bool SetWindowPos(IntPtr hWnd, IntPtr h, int x, int y, int w, int h, uint f); \"@; [ShowWindowAsync]::ShowWindowAsync($w.MainWindowHandle, 1); Start-Sleep -m 100; [SetWindowPos]::SetWindowPos($w.MainWindowHandle, 0, 0, 0, [System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Width/2, [System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Height, 0x0040)"',
    snap_right: '',
  }
  const cmd = commands[effect]
  if (!cmd) return
  try {
    fetch('http://127.0.0.1:4892/exec', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command: cmd }),
    }).catch(() => {})
  } catch { /* silent */ }
}

export class VisualEffectEngine {
  private active = false
  private lastEffect: VisualEffect | null = null
  private lastTrigger = 0
  private cooldown = 500  // ms between triggers

  start() { this.active = true }
  stop() { this.active = false }

  trigger(gesture: string, velocity: number = 0) {
    if (!this.active) return null
    const now = Date.now()
    if (now - this.lastTrigger < this.cooldown) return null

    const binding = lookupEffect(gesture)
    if (!binding) return null

    this.lastEffect = binding.effect
    this.lastTrigger = now
    executeSystemCommand(binding.effect)
    return binding
  }
}

export const visualEffects = new VisualEffectEngine()

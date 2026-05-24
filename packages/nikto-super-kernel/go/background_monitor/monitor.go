package main

import (
	"encoding/json"
	"os"
	"runtime"
	"strconv"
	"time"
)

type CPUMetrics struct {
	CPUPercent  float64 `json:"cpu_percent"`
	GoRoutines  int     `json:"go_routines"`
	MemoryMB    float64 `json:"memory_mb"`
	NumCPU      int     `json:"num_cpu"`
	OS          string  `json:"os"`
	UptimeSecs  float64 `json:"uptime_secs"`
	LastUpdated int64   `json:"last_updated"`
}

var startTime = time.Now()

func getCPUPercent() float64 {
	var m runtime.MemStats
	runtime.ReadMemStats(&m)
	return float64(m.NumGC) / float64(time.Since(startTime).Seconds()+1) * 100
}

func getMemoryMB() float64 {
	var m runtime.MemStats
	runtime.ReadMemStats(&m)
	return float64(m.Alloc) / 1024 / 1024
}

func runMonitor(intervalMs int) {
	ticker := time.NewTicker(time.Duration(intervalMs) * time.Millisecond)
	defer ticker.Stop()
	for range ticker.C {
		m := CPUMetrics{
			CPUPercent:  getCPUPercent(),
			GoRoutines:  runtime.NumGoroutine(),
			MemoryMB:    getMemoryMB(),
			NumCPU:      runtime.NumCPU(),
			OS:          runtime.GOOS,
			UptimeSecs:  time.Since(startTime).Seconds(),
			LastUpdated: time.Now().Unix(),
		}
		data, _ := json.Marshal(m)
		os.Stdout.Write(data)
		os.Stdout.Write([]byte("\n"))
	}
}

func main() {
	intervalMs := 5000
	if len(os.Args) > 1 {
		intervalMs, _ = strconv.Atoi(os.Args[1])
	}
	if intervalMs < 100 {
		intervalMs = 100
	}
	runMonitor(intervalMs)
}

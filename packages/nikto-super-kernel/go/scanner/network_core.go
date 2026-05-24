package main

import (
	"encoding/json"
	"fmt"
	"net"
	"os"
	"strings"
	"sync"
	"time"
)

type PortResult struct {
	Port    int    `json:"port"`
	Open    bool   `json:"open"`
	Service string `json:"service"`
	Banner  string `json:"banner"`
}

type ScanResult struct {
	Host      string       `json:"host"`
	Ports     []PortResult `json:"ports"`
	OpenCount int          `json:"open_count"`
	Duration  string       `json:"duration_ms"`
}

type PingResult struct {
	Host    string `json:"host"`
	Reached bool   `json:"reached"`
}

var commonPorts = map[int]string{
	21: "ftp", 22: "ssh", 23: "telnet", 25: "smtp", 53: "dns",
	80: "http", 110: "pop3", 143: "imap", 443: "https", 445: "smb",
	993: "imaps", 995: "pop3s", 1433: "mssql", 1521: "oracle",
	2049: "nfs", 3306: "mysql", 3389: "rdp", 5432: "postgresql",
	5900: "vnc", 6379: "redis", 8080: "http-proxy", 8443: "https-alt",
	27017: "mongodb",
}

func scanPort(host string, port int, timeout time.Duration) PortResult {
	addr := fmt.Sprintf("%s:%d", host, port)
	conn, err := net.DialTimeout("tcp", addr, timeout)
	pr := PortResult{Port: port, Open: false, Service: "unknown", Banner: ""}
	if err != nil {
		return pr
	}
	defer conn.Close()
	pr.Open = true
	if svc, ok := commonPorts[port]; ok {
		pr.Service = svc
	}
	buf := make([]byte, 256)
	conn.SetReadDeadline(time.Now().Add(timeout))
	if n, err := conn.Read(buf); err == nil && n > 0 {
		pr.Banner = string(buf[:n])
	}
	return pr
}

func doScan(host string, portsStr string, timeoutMs int) string {
	timeout := time.Duration(timeoutMs) * time.Millisecond
	if timeoutMs <= 0 {
		timeout = 2 * time.Second
	}

	ports := []int{}
	if portsStr == "common" || portsStr == "" {
		for p := range commonPorts {
			ports = append(ports, p)
		}
	} else {
		for _, s := range strings.Split(portsStr, ",") {
			var p int
			fmt.Sscanf(strings.TrimSpace(s), "%d", &p)
			if p > 0 {
				ports = append(ports, p)
			}
		}
	}

	start := time.Now()
	var mu sync.Mutex
	results := make([]PortResult, 0, len(ports))
	var wg sync.WaitGroup
	sem := make(chan struct{}, 100)

	for _, port := range ports {
		wg.Add(1)
		sem <- struct{}{}
		go func(p int) {
			defer wg.Done()
			defer func() { <-sem }()
			pr := scanPort(host, p, timeout)
			if pr.Open {
				mu.Lock()
				results = append(results, pr)
				mu.Unlock()
			}
		}(port)
	}
	wg.Wait()
	close(sem)

	duration := time.Since(start)
	scanResult := ScanResult{
		Host:      host,
		Ports:     results,
		OpenCount: len(results),
		Duration:  fmt.Sprintf("%.0f", duration.Seconds()*1000),
	}
	data, _ := json.Marshal(scanResult)
	return string(data)
}

func doPing(host string) string {
	conn, err := net.DialTimeout("tcp", host+":80", 2*time.Second)
	pr := PingResult{Host: host, Reached: false}
	if err == nil {
		conn.Close()
		pr.Reached = true
	}
	data, _ := json.Marshal(pr)
	return string(data)
}

func main() {
	if len(os.Args) < 2 {
		fmt.Println(`{"error":"usage: scanner scan <host> [ports] [timeout_ms] | scanner ping <host>"}`)
		return
	}
	cmd := os.Args[1]
	switch cmd {
	case "scan":
		if len(os.Args) < 3 {
			fmt.Println(`{"error":"missing host"}`)
			return
		}
		host := os.Args[2]
		ports := ""
		if len(os.Args) > 3 {
			ports = os.Args[3]
		}
		timeoutMs := 2000
		if len(os.Args) > 4 {
			fmt.Sscanf(os.Args[4], "%d", &timeoutMs)
		}
		fmt.Println(doScan(host, ports, timeoutMs))
	case "ping":
		if len(os.Args) < 3 {
			fmt.Println(`{"error":"missing host"}`)
			return
		}
		fmt.Println(doPing(os.Args[2]))
	default:
		fmt.Printf(`{"error":"unknown command: %s"}`, cmd)
	}
}

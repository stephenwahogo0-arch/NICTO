package main

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strconv"
	"strings"
	"sync"
	"time"
)

var (
	oddsCache   = make(map[string]OddsEntry)
	oddsCacheMu sync.RWMutex
)

type OddsEntry struct {
	Sport    string  `json:"sport"`
	League   string  `json:"league"`
	TeamA    string  `json:"team_a"`
	TeamB    string  `json:"team_b"`
	OddsA    float64 `json:"odds_a"`
	OddsB    float64 `json:"odds_b"`
	OddsDraw float64 `json:"odds_draw"`
	Fetched  int64   `json:"fetched"`
}

type OddsSnapshot struct {
	Entries   []OddsEntry `json:"entries"`
	Count     int         `json:"count"`
	Timestamp int64       `json:"timestamp"`
}

func fetchOdds(sport, league string) string {
	key := sport + ":" + league
	oddsCacheMu.RLock()
	cached, ok := oddsCache[key]
	oddsCacheMu.RUnlock()
	if ok && time.Now().Unix()-cached.Fetched < 300 {
		data, _ := json.Marshal(cached)
		return string(data)
	}

	url := fmt.Sprintf("https://api.the-odds-api.com/v4/sports/%s/odds/?regions=us&markets=h2h&apiKey=demo", sport)
	resp, err := http.Get(url)
	if err != nil {
		return `{"error":"api_unavailable"}`
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)

	entry := OddsEntry{
		Sport:   sport,
		League:  league,
		Fetched: time.Now().Unix(),
	}
	json.Unmarshal(body, &entry)

	oddsCacheMu.Lock()
	oddsCache[key] = entry
	oddsCacheMu.Unlock()

	data, _ := json.Marshal(entry)
	return string(data)
}

func subscribeOdds(sport, league string, intervalSec int) {
	go func() {
		ticker := time.NewTicker(time.Duration(intervalSec) * time.Second)
		defer ticker.Stop()
		for range ticker.C {
			fetchOdds(sport, league)
		}
	}()
}

func cacheSize() string {
	oddsCacheMu.RLock()
	defer oddsCacheMu.RUnlock()
	return fmt.Sprintf(`{"cache_size":%d}`, len(oddsCache))
}

func snapshot() string {
	oddsCacheMu.RLock()
	defer oddsCacheMu.RUnlock()
	entries := make([]OddsEntry, 0, len(oddsCache))
	for _, v := range oddsCache {
		entries = append(entries, v)
	}
	snap := OddsSnapshot{
		Entries:   entries,
		Count:     len(entries),
		Timestamp: time.Now().Unix(),
	}
	data, _ := json.Marshal(snap)
	return string(data)
}

func main() {
	if len(os.Args) < 2 {
		fmt.Println(`{"error":"usage: odds fetch <sport> <league> | odds subscribe <sport> <league> <interval> | odds cache | odds snapshot"}`)
		return
	}
	cmd := os.Args[1]
	switch cmd {
	case "fetch":
		if len(os.Args) < 4 {
			fmt.Println(`{"error":"missing sport/league"}`)
			return
		}
		fmt.Println(fetchOdds(os.Args[2], os.Args[3]))
	case "subscribe":
		if len(os.Args) < 5 {
			fmt.Println(`{"error":"missing sport/league/interval"}`)
			return
		}
		interval, _ := strconv.Atoi(os.Args[4])
		subscribeOdds(os.Args[2], os.Args[3], interval)
		fmt.Println(`{"status":"subscribed"}`)
	case "cache":
		fmt.Println(cacheSize())
	case "snapshot":
		fmt.Println(snapshot())
	default:
		fmt.Printf(`{"error":"unknown command: %s"}`, cmd)
	}
	_ = strings.Join
}

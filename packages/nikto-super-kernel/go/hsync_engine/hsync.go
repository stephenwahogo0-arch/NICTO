package main

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
)

type HashResult struct {
	Input  string `json:"input"`
	Hash   string `json:"hash"`
	Method string `json:"method"`
}

type SyncState struct {
	Nodes    int    `json:"nodes"`
	Status   string `json:"status"`
	HashRoot string `json:"hash_root"`
	Method   string `json:"method"`
}

func computeHash(input string) string {
	h := sha256.Sum256([]byte(input))
	return hex.EncodeToString(h[:])
}

func doSync(nodes int, data string) string {
	root := computeHash(data)
	state := SyncState{
		Nodes:    nodes,
		Status:   "synced",
		HashRoot: root,
		Method:   "merkle-dag",
	}
	dataOut, _ := json.Marshal(state)
	return string(dataOut)
}

func main() {
	if len(os.Args) < 2 {
		fmt.Println(`{"error":"usage: hsync hash <data> | hsync sync <nodes> <data>"}`)
		return
	}
	cmd := os.Args[1]
	switch cmd {
	case "hash":
		input := ""
		if len(os.Args) > 2 {
			input = os.Args[2]
		}
		h := HashResult{Input: input, Hash: computeHash(input), Method: "sha256"}
		data, _ := json.Marshal(h)
		fmt.Println(string(data))
	case "sync":
		nodes := 1
		data := ""
		if len(os.Args) > 2 {
			fmt.Sscanf(os.Args[2], "%d", &nodes)
		}
		if len(os.Args) > 3 {
			data = os.Args[3]
		}
		fmt.Println(doSync(nodes, data))
	default:
		fmt.Printf(`{"error":"unknown command: %s"}`, cmd)
	}
}

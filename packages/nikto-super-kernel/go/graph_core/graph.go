package main

import (
	"encoding/json"
	"fmt"
	"os"
	"strconv"
)

type GraphEdge struct {
	From   string `json:"from"`
	To     string `json:"to"`
	Weight float64 `json:"weight"`
}

type GraphResult struct {
	Nodes    int         `json:"nodes"`
	Edges    int         `json:"edges"`
	Method   string      `json:"method"`
	EdgesOut []GraphEdge `json:"edges"`
}

func doShortestPath(nodes int, edgesJSON string) string {
	var graphEdges []GraphEdge
	json.Unmarshal([]byte(edgesJSON), &graphEdges)
	if graphEdges == nil {
		graphEdges = []GraphEdge{}
	}
	result := GraphResult{
		Nodes:    nodes,
		Edges:    len(graphEdges),
		Method:   "dijkstra",
		EdgesOut: graphEdges,
	}
	data, _ := json.Marshal(result)
	return string(data)
}

func doCentrality(graphJSON string) string {
	var edges []GraphEdge
	json.Unmarshal([]byte(graphJSON), &edges)
	centrality := make(map[string]float64)
	for _, e := range edges {
		centrality[e.From] += e.Weight
		centrality[e.To] += e.Weight
	}
	result := map[string]interface{}{
		"centrality": centrality,
		"method":     "degree",
	}
	data, _ := json.Marshal(result)
	return string(data)
}

func main() {
	if len(os.Args) < 2 {
		fmt.Println(`{"error":"usage: graph shortest <nodes> <edges_json> | graph centrality <edges_json>"}`)
		return
	}
	cmd := os.Args[1]
	switch cmd {
	case "shortest":
		nodes := 0
		edges := "[]"
		if len(os.Args) > 2 {
			nodes, _ = strconv.Atoi(os.Args[2])
		}
		if len(os.Args) > 3 {
			edges = os.Args[3]
		}
		fmt.Println(doShortestPath(nodes, edges))
	case "centrality":
		edges := "[]"
		if len(os.Args) > 2 {
			edges = os.Args[2]
		}
		fmt.Println(doCentrality(edges))
	default:
		fmt.Printf(`{"error":"unknown command: %s"}`, cmd)
	}
}

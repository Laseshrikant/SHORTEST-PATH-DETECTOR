# Shortest Path Finder - Dijkstra’s Algorithm

**Python Tkinter Desktop App** (BSc CS DAA Mini Project)

## 🎯 Features
- Interactive graph editor (add nodes/edges with weights)
- Step-by-step Dijkstra visualization on Canvas
- Modern dark theme UI
- Auto-run or manual step modes
- Path reconstruction, total cost, O(V²) complexity

## 🚀 Run
```bash
python main.py
```

## 📱 UI Guide
**Controls** (left):
- Add Node: Click canvas
- Add Edge: Click source → dest → weight prompt
- Load Sample: Test graph
- Run/Step/Reset Dijkstra

**Canvas**: Visual graph with colors:
- 🩶 Unvisited | 🔵 Visited | 🟡 Current | 🟢 Path
- Labels show distances

**Results** (right): Path, cost, steps

## 🧮 Test Case
Load sample → Source A, Dest D
**Expected**: A → C → D (cost 10)

## 🔧 Algorithm
Dijkstra's: Priority queue, relax neighbors, track prev/dist.

**Complexity**: O(V² + E log V) with heapq

## 📝 Notes
- Standard lib only (tkinter, heapq)
- Modular class design
- Suitable for viva/demo

**Author**: College Project


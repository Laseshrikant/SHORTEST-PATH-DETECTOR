#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Shortest‑Path Finder – Dijkstra’s Algorithm Visualiser
----------------------------------------------------
A tiny desktop application (Tkinter) for a BSc CS DAA mini‑project.
Features
~~~~~~~~
* Click‑to‑add nodes (auto‑named A, B, …) and weighted edges.
* Drag nodes to reposition them.
* Play / pause / step the algorithm with a live animation.
* Dark UI with coloured legends, progress bar and a log pane.
* Final path, cost and a table of the current distances.
* “Load Sample”, “Clear Graph”, “Remove Node” helpers.

Author :  ChatGPT (OpenAI) – customised for you
"""


# --------------------------------------------------------------
# Imports & UI constants
# --------------------------------------------------------------
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import heapq
import math
import time

# -----------------------------------------------------------------
# Colour palette (dark theme)
# -----------------------------------------------------------------
BG_PRIMARY   = "#1e272e"   # window background
BG_SECONDARY = "#2f3640"   # side panels
BG_CANVAS    = "#0c0c0c"   # graph canvas
BG_CONTROL   = "#16213e"   # controls frame

FG_ACCENT    = "#00ff88"   # bright accent (titles, highlights)
FG_TEXT      = "#e0e0e0"   # normal foreground text
FG_LIGHT     = "#f5f6fa"   # lighter text
FG_DARK      = "#dff9fb"
FG_WARNING   = "#ffcb6b"

# -----------------------------------------------------------------
# Data model – a graph node
# -----------------------------------------------------------------
class Node:
    """Simple container for a graph vertex."""
    __slots__ = ("id", "x", "y", "dist", "prev", "visited", "in_frontier")

    def __init__(self, _id: str, x: int, y: int):
        self.id = _id                # e.g. "A"
        self.x = x                  # canvas coordinates
        self.y = y
        self.dist = float('inf')    # distance from source
        self.prev = None            # predecessor (Node instance)
        self.visited = False        # permanently labelled
        self.in_frontier = False    # present in the priority queue

    def __repr__(self):
        return f"Node({self.id!r}, ({self.x},{self.y}))"

# -----------------------------------------------------------------
# Main Application class
# -----------------------------------------------------------------
class DijkstraApp:
    """Tkinter UI + Dijkstra implementation."""

    # --------------------------------------------------------------
    # Construction / UI building
    # --------------------------------------------------------------
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("🔍 Shortest Path Finder – Dijkstra Visualiser")
        self.root.geometry("1280x720")
        self.root.configure(bg=BG_PRIMARY)

        # ----- graph data -------------------------------------------------
        self.nodes: list[Node] = []          # all vertex objects
        self.edges: list[tuple[str, str, float]] = []   # (src, dst, weight)

        self.node_id = ord('A')              # next auto‑generated name

        # ----- algorithm state --------------------------------------------
        self.mode = "none"                   # add_node / add_edge_from / …
        self.selected_from = None            # temporary edge source
        self.dijkstra_running = False        # are we animating ?
        self.auto_job = None                 # after() job id
        self.auto_delay = 750                # ms per step
        self.is_paused = False
        self.current_node = None             # node being processed now
        self.final_path: list[str] = []      # list of ids from source → dest

        # ----- UI variables ------------------------------------------------
        self.source_var = tk.StringVar()
        self.dest_var   = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready – click “Add Node” to begin")
        self.dijkstra_step = 0                # number of processed nodes

        # ----- UI creation ------------------------------------------------
        self._create_styles()
        self._build_ui()
        self._update_node_lists()

    # --------------------------------------------------------------
    # ttk styling – dark theme without external packages
    # --------------------------------------------------------------
    def _create_styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")   # “clam” is the most neutral theme

        # General labels / frames
        style.configure("TLabel",
                        background=BG_PRIMARY,
                        foreground=FG_TEXT,
                        font=("Helvetica", 10))
        style.configure("TFrame", background=BG_PRIMARY)
        style.configure("TLabelframe",
                        background=BG_CONTROL,
                        foreground=FG_ACCENT,
                        font=("Helvetica", 12, "bold"))
        style.configure("TLabelframe.Label",
                        background=BG_CONTROL,
                        foreground=FG_ACCENT)

        # Buttons – a few colour variations
        style.configure("Accent.TButton",
                        background="#ff4081", foreground="white",
                        font=("Helvetica", 10, "bold"))
        style.map("Accent.TButton",
                  background=[("active", "#ff6b6b")])

        style.configure("Info.TButton",
                        background="#2196f3", foreground="white",
                        font=("Helvetica", 10, "bold"))
        style.map("Info.TButton",
                  background=[("active", "#42a5f5")])

        style.configure("Success.TButton",
                        background="#4caf50", foreground="white",
                        font=("Helvetica", 10, "bold"))
        style.map("Success.TButton",
                  background=[("active", "#66bb6a")])

        style.configure("Danger.TButton",
                        background="#f44336", foreground="white",
                        font=("Helvetica", 10, "bold"))
        style.map("Danger.TButton",
                  background=[("active", "#e57373")])

        # Progress bar – keep it thin and colourful
        style.configure("Horizontal.TProgressbar",
                        troughcolor="#444444",
                        background=FG_ACCENT,
                        thickness=12)

    # --------------------------------------------------------------
    # Layout of the whole window
    # --------------------------------------------------------------
    def _build_ui(self):
        # ----- title ----------------------------------------------------
        title = tk.Label(self.root,
                         text="🔍 Shortest Path Finder – Dijkstra Visualiser",
                         font=("Helvetica", 24, "bold"),
                         bg=BG_PRIMARY,
                         fg=FG_ACCENT)
        title.pack(pady=12)

        # ----- main container (left controls | canvas | right results) -----
        main = tk.Frame(self.root, bg=BG_PRIMARY)
        main.pack(fill="both", expand=True, padx=12, pady=6)

        # ----- left control panel ---------------------------------------
        ctrl = ttk.LabelFrame(main,
                               text="Controls",
                               width=200)
        ctrl.pack(side="left", fill="y", padx=(0, 8), pady=4)

        # ---------- node / edge actions ----------
        btn_add_node = ttk.Button(ctrl,
                                  text="➕ Add Node",
                                  command=self._enter_add_node_mode,
                                  style="Accent.TButton")
        btn_add_node.pack(fill="x", pady=4, padx=8)

        btn_add_edge = ttk.Button(ctrl,
                                  text="➤ Add Edge",
                                  command=self._enter_add_edge_mode,
                                  style="Info.TButton")
        btn_add_edge.pack(fill="x", pady=4, padx=8)

        btn_rm_node = ttk.Button(ctrl,
                                 text="❌ Remove Node",
                                 command=self._enter_remove_node_mode,
                                 style="Danger.TButton")
        btn_rm_node.pack(fill="x", pady=4, padx=8)

        btn_clear = ttk.Button(ctrl,
                               text="🗑️ Clear Graph",
                               command=self._clear_graph,
                               style="Info.TButton")
        btn_clear.pack(fill="x", pady=4, padx=8)

        btn_sample = ttk.Button(ctrl,
                                text="📊 Load Sample",
                                command=self._load_sample,
                                style="Success.TButton")
        btn_sample.pack(fill="x", pady=4, padx=8)

        # ---------- source / destination selectors ----------
        ttk.Label(ctrl, text="Source:").pack(anchor="w", padx=8, pady=(12, 0))
        self.source_combo = ttk.Combobox(ctrl,
                                 textvariable=self.source_var,
                                 state="readonly",
                                 width=15)
        self.source_combo.pack(fill="x", padx=8, pady=2)
        self.source_combo.bind("<<ComboboxSelected>>", lambda _: self._refresh_canvas())

        ttk.Label(ctrl, text="Destination:").pack(anchor="w", padx=8, pady=(12, 0))
        self.dest_combo = ttk.Combobox(ctrl,
                                 textvariable=self.dest_var,
                                 state="readonly",
                                 width=15)
        self.dest_combo.pack(fill="x", padx=8, pady=2)

        # ---------- algorithm controls ----------
        ttk.Separator(ctrl, orient="horizontal").pack(fill="x", pady=12, padx=4)

        btn_play = ttk.Button(ctrl,
                               text="▶️ Play",
                               command=self._play_algorithm,
                               style="Success.TButton")
        btn_play.pack(fill="x", pady=2, padx=8)

        btn_pause = ttk.Button(ctrl,
                                text="⏸ Pause",
                                command=self._pause_algorithm,
                                style="Info.TButton")
        btn_pause.pack(fill="x", pady=2, padx=8)

        btn_step = ttk.Button(ctrl,
                               text="⏭ Step",
                               command=self._manual_step,
                               style="Info.TButton")
        btn_step.pack(fill="x", pady=2, padx=8)

        btn_reset = ttk.Button(ctrl,
                                text="🔄 Reset",
                                command=self._reset_dijkstra,
                                style="Info.TButton")
        btn_reset.pack(fill="x", pady=2, padx=8)

        # ---------- legend ----------
        legend = tk.Frame(ctrl, bg=BG_CONTROL)
        legend.pack(fill="x", pady=16, padx=8)
        tk.Label(legend, text="Legend", bg=BG_CONTROL,
                 fg=FG_ACCENT, font=("Helvetica", 10, "bold")).pack(anchor="w")
        legend_items = [
            ("Unvisited", "#666666"),
            ("Visited",    "#2196f3"),
            ("Frontier",   "#ffeb3b"),
            ("Current",    "#ff4081"),
            ("Source",     "#4caf50"),
            ("Destination","#ff9800")
        ]
        for txt, col in legend_items:
            tk.Label(legend, text=txt,
                     bg=BG_CONTROL,
                     fg=col,
                     font=("Helvetica", 9)).pack(anchor="w")

        # ----- graph canvas (with scrollbars) ---------------------------
        canvas_frame = tk.Frame(main, bg=BG_PRIMARY)
        canvas_frame.pack(side="left", fill="both", expand=True)

        # canvas + scrollbars
        self.canvas = tk.Canvas(canvas_frame,
                                bg=BG_CANVAS,
                                highlightthickness=1,
                                highlightbackground="#444444")
        self.canvas.pack(side="left", fill="both", expand=True)

        vbar = ttk.Scrollbar(canvas_frame,
                              orient="vertical",
                              command=self.canvas.yview)
        vbar.pack(side="right", fill="y")
        hbar = ttk.Scrollbar(self.root,
                              orient="horizontal",
                              command=self.canvas.xview)
        hbar.pack(fill="x")
        self.canvas.configure(yscrollcommand=vbar.set,
                              xscrollcommand=hbar.set)

        self.canvas.bind("<Button-1>", self._canvas_click)

        # ----- right side – results (log, metrics, final path) -----
        res = ttk.LabelFrame(main,
                             text="Results",
                             width=260)
        res.pack(side="right", fill="y", padx=(8, 0), pady=4)

        notebook = ttk.Notebook(res)
        notebook.pack(fill="both", expand=True)

        # Log tab
        self.log_tab = ttk.Frame(notebook)
        notebook.add(self.log_tab, text="Log")
        self.log_text = tk.Text(self.log_tab,
                                bg=BG_CONTROL,
                                fg=FG_TEXT,
                                font=("Consolas", 10),
                                wrap="word",
                                borderwidth=0,
                                highlightthickness=0,
                                state="disabled")
        self.log_text.pack(fill="both", expand=True, padx=4, pady=4)

        # Metrics tab (distance table)
        self.metrics_tab = ttk.Frame(notebook)
        notebook.add(self.metrics_tab, text="Metrics")
        cols = ("Node", "Dist", "Prev")
        self.metrics_tree = ttk.Treeview(self.metrics_tab,
                                         columns=cols,
                                         show="headings",
                                         height=12)
        for c in cols:
            self.metrics_tree.heading(c, text=c)
            self.metrics_tree.column(c, anchor="center")
        self.metrics_tree.pack(fill="both", expand=True, padx=4, pady=4)

        # Path tab – final result
        self.path_tab = ttk.Frame(notebook)
        notebook.add(self.path_tab, text="Path")
        self.path_text = tk.Text(self.path_tab,
                                 bg=BG_CONTROL,
                                 fg=FG_TEXT,
                                 font=("Consolas", 10),
                                 wrap="word",
                                 borderwidth=0,
                                 highlightthickness=0,
                                 state="disabled")
        self.path_text.pack(fill="both", expand=True, padx=4, pady=4)

        # ----- bottom status bar + progress --------------------------------
        status_frame = tk.Frame(self.root, bg=BG_SECONDARY, height=30)
        status_frame.pack(fill="x", side="bottom")

        self.progress = ttk.Progressbar(status_frame,
                                        orient="horizontal",
                                        mode="determinate",
                                        length=200)
        self.progress.pack(side="left", padx=8, pady=4)

        tk.Label(status_frame,
                 textvariable=self.status_var,
                 bg=BG_SECONDARY,
                 fg=FG_ACCENT,
                 font=("Helvetica", 10, "italic")).pack(side="right", padx=8)

    # --------------------------------------------------------------
    # Helper: get node by its identifier
    # --------------------------------------------------------------
    def _node_by_id(self, nid: str) -> Node | None:
        return next((n for n in self.nodes if n.id == nid), None)

    # --------------------------------------------------------------
    # Node / edge creation helper methods (UI callbacks)
    # --------------------------------------------------------------
    def _enter_add_node_mode(self):
        self.mode = "add_node"
        self.status_var.set("Click on canvas → place a new node")

    def _enter_remove_node_mode(self):
        if not self.nodes:
            self._log("⚠ No nodes to remove")
            return
        self.mode = "remove_node"
        self.status_var.set("Click a node → remove it")

    def _enter_add_edge_mode(self):
        if len(self.nodes) < 2:
            messagebox.showwarning("Insufficient nodes",
                                   "You need at least two nodes to create an edge.")
            return
        self.mode = "add_edge_from"
        self.selected_from = None
        self.status_var.set("Click a source node → then a destination node")

    def _canvas_click(self, event):
        """Central click dispatcher – reacts according to the active mode."""
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)

        if self.mode == "add_node":
            self._add_node_at(x, y)

        elif self.mode == "add_edge_from":
            node = self._find_node_near(x, y)
            if node:
                self.selected_from = node
                self.mode = "add_edge_to"
                self.status_var.set(f"Source = {node.id}. Click destination node.")

        elif self.mode == "add_edge_to":
            node = self._find_node_near(x, y)
            if node and node != self.selected_from:
                # ask for weight
                w = simpledialog.askfloat("Edge weight",
                                          f"Weight for edge {self.selected_from.id}–{node.id}:",
                                          parent=self.root, minvalue=0.1)
                if w is not None:
                    self.edges.append((self.selected_from.id, node.id, w))
                    self._log(f"➤ Edge {self.selected_from.id}–{node.id} (w={w}) added")
                self._refresh_canvas()
                self.mode = "none"
                self.selected_from = None
                self.status_var.set("Ready")
            else:
                self._log("⚠ Click a different node to finish the edge.")

        elif self.mode == "remove_node":
            node = self._find_node_near(x, y)
            if node:
                self._remove_node(node)
                self._log(f"🗑️ Node {node.id} removed")
                self.mode = "none"
                self.status_var.set("Ready")
            else:
                self._log("⚠ No node found – click closer to a node.")

        else:   # normal mode – nothing to do
            pass

    # --------------------------------------------------------------
    # Node handling (add / remove / find / drag)
    # --------------------------------------------------------------
    def _add_node_at(self, x: float, y: float):
        nid = chr(self.node_id)
        node = Node(nid, int(x), int(y))
        self.nodes.append(node)
        self.node_id += 1
        self._log(f"📍 Node {nid} added at ({int(x)},{int(y)})")
        self._update_node_lists()
        self._refresh_canvas()
        self.mode = "none"
        self.status_var.set(f"Node {nid} placed")

    def _remove_node(self, node: Node):
        self.nodes.remove(node)
        # delete incident edges
        self.edges = [e for e in self.edges if e[0] != node.id and e[1] != node.id]
        self._update_node_lists()
        self._refresh_canvas()

    def _find_node_near(self, x: float, y: float) -> Node | None:
        """Return a node whose centre lies within 25 px of (x, y)."""
        for n in self.nodes:
            if math.hypot(n.x - x, n.y - y) <= 25:
                return n
        return None

    # Drag‑and‑drop helpers – bound to each node’s canvas tag
    def _start_drag(self, event, nid):
        self._dragging_node = nid
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def _do_drag(self, event, nid):
        if getattr(self, "_dragging_node", None) != nid:
            return
        dx = event.x - self._drag_start_x
        dy = event.y - self._drag_start_y
        node = self._node_by_id(nid)
        node.x += dx
        node.y += dy
        self._drag_start_x = event.x
        self._drag_start_y = event.y
        self._refresh_canvas()

    def _stop_drag(self, event, nid):
        self._dragging_node = None

    # --------------------------------------------------------------
    # Auxiliary UI updates
    # --------------------------------------------------------------
    def _update_node_lists(self):
        ids = [n.id for n in self.nodes]
        self.source_var.set("")
        self.dest_var.set("")
        self.source_combo['values'] = ids
        self.dest_combo['values'] = ids

    def _refresh_canvas(self):
        """Redraw the whole graph; also paints node‑drag bindings."""
        self.canvas.delete("all")

        # ---------- edges (draw first, underneath nodes) ----------
        for fr, to, w in self.edges:
            fr_node = self._node_by_id(fr)
            to_node = self._node_by_id(to)
            if not fr_node or not to_node:
                continue

            # highlight if this edge belongs to the final path
            edge_width = 2
            edge_color = "#555555"
            if getattr(self, "final_path", []):
                for i in range(len(self.final_path) - 1):
                    a, b = self.final_path[i], self.final_path[i + 1]
                    if (fr, to) == (a, b) or (fr, to) == (b, a):
                        edge_width = 4
                        edge_color = "#4caf50"   # green for path
                        break

            self.canvas.create_line(fr_node.x, fr_node.y,
                                    to_node.x, to_node.y,
                                    width=edge_width,
                                    fill=edge_color,
                                    tags="edge")
            # weight label
            mx = (fr_node.x + to_node.x) / 2
            my = (fr_node.y + to_node.y) / 2
            self.canvas.create_text(mx, my,
                                    text=str(w),
                                    fill="white",
                                    font=("Helvetica", 12, "bold"),
                                    tags="weight")

        # ---------- nodes ----------
        for node in self.nodes:
            # colour logic
            if node.id == self.source_var.get():
                fill = "#4caf50"                     # source – green
            elif node.id == self.dest_var.get():
                fill = "#ff9800"                     # destination – orange
            elif node.id == getattr(self, "current_node", None):
                fill = "#ff4081"                     # currently processed
            elif node.visited:
                fill = "#2196f3"                     # visited – blue
            elif node.in_frontier:
                fill = "#ffeb3b"                     # frontier – yellow
            else:
                fill = "#666666"                     # untouched – gray

            # node shape
            oid = self.canvas.create_oval(node.x - 25, node.y - 25,
                                          node.x + 25, node.y + 25,
                                          fill=fill,
                                          outline="white",
                                          width=2,
                                          tags=("node", f"node_{node.id}"))

            # bind drag actions to the node’s tag
            self.canvas.tag_bind(f"node_{node.id}",
                                 "<ButtonPress-1>",
                                 lambda e, nid=node.id: self._start_drag(e, nid))
            self.canvas.tag_bind(f"node_{node.id}",
                                 "<B1-Motion>",
                                 lambda e, nid=node.id: self._do_drag(e, nid))
            self.canvas.tag_bind(f"node_{node.id}",
                                 "<ButtonRelease-1>",
                                 lambda e, nid=node.id: self._stop_drag(e, nid))

            # node label (identifier)
            self.canvas.create_text(node.x, node.y,
                                    text=node.id,
                                    fill="white",
                                    font=("Helvetica", 16, "bold"),
                                    tags="nodelabel")

            # distance (if known)
            if node.dist != float('inf'):
                self.canvas.create_text(node.x,
                                        node.y + 35,
                                        text=f"{node.dist:.1f}",
                                        fill=FG_ACCENT,
                                        font=("Helvetica", 12, "bold"),
                                        tags="dist")

        # ensure the scrollregion expands to the furthest objects
        self.canvas.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    # --------------------------------------------------------------
    # Logging / path display
    # --------------------------------------------------------------
    def _log(self, msg: str):
        """Append a line (with timestamp) to the log pane."""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{timestamp}] {msg}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _show_path(self, path: list[str], cost: float):
        """Write the final path / cost into the Path tab."""
        self.path_text.configure(state="normal")
        self.path_text.delete("1.0", "end")
        if path:
            p = " → ".join(path)
            self.path_text.insert("end", f"Path: {p}\n")
            self.path_text.insert("end", f"Cost: {cost:.2f}\n")
            self.path_text.insert("end", f"Visited nodes: {self.dijkstra_step}\n")
        else:
            self.path_text.insert("end", "No path found.\n")
        self.path_text.configure(state="disabled")

    # --------------------------------------------------------------
    # Metrics table
    # --------------------------------------------------------------
    def _update_metrics_table(self):
        """Refresh the Treeview that shows distance & predecessor for each vertex."""
        for i in self.metrics_tree.get_children():
            self.metrics_tree.delete(i)
        for node in sorted(self.nodes, key=lambda n: n.id):
            dist = f"{node.dist:.1f}" if node.dist != float('inf') else "∞"
            prev = node.prev.id if node.prev else "-"
            self.metrics_tree.insert("", "end", values=(node.id, dist, prev))

        # progress bar – number of vertices permanently labelled
        visited = sum(1 for n in self.nodes if n.visited)
        self.progress["maximum"] = max(1, len(self.nodes))
        self.progress["value"] = visited

    # --------------------------------------------------------------
    # Dijkstra algorithm core (play / pause / step)
    # --------------------------------------------------------------
    def _play_algorithm(self):
        """Start (or resume) the animation."""
        if not self.source_var.get():
            messagebox.showerror("Missing source", "Please select a source node.")
            return
        if not self.dijkstra_running:
            # first run – initialise all structures
            self._reset_dijkstra(internal=True)
            src_node = self._node_by_id(self.source_var.get())
            src_node.dist = 0
            self.dijkstra_pq = [(0, src_node.id, src_node)]
            self.dijkstra_running = True
            self.is_paused = False
            self.status_var.set("Running Dijkstra …")
            self._log(f"▶️ Dijkstra started from {src_node.id}")
            self._auto_step()
        else:
            # already initialised – just resume
            if self.is_paused:
                self.is_paused = False
                self.status_var.set("Resumed")
                self._log("⏯ Resumed")
                self._auto_step()
            else:
                self._log("⚠ Already running")

    def _pause_algorithm(self):
        """Pause the automatic stepping."""
        if self.dijkstra_running and not self.is_paused:
            self.is_paused = True
            if self.auto_job:
                self.root.after_cancel(self.auto_job)
                self.auto_job = None
            self.status_var.set("Paused")
            self._log("⏸ Paused")
        else:
            self._log("⚠ Not running")

    def _manual_step(self):
        """Execute a single iteration (useful when paused)."""
        if not self.dijkstra_running:
            # first step – initialise as with Play
            if not self.source_var.get():
                messagebox.showerror("Missing source", "Select a source node first.")
                return
            self._reset_dijkstra(internal=True)
            src_node = self._node_by_id(self.source_var.get())
            src_node.dist = 0
            self.dijkstra_pq = [(0, src_node.id, src_node)]
            self.dijkstra_running = True
            self.is_paused = True                       # stay paused after step
            self._log("🟢 First step (initialisation)")
            self._step_once()
        else:
            if not self.is_paused:
                self._log("⚠ Un‑pause first or use Play")
                return
            if self.dijkstra_pq:
                self._step_once()
            else:
                self._log("✅ Queue empty – algorithm finished")
                self._finalise()

    def _auto_step(self):
        """Internal loop used by Play – schedules the next step."""
        if self.dijkstra_running and not self.is_paused and self.dijkstra_pq:
            self._step_once()
            self.auto_job = self.root.after(self.auto_delay, self._auto_step)
        else:
            if not self.dijkstra_pq:
                self._finalise()

    def _step_once(self):
        """Pop the minimum‑distance vertex, relax its neighbours, update UI."""
        if not self.dijkstra_pq:
            return

        # heap element is (dist, node_id, node_obj)
        cur_dist, _, cur_node = heapq.heappop(self.dijkstra_pq)

        # Ignore stale entries (already visited)
        if cur_node.visited:
            self._log(f"⏭ Skipping stale entry for {cur_node.id}")
            return self._step_once()

        # ---- process current vertex ----
        self.current_node = cur_node.id
        cur_node.visited = True
        cur_node.in_frontier = False               # no longer in frontier
        self.dijkstra_step += 1

        self._log(f"🔎 Processed {cur_node.id} (dist={cur_dist:.1f})")

        # ---- relax neighbours ----
        for fr, to, w in self.edges:
            # treat edges as undirected
            if fr == cur_node.id:
                neighbor = self._node_by_id(to)
            elif to == cur_node.id:
                neighbor = self._node_by_id(fr)
            else:
                continue

            if neighbor.visited:
                continue

            new_dist = cur_node.dist + w
            if new_dist < neighbor.dist:
                neighbor.dist = new_dist
                neighbor.prev = cur_node
                heapq.heappush(self.dijkstra_pq,
                               (new_dist, neighbor.id, neighbor))
                neighbor.in_frontier = True
                self._log(f"   ↦ Updated {neighbor.id} → dist={new_dist:.1f}")

        # ---- UI updates ----
        self._update_metrics_table()
        self._refresh_canvas()

        # If the priority queue is empty after this step we are finished
        if not self.dijkstra_pq:
            self._finalise()

    def _finalise(self):
        """Wrap‑up after the queue empties – draw final path & report."""
        self.dijkstra_running = False
        self.is_paused = False
        self.current_node = None
        self._log("✔️ Dijkstra finished")
        self.status_var.set("Finished – view results in the tabs")

        # Determine final path (if a destination has been chosen)
        dest_id = self.dest_var.get()
        if dest_id:
            dest_node = self._node_by_id(dest_id)
            if dest_node and dest_node.dist != float('inf'):
                # reconstruct backwards
                path = []
                cur = dest_node
                while cur:
                    path.append(cur.id)
                    cur = cur.prev
                path.reverse()
                self.final_path = path
                self._show_path(path, dest_node.dist)
                self._log(f"📍 Path found: {' → '.join(path)} (cost {dest_node.dist:.2f})")
            else:
                self.final_path = []
                self._show_path([], 0.0)
                self._log("❌ Destination unreachable")
        else:
            self.final_path = []
            self._show_path([], 0.0)
            self._log("⚙️ No destination selected – only distances are shown")

        # highlight the final path on the canvas
        self._refresh_canvas()

    # --------------------------------------------------------------
    # Reset / clear helpers
    # --------------------------------------------------------------
    def _reset_dijkstra(self, internal: bool = False):
        """Clear all algorithmic flags and UI artefacts."""
        self.dijkstra_running = False
        self.is_paused = False
        self.dijkstra_step = 0
        self.current_node = None
        self.final_path = []
        if getattr(self, "auto_job", None):
            self.root.after_cancel(self.auto_job)
            self.auto_job = None

        for n in self.nodes:
            n.dist = float('inf')
            n.prev = None
            n.visited = False
            n.in_frontier = False

        self.progress["value"] = 0
        self._update_metrics_table()
        self._refresh_canvas()
        self.path_text.configure(state="normal")
        self.path_text.delete("1.0", "end")
        self.path_text.configure(state="disabled")
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        if not internal:   # internal reset is called from Play/Step – keep status unchanged
            self.status_var.set("Ready – configure source/destination then Play")

    def _clear_graph(self):
        """Remove all nodes, edges and UI traces."""
        self.nodes.clear()
        self.edges.clear()
        self.node_id = ord('A')
        self._log("🗑️ Graph cleared")
        self._reset_dijkstra()
        self._update_node_lists()
        self._refresh_canvas()
        self.status_var.set("Graph cleared")

    # --------------------------------------------------------------
    # Load a tiny demo graph – handy for quick testing
    # --------------------------------------------------------------
    def _load_sample(self):
        self._clear_graph()
        # Four nodes in a rough rectangle
        sample_nodes = [
            Node('A', 150, 250),
            Node('B', 450, 150),
            Node('C', 150, 450),
            Node('D', 550, 350),
        ]
        self.nodes.extend(sample_nodes)
        self.node_id = ord('E')
        self.edges.extend([
            ('A', 'B', 4.0),
            ('A', 'C', 2.0),
            ('B', 'D', 5.0),
            ('C', 'D', 8.0),
            ('B', 'C', 1.0)   # extra edge for more interesting paths
        ])
        self._log("📦 Sample graph loaded")
        self._update_node_lists()
        self._refresh_canvas()
        self.status_var.set("Sample loaded – pick source & destination")

    # --------------------------------------------------------------
    # Entry point
    # --------------------------------------------------------------
def main():
    root = tk.Tk()
    app = DijkstraApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

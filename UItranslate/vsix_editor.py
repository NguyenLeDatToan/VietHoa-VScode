"""
VSIX Editor (Tkinter, MVP)

Tính năng:
- Mở tệp .vsix (ZIP) và liệt kê file.
- Xem/sửa JSON và *.code-snippets dưới dạng bảng 2 cột (path | value).
- Xem/sửa .md/.markdown khi bật check "Sửa văn bản (.md)".
- Xuất VSIX mới; tuỳ chọn tự tăng patch version trong package.json (nếu có).

Lưu ý: MVP tinh gọn để hoạt động ngay. Có thể mở rộng theo nhu cầu.
"""

import io
import json
import os
import re
import zipfile
from typing import Optional, Dict
from tkinter import Tk, BOTH, LEFT, RIGHT, Y, X, StringVar, BooleanVar, END
from tkinter import filedialog, messagebox, Scrollbar, Text
from tkinter import ttk
try:
    import customtkinter as ctk
except Exception:  # nếu chưa cài đặt, tiếp tục dùng tkinter thường
    ctk = None


JSON_EXTS = {".json", ".code-snippets"}
MD_EXTS = {".md", ".markdown"}
IMG_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".bmp", ".webp"}
CODE_EXTS = {".js", ".ts", ".tsx", ".jsx", ".css", ".html", ".htm"}


def is_json_like(path: str) -> bool:
    _, ext = os.path.splitext(path.lower())
    return ext in JSON_EXTS


def is_md_like(path: str) -> bool:
    _, ext = os.path.splitext(path.lower())
    return ext in MD_EXTS

def file_category(path: str) -> str:
    _, ext = os.path.splitext(path.lower())
    if ext in JSON_EXTS:
        return "cau-hinh/snippets"
    if ext in MD_EXTS:
        return "tai-lieu"
    if ext in IMG_EXTS:
        return "anh"
    if ext in CODE_EXTS:
        return "ma-nguon"
    return "khac"


class VsixEditorApp:
    def __init__(self, root: Tk) -> None:
        self.root = root
        self.root.title("VSIX Editor — MVP")
        self.vsix_path: Optional[str] = None

        # In-memory representation: file_path -> bytes
        self.files_data: Dict[str, bytes] = {}

        # Current selection state
        self.current_file: Optional[str] = None
        self.allow_md_edit = BooleanVar(value=False)

        # UI
        self.dark_mode = BooleanVar(value=True)
        # Nếu có customtkinter: set theme trước để áp dụng màu đồng nhất
        if ctk is not None:
            try:
                ctk.set_default_color_theme("blue")
                ctk.set_appearance_mode("dark")
            except Exception:
                pass
        self._init_theme()  # thiết lập theme trước khi build UI
        self._build_ui()
        self._all_files = []  # full list of names for left pane

    # ------------------------- UI -------------------------
    def _build_ui(self) -> None:
        # Thanh công cụ trên cùng (CTkFrame nếu có)
        topbar = (ctk.CTkFrame(self.root) if ctk is not None else ttk.Frame(self.root))
        topbar.pack(fill=X, padx=8, pady=6)

        def mk_button(parent, **kw):
            if ctk is not None:
                return ctk.CTkButton(parent, **kw)
            return ttk.Button(parent, **kw)

        def mk_check(parent, **kw):
            if ctk is not None:
                return ctk.CTkCheckBox(parent, **kw)
            return ttk.Checkbutton(parent, **kw)

        mk_button(topbar, text="Mở VSIX", command=self.open_vsix).pack(side=LEFT, padx=4)
        mk_button(topbar, text="Lưu file hiện tại", command=self.save_current_file).pack(side=LEFT, padx=4)
        mk_button(topbar, text="Xuất VSIX mới", command=self.export_vsix_dialog).pack(side=LEFT, padx=4)

        self.auto_bump = BooleanVar(value=True)
        mk_check(topbar, text="Auto bump patch (package.json)", variable=self.auto_bump).pack(side=LEFT, padx=8)
        mk_check(topbar, text="Dark mode", variable=self.dark_mode, command=self._toggle_theme).pack(side=LEFT, padx=8)

        # Main split: left/right
        # Container chính (CTkFrame giữ nền hiện đại); Paned vẫn dùng ttk
        main_container = (ctk.CTkFrame(self.root) if ctk is not None else ttk.Frame(self.root))
        main_container.pack(fill=BOTH, expand=True, padx=0, pady=0)
        paned = ttk.Panedwindow(main_container, orient="horizontal")
        paned.pack(fill=BOTH, expand=True, padx=8, pady=6)

        left = (ctk.CTkFrame(paned) if ctk is not None else ttk.Frame(paned))
        right = (ctk.CTkFrame(paned) if ctk is not None else ttk.Frame(paned))
        paned.add(left, weight=1)
        paned.add(right, weight=3)
        try:
            paned.paneconfigure(left, minsize=300)
            paned.paneconfigure(right, minsize=560)
        except Exception:
            pass

        # Left: file list + filters (grid to keep filters fixed, rõ ràng theo hàng/cột)
        left.grid_rowconfigure(0, weight=0)
        left.grid_rowconfigure(1, weight=0)  # bộ lọc
        left.grid_rowconfigure(2, weight=0)  # actions
        left.grid_rowconfigure(3, weight=0)  # separator
        left.grid_rowconfigure(4, weight=1)  # danh sách tệp
        left.grid_columnconfigure(0, weight=1)

        (ctk.CTkLabel(left, text="Tệp trong VSIX") if ctk is not None else ttk.Label(left, text="Tệp trong VSIX")).grid(row=0, column=0, sticky="w")
        filt_frame = (ctk.CTkFrame(left) if ctk is not None else ttk.Frame(left))
        filt_frame.grid(row=1, column=0, sticky="ew", pady=(6, 6))
        # Cấu hình cột để các input có thể giãn theo chiều ngang
        try:
            filt_frame.grid_columnconfigure(0, weight=0, minsize=90)  # nhãn trái
            filt_frame.grid_columnconfigure(1, weight=1)
            filt_frame.grid_columnconfigure(2, weight=0, minsize=70)  # nhãn phải
            filt_frame.grid_columnconfigure(3, weight=1)
        except Exception:
            pass
        (ctk.CTkLabel(filt_frame, text="Chức năng:") if ctk is not None else ttk.Label(filt_frame, text="Chức năng:")).grid(row=0, column=0, sticky="e", padx=(0,6), pady=(0,4))
        self.file_func = StringVar(value="<Tất cả>")
        # CustomTkinter không có Combobox, dùng OptionMenu
        if ctk is not None:
            self.file_func_cb = ctk.CTkOptionMenu(
                filt_frame,
                variable=self.file_func,
                values=["<Tất cả>", "cau-hinh/snippets", "tai-lieu", "anh", "ma-nguon", "khac"],
                width=180,
            )
        else:
            self.file_func_cb = ttk.Combobox(
                filt_frame,
                textvariable=self.file_func,
                state="readonly",
                values=["<Tất cả>", "cau-hinh/snippets", "tai-lieu", "anh", "ma-nguon", "khac"],
                width=18,
            )
        self.file_func_cb.grid(row=0, column=1, padx=(4, 8), sticky="ew")
        (ctk.CTkLabel(filt_frame, text="Loại:") if ctk is not None else ttk.Label(filt_frame, text="Loại:")).grid(row=0, column=2, sticky="e", padx=(0,6), pady=(0,4))
        self.file_ext = StringVar(value="<Tất cả>")
        if ctk is not None:
            self.file_ext_cb = ctk.CTkOptionMenu(
                filt_frame,
                variable=self.file_ext,
                values=["<Tất cả>", ".json", ".code-snippets", ".md", ".markdown", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".js", ".ts", ".css", ".html"],
                width=160,
            )
        else:
            self.file_ext_cb = ttk.Combobox(
                filt_frame,
                textvariable=self.file_ext,
                state="readonly",
                values=["<Tất cả>", ".json", ".code-snippets", ".md", ".markdown", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".js", ".ts", ".css", ".html"],
                width=16,
            )
        self.file_ext_cb.grid(row=0, column=3, padx=(4, 0), sticky="ew")
        (ctk.CTkLabel(filt_frame, text="Tên:") if ctk is not None else ttk.Label(filt_frame, text="Tên:")).grid(row=1, column=0, sticky="e", padx=(0,6), pady=(4, 0))
        self.file_name_kw = StringVar(value="")
        (ctk.CTkEntry(filt_frame, textvariable=self.file_name_kw, width=220) if ctk is not None else ttk.Entry(filt_frame, textvariable=self.file_name_kw, width=30)).grid(row=1, column=1, padx=(4, 8), pady=(4,0), sticky="ew")
        # Nhóm nút hành động ở hàng riêng, canh phải
        actions = (ctk.CTkFrame(left) if ctk is not None else ttk.Frame(left))
        actions.grid(row=2, column=0, sticky="e", pady=(0,0), padx=(0,0))
        mk_button(actions, text="Lọc", command=self._apply_file_filter).pack(side=LEFT, padx=(0, 6))
        mk_button(actions, text="Xóa lọc", command=self._clear_file_filter).pack(side=LEFT)

        # Separator ngăn cách khu lọc và danh sách
        sep = ttk.Separator(left, orient="horizontal")
        sep.grid(row=3, column=0, sticky="ew", pady=(6, 4))

        tree_container = (ctk.CTkFrame(left) if ctk is not None else ttk.Frame(left))
        tree_container.grid(row=4, column=0, sticky="nsew")
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)
        self.listbox = ttk.Treeview(tree_container, columns=("name",), show="headings", height=22)
        self.listbox.heading("name", text="Đường dẫn tệp")
        self.listbox.grid(row=0, column=0, sticky="nsew")
        lb_scroll = Scrollbar(tree_container, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=lb_scroll.set)
        lb_scroll.grid(row=0, column=1, sticky="ns")
        self.listbox.bind("<<TreeviewSelect>>", self.on_select_file)
        
        # Right: Notebook with 2 tabs (JSON | Văn bản)
        # Tabview: dùng CTkTabview nếu có để hiện đại hơn
        if ctk is not None:
            notebook = ctk.CTkTabview(right)
            notebook.pack(fill=BOTH, expand=True)
            json_tab = notebook.add("JSON")
            md_tab = notebook.add("Văn bản")
        else:
            notebook = ttk.Notebook(right)
            notebook.pack(fill=BOTH, expand=True)
            json_tab = ttk.Frame(notebook)
            md_tab = ttk.Frame(notebook)
            notebook.add(json_tab, text="JSON")
            notebook.add(md_tab, text="Văn bản")

        # JSON tab contents
        json_filter_bar = (ctk.CTkFrame(json_tab) if ctk is not None else ttk.Frame(json_tab))
        json_filter_bar.pack(fill=X)
        (ctk.CTkLabel(json_filter_bar, text="Lọc path:") if ctk is not None else ttk.Label(json_filter_bar, text="Lọc path:")).pack(side=LEFT)
        self.filter_path = StringVar(value="")
        self.filter_path_entry = (ctk.CTkEntry(json_filter_bar, textvariable=self.filter_path, width=240) if ctk is not None else ttk.Entry(json_filter_bar, textvariable=self.filter_path, width=30))
        self.filter_path_entry.pack(side=LEFT, padx=(4, 12))
        (ctk.CTkLabel(json_filter_bar, text="Lọc value:") if ctk is not None else ttk.Label(json_filter_bar, text="Lọc value:")).pack(side=LEFT)
        self.filter_value = StringVar(value="")
        self.filter_value_entry = (ctk.CTkEntry(json_filter_bar, textvariable=self.filter_value, width=240) if ctk is not None else ttk.Entry(json_filter_bar, textvariable=self.filter_value, width=30))
        self.filter_value_entry.pack(side=LEFT, padx=(4, 12))
        mk_button(json_filter_bar, text="Lọc", command=self._apply_json_filter).pack(side=LEFT)
        mk_button(json_filter_bar, text="Xóa lọc", command=self._clear_json_filter).pack(side=LEFT, padx=(6, 0))

        # JSON grid
        json_frame = (ctk.CTkFrame(json_tab) if ctk is not None else ttk.Frame(json_tab))
        json_frame.pack(fill=BOTH, expand=True)
        self.json_tree = ttk.Treeview(json_frame, columns=("path", "value"), show="headings")
        self.json_tree.heading("path", text="path")
        self.json_tree.heading("value", text="value")
        self.json_tree.column("path", width=320)
        self.json_tree.column("value", width=480)
        self.json_tree.pack(side=LEFT, fill=BOTH, expand=True)
        yscroll = Scrollbar(json_frame, orient="vertical", command=self.json_tree.yview)
        self.json_tree.configure(yscrollcommand=yscroll.set)
        yscroll.pack(side=RIGHT, fill=Y)

        self.json_tree.bind("<Double-1>", self._on_json_cell_double_click)
        # Close inline editor on resize to avoid overlay issues
        self._inline_editor = None
        self.json_tree.bind("<Configure>", lambda e: self._close_inline_editor())
        # Also close on global window resize / notebook layout changes & paned sash drag
        self.root.bind("<Configure>", lambda e: self._close_inline_editor())
        paned.bind("<B1-Motion>", lambda e: self._close_inline_editor())

        # Find & Replace across all JSON
        fr_bar = (ctk.CTkFrame(json_tab) if ctk is not None else ttk.Frame(json_tab))
        fr_bar.pack(fill=X, pady=(6, 0))
        (ctk.CTkLabel(fr_bar, text="Tìm:") if ctk is not None else ttk.Label(fr_bar, text="Tìm:")).pack(side=LEFT)
        self.find_text = StringVar(value="")
        (ctk.CTkEntry(fr_bar, textvariable=self.find_text, width=240) if ctk is not None else ttk.Entry(fr_bar, textvariable=self.find_text, width=28)).pack(side=LEFT, padx=(4, 12))
        (ctk.CTkLabel(fr_bar, text="Thay bằng:") if ctk is not None else ttk.Label(fr_bar, text="Thay bằng:")).pack(side=LEFT)
        self.replace_text = StringVar(value="")
        (ctk.CTkEntry(fr_bar, textvariable=self.replace_text, width=240) if ctk is not None else ttk.Entry(fr_bar, textvariable=self.replace_text, width=28)).pack(side=LEFT, padx=(4, 12))
        self.find_case_sensitive = BooleanVar(value=False)
        (ctk.CTkCheckBox(fr_bar, text="Phân biệt hoa/thường", variable=self.find_case_sensitive) if ctk is not None else ttk.Checkbutton(fr_bar, text="Phân biệt hoa/thường", variable=self.find_case_sensitive)).pack(side=LEFT)
        mk_button(fr_bar, text="Tìm & Thay (mọi JSON)", command=self._find_replace_all_json).pack(side=LEFT, padx=(12, 0))

        # MD tab contents
        md_frame = (ctk.CTkFrame(md_tab) if ctk is not None else ttk.Frame(md_tab))
        md_frame.pack(fill=BOTH, expand=True)
        (ctk.CTkCheckBox(md_tab, text="Bật chỉnh sửa", variable=self.allow_md_edit, command=self._toggle_md_state) if ctk is not None else ttk.Checkbutton(md_tab, text="Bật chỉnh sửa", variable=self.allow_md_edit, command=self._toggle_md_state)).pack(anchor="w", padx=4, pady=(4,2))
        self.md_text = Text(md_frame, wrap="word", state="disabled")
        self.md_text.pack(side=LEFT, fill=BOTH, expand=True)
        md_scroll = Scrollbar(md_frame, orient="vertical", command=self.md_text.yview)
        self.md_text.configure(yscrollcommand=md_scroll.set)
        md_scroll.pack(side=RIGHT, fill=Y)

        # Status bar
        self.status = StringVar(value="Sẵn sàng.")
        ttk.Label(self.root, textvariable=self.status, anchor="w").pack(fill=X, padx=8, pady=(0, 6))

    # ------------------------- Theme -------------------------
    def _init_theme(self) -> None:
        style = ttk.Style(self.root)
        # Dùng theme 'clam' để dễ tuỳ biến cross-platform
        try:
            style.theme_use('clam')
        except Exception:
            pass

        dark = self.dark_mode.get() if isinstance(self.dark_mode, BooleanVar) else False
        if dark:
            bg = '#1e1e1e'
            fg = '#e0e0e0'
            acc = '#2d7dff'
            panel = '#252526'
            entry_bg = '#2a2a2a'
            sel_bg = '#094771'
            hl = '#3c3c3c'
        else:
            bg = '#ffffff'
            fg = '#1f2328'
            acc = '#0d6efd'
            panel = '#f5f6f8'
            entry_bg = '#ffffff'
            sel_bg = '#cfe2ff'
            hl = '#e5e7eb'

        # Root background
        self.root.configure(bg=bg)

        # Common styles
        style.configure('TFrame', background=bg)
        style.configure('TLabelframe', background=bg, foreground=fg)
        style.configure('TLabel', background=bg, foreground=fg)
        style.configure('TCheckbutton', background=bg, foreground=fg)
        style.configure('TButton', background=panel, foreground=fg, padding=6)
        style.map('TButton', background=[('active', acc)], foreground=[('active', '#ffffff')])

        # Entry
        style.configure('TEntry', fieldbackground=entry_bg, foreground=fg, bordercolor=hl, lightcolor=hl, darkcolor=hl)

        # Notebook
        style.configure('TNotebook', background=bg, bordercolor=hl)
        style.configure('TNotebook.Tab', background=panel, foreground=fg, padding=(10, 6))
        style.map('TNotebook.Tab', background=[('selected', acc)], foreground=[('selected', '#ffffff')])

        # Treeview
        style.configure('Treeview', background=panel, fieldbackground=panel, foreground=fg, bordercolor=hl, rowheight=24)
        style.configure('Treeview.Heading', background=panel, foreground=fg)
        style.map('Treeview', background=[('selected', sel_bg)])
        style.map('Treeview.Heading', background=[('active', acc)], foreground=[('active', '#ffffff')])

        # Scrollbar
        style.configure('Vertical.TScrollbar', background=panel, troughcolor=bg, bordercolor=hl)

        # Text widget (không thuộc ttk) — đặt trực tiếp khi dùng
        if hasattr(self, 'md_text'):
            try:
                self.md_text.configure(bg=panel, fg=fg, insertbackground=fg)
            except Exception:
                pass

    def _toggle_theme(self) -> None:
        # Gọi lại init theme với trạng thái mới
        self._init_theme()

    # ------------------------- Actions -------------------------
    def open_vsix(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("VSIX (ZIP)", "*.vsix"), ("ZIP", "*.zip"), ("All", "*.*")])
        if not path:
            return
        self._open_vsix(path)

    def _open_vsix(self, path: str) -> None:
        try:
            with zipfile.ZipFile(path, "r") as zf:
                names = zf.namelist()
                self.files_data.clear()
                for n in names:
                    try:
                        self.files_data[n] = zf.read(n)
                    except Exception:
                        self.files_data[n] = b""
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể mở VSIX: {e}")
            return
        # populate list with filters support
        self._all_files = sorted(self.files_data.keys())
        self._refresh_file_list()
        self.status.set(f"Đã mở: {os.path.basename(path)} — {len(names)} tệp")
        self.vsix_path = path

    def on_select_file(self, event=None) -> None:
        sel = self.listbox.selection()
        if not sel:
            return
        name = self.listbox.item(sel[0], "values")[0]
        self.current_file = name
        data = self.files_data.get(name, b"")
        # Route to appropriate viewer
        if is_json_like(name):
            self._show_json(data)
            self._show_md(None)
        elif is_md_like(name):
            self._show_json(None)
            self._show_md(data)
        else:
            # default: text preview if decodable
            self._show_json(None)
            try:
                text = data.decode("utf-8")
            except Exception:
                text = "<binary or non-utf8 content>"
            self._show_md(text.encode("utf-8"))
            self.allow_md_edit.set(False)
            self._toggle_md_state()

    # ------------------------- File list filters -------------------------
    def _refresh_file_list(self) -> None:
        for iid in self.listbox.get_children():
            self.listbox.delete(iid)
        for name in self._filter_file_names(self._all_files):
            self.listbox.insert("", END, values=(name,))

    def _filter_file_names(self, names: list[str]) -> list[str]:
        func = self.file_func.get() if hasattr(self, "file_func") else "<Tất cả>"
        ext_sel = self.file_ext.get() if hasattr(self, "file_ext") else "<Tất cả>"
        kw = self.file_name_kw.get().strip().lower() if hasattr(self, "file_name_kw") else ""

        out = []
        for n in names:
            # chức năng
            if func != "<Tất cả>" and file_category(n) != func:
                continue
            # loại (đuôi)
            _, ext = os.path.splitext(n.lower())
            if ext_sel != "<Tất cả>" and ext != ext_sel.lower():
                continue
            # tên
            if kw and kw not in n.lower():
                continue
            out.append(n)
        return out

    def _apply_file_filter(self) -> None:
        self._refresh_file_list()
        if hasattr(self, "_all_files"):
            cur = len(self.listbox.get_children())
            self.status.set(f"Lọc tệp: còn {cur}/{len(self._all_files)}")

    def _clear_file_filter(self) -> None:
        if hasattr(self, "file_func"):
            self.file_func.set("<Tất cả>")
        if hasattr(self, "file_ext"):
            self.file_ext.set("<Tất cả>")
        if hasattr(self, "file_name_kw"):
            self.file_name_kw.set("")
        self._refresh_file_list()
        if hasattr(self, "_all_files"):
            self.status.set(f"Đã xoá lọc tệp ({len(self._all_files)} mục)")

    # ------------------------- JSON View -------------------------
    def _show_json(self, raw: Optional[bytes]) -> None:
        for iid in self.json_tree.get_children():
            self.json_tree.delete(iid)
        if raw is None:
            return
        try:
            obj = json.loads(raw.decode("utf-8"))
        except Exception as e:
            self.json_tree.insert("", END, values=("<parse-error>", str(e)))
            return

        # Flatten JSON to key-paths
        flat = {}

        def walk(prefix, val):
            if isinstance(val, dict):
                for k, v in val.items():
                    walk(f"{prefix}.{k}" if prefix else str(k), v)
            elif isinstance(val, list):
                for i, v in enumerate(val):
                    walk(f"{prefix}[{i}]", v)
            else:
                flat[prefix] = val

        walk("", obj)
        self._json_flat = {k: flat[k] for k in flat}
        self._render_json_rows(self._json_flat)

        # Store parsed object for editing
        self._json_obj_cache = obj

    def _render_json_rows(self, data_map: dict) -> None:
        for iid in self.json_tree.get_children():
            self.json_tree.delete(iid)
        for k in sorted(data_map.keys()):
            self.json_tree.insert("", END, values=(k, json.dumps(data_map[k], ensure_ascii=False)))

    def _apply_json_filter(self) -> None:
        if not hasattr(self, "_json_flat"):
            return
        p = self.filter_path.get().strip()
        v = self.filter_value.get().strip()
        def match(s: str, q: str) -> bool:
            if not q:
                return True
            return q.lower() in s.lower()
        filtered = {}
        for k, val in self._json_flat.items():
            val_text = json.dumps(val, ensure_ascii=False)
            if match(k, p) and match(val_text, v):
                filtered[k] = val
        self._render_json_rows(filtered)
        self.status.set(f"Đã áp lọc ({len(filtered)}/{len(self._json_flat)} hàng)")

    def _clear_json_filter(self) -> None:
        if hasattr(self, "_json_flat"):
            self.filter_path.set("")
            self.filter_value.set("")
            self._render_json_rows(self._json_flat)
            self.status.set("Đã xoá lọc")

    def _close_inline_editor(self) -> None:
        if getattr(self, "_inline_editor", None) is not None:
            try:
                self._inline_editor.destroy()
            except Exception:
                pass
            self._inline_editor = None

    def _on_json_cell_double_click(self, event) -> None:
        item = self.json_tree.identify_row(event.y)
        column = self.json_tree.identify_column(event.x)
        if not item or column != "#2":  # only allow edit on value column
            return
        # Close previous editor if any
        self._close_inline_editor()

        # Cell bbox and current value
        bbox = self.json_tree.bbox(item, "value")
        if not bbox:
            return
        x, y, w, h = bbox
        values = self.json_tree.item(item, "values")
        if len(values) < 2:
            return
        path_key, old_val = values[0], values[1]

        entry = ttk.Entry(self.json_tree)
        entry.place(x=x, y=y, width=w, height=h)
        entry.insert(0, old_val)
        entry.focus_set()
        self._inline_editor = entry

        def commit(*_):
            new_val_text = entry.get()
            self.json_tree.set(item, "value", new_val_text)
            entry.destroy()
            self._inline_editor = None
            # Parse to Python type if possible (allow numbers/bools/strings/objects)
            try:
                new_val = json.loads(new_val_text)
            except Exception:
                new_val = new_val_text
            self._write_json_value(path_key, new_val)
            self.status.set("Đã cập nhật giá trị trong bộ nhớ. Nhấn 'Lưu file hiện tại' để ghi.")

        entry.bind("<Return>", commit)
        entry.bind("<FocusOut>", commit)
        entry.bind("<Escape>", lambda e: (entry.destroy(), setattr(self, "_inline_editor", None)))

    def _write_json_value(self, path_key: str, value):
        # path like: a.b[0].c
        def parse_tokens(p: str):
            parts = []
            # split by dots but keep [idx]
            tokens = re.split(r"(\.[^\[]+|\[[0-9]+\])", p)
            cur = ""
            for t in tokens:
                if not t:
                    continue
                cur += t
            # rebuild simple scanner
            i = 0
            key = ""
            while i < len(p):
                if p[i] == '.':
                    i += 1
                    start = i
                    while i < len(p) and p[i] not in '.[':
                        i += 1
                    parts.append(p[start:i])
                elif p[i] == '[':
                    i += 1
                    start = i
                    while i < len(p) and p[i] != ']':
                        i += 1
                    parts.append(int(p[start:i]))
                    i += 1  # skip ]
                else:
                    # first token (no leading dot)
                    start = i
                    while i < len(p) and p[i] not in '.[':
                        i += 1
                    parts.append(p[start:i])
            return parts

        parts = parse_tokens(path_key)
        ref = self._json_obj_cache
        for idx, tk in enumerate(parts):
            is_last = idx == len(parts) - 1
            if is_last:
                if isinstance(tk, int):
                    ref[tk] = value
                else:
                    ref[tk] = value
            else:
                ref = ref[tk]

    # ------------------------- MD View -------------------------
    def _show_md(self, raw: Optional[bytes]) -> None:
        self.md_text.config(state="normal")
        self.md_text.delete("1.0", END)
        if raw is not None:
            try:
                self.md_text.insert("1.0", raw.decode("utf-8"))
            except Exception:
                self.md_text.insert("1.0", "<binary or non-utf8 content>")
        self._toggle_md_state()

    def _toggle_md_state(self) -> None:
        if self.allow_md_edit.get():
            self.md_text.config(state="normal")
        else:
            self.md_text.config(state="disabled")

    # ------------------------- Save / Export -------------------------
    def save_current_file(self) -> None:
        if not self.current_file:
            messagebox.showinfo("Thông báo", "Chưa chọn tệp để lưu.")
            return
        name = self.current_file
        if is_json_like(name):
            try:
                new_bytes = json.dumps(self._json_obj_cache, ensure_ascii=False, indent=2).encode("utf-8")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không serialize JSON: {e}")
                return
            self.files_data[name] = new_bytes
            self.status.set(f"Đã lưu vào bộ nhớ: {name}")
        elif is_md_like(name):
            if not self.allow_md_edit.get():
                messagebox.showinfo("Thông báo", "Bật 'Sửa văn bản (.md)' để lưu thay đổi.")
                return
            text = self.md_text.get("1.0", END).encode("utf-8")
            self.files_data[name] = text
            self.status.set(f"Đã lưu vào bộ nhớ: {name}")
        else:
            messagebox.showinfo("Thông báo", "Loại tệp này đang chỉ xem trước (chưa hỗ trợ chỉnh sửa).")

    def export_vsix_dialog(self) -> None:
        if not self.files_data:
            messagebox.showinfo("Thông báo", "Chưa mở VSIX nào.")
            return
        out_path = filedialog.asksaveasfilename(defaultextension=".vsix", filetypes=[("VSIX", "*.vsix")])
        if not out_path:
            return
        self.export_vsix(out_path, auto_bump=self.auto_bump.get())

    def export_vsix(self, out_path: str, auto_bump: bool = True) -> None:
        data = dict(self.files_data)
        if auto_bump:
            try:
                if "package.json" in data:
                    pkg = json.loads(data["package.json"].decode("utf-8"))
                    ver = str(pkg.get("version", "0.0.0"))
                    m = re.match(r"^(\d+)\.(\d+)\.(\d+)$", ver)
                    if m:
                        x, y, z = map(int, m.groups())
                        pkg["version"] = f"{x}.{y}.{z+1}"
                        data["package.json"] = json.dumps(pkg, ensure_ascii=False, indent=2).encode("utf-8")
            except Exception as e:
                messagebox.showwarning("Cảnh báo", f"Không thể auto bump version: {e}")

        try:
            with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for name, content in data.items():
                    # Ensure directories in zip path are handled by ZipInfo automatically
                    zf.writestr(name, content)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xuất VSIX: {e}")
            return
        messagebox.showinfo("Thành công", f"Đã xuất VSIX: {out_path}")
        self.status.set(f"Đã xuất VSIX: {out_path}")

    # ------------------------- Find & Replace across JSON -------------------------
    def _find_replace_all_json(self) -> None:
        needle = self.find_text.get()
        repl = self.replace_text.get()
        if not needle:
            messagebox.showinfo("Thông báo", "Vui lòng nhập chuỗi cần tìm.")
            return
        count_changes = 0

        def replace_in_obj(obj):
            nonlocal count_changes
            if isinstance(obj, dict):
                for k in list(obj.keys()):
                    obj[k] = replace_in_obj(obj[k])
                return obj
            elif isinstance(obj, list):
                for i in range(len(obj)):
                    obj[i] = replace_in_obj(obj[i])
                return obj
            elif isinstance(obj, str):
                if self.find_case_sensitive.get():
                    if needle in obj:
                        count_changes += obj.count(needle)
                        return obj.replace(needle, repl)
                    return obj
                else:
                    # case-insensitive replace
                    pattern = re.compile(re.escape(needle), re.IGNORECASE)
                    matches = len(pattern.findall(obj))
                    if matches:
                        count_changes += matches
                        return pattern.sub(repl, obj)
                    return obj
            else:
                return obj

        updated_files = 0
        for name in list(self.files_data.keys()):
            if not is_json_like(name):
                continue
            try:
                obj = json.loads(self.files_data[name].decode("utf-8"))
            except Exception:
                continue
            before_changes = count_changes
            obj2 = replace_in_obj(obj)
            if count_changes > before_changes:
                self.files_data[name] = json.dumps(obj2, ensure_ascii=False, indent=2).encode("utf-8")
                updated_files += 1

        self.status.set(f"Tìm & Thay xong: {count_changes} thay đổi trong {updated_files} tệp JSON")
        # refresh current view if current file is JSON
        if self.current_file and is_json_like(self.current_file):
            self._show_json(self.files_data[self.current_file])


def main():
    root = Tk()
    root.geometry("1100x720")
    app = VsixEditorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

import customtkinter as ctk
from turkanime_api.objects import Anime
from turkanime_api.webdriver import create_webdriver
from turkanime_api.cli.dosyalar import Dosyalar
from turkanime_api.cli.gereksinimler import Gereksinimler, gereksinim_kontrol_cli
import threading
from tkinter import messagebox
import os
import subprocess
import os.path

# Add these constants at the top after imports
PADDING = 10
CORNER_RADIUS = 12
BUTTON_COLOR = "#3b82f6"  # Modern blue
BUTTON_HOVER_COLOR = "#2563eb"
FRAME_COLOR = "#1e1e1e"  # Darker background
TEXT_COLOR = "#f3f4f6"
ENTRY_COLOR = "#2d2d2d"
WATCHED_COLOR = "#22c55e"  # Bright green
DOWNLOADED_COLOR = "#3b82f6"  # Bright blue
INDICATOR_SIZE = 20

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class TurkanimeGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Turkanime GUI")
        self.geometry("1000x800")
        
        # Configure colors and styling
        self.configure(fg_color="#1a1a1a")
        
        # Initialize basic components
        self.dosyalar = Dosyalar()
        self.driver = None
        self.anime_list = None
        self.current_anime = None
        self.selected_episodes = []
        self.download_threads = {}
        self.download_controls = {}
        self.is_playing_episode = False
        self.episode_vars = []
        self.episode_frames = []

        self.items_per_page = 20
        self.current_page = 0
        self.search_results = []

        # Create frames
        self.create_frames()
        
        # Initialize dependencies and start application
        self.after(100, self.initialize_application)

    def create_frames(self):
        # Create frames for different pages
        self.anime_list_frame = ctk.CTkFrame(self, fg_color="#1a1a1a")
        self.anime_list_frame.grid(row=0, column=0, sticky="nsew")
        self.anime_list_frame.grid_rowconfigure(1, weight=1)
        self.anime_list_frame.grid_columnconfigure(0, weight=1)

        self.episode_list_frame = ctk.CTkFrame(self, fg_color="#1a1a1a")
        self.episode_list_frame.grid(row=0, column=0, sticky="nsew")
        self.episode_list_frame.grid_rowconfigure(1, weight=1)
        self.episode_list_frame.grid_columnconfigure(0, weight=1)
        self.episode_list_frame.grid_remove()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def initialize_application(self):
        """Initialize the application after ensuring dependencies are installed"""
        try:
            # Check and install dependencies
            if not self.check_dependencies():
                self.quit()
                return

            # Initialize webdriver and fetch anime list
            self.driver = create_webdriver()
            self.anime_list = Anime.get_anime_listesi(self.driver)
            self.search_results = self.anime_list

            # Create widgets and show initial results
            self.create_widgets()
            self.update_search_results()
            
            # Set up window close handler
            self.protocol("WM_DELETE_WINDOW", self.on_closing)

        except Exception as e:
            messagebox.showerror("Hata", f"Uygulama başlatılırken bir hata oluştu:\n{str(e)}")
            self.quit()

    def check_dependencies(self):
        """Check and install required dependencies"""
        try:
            gerek = Gereksinimler()
            eksikler = gerek.eksikler
            
            if eksikler:
                loading = ctk.CTkToplevel(self)
                loading.title("Gereksinimler Yükleniyor")
                loading.geometry("400x150")
                loading.transient(self)
                loading.grab_set()
                
                status_label = ctk.CTkLabel(loading, text="Gerekli bileşenler indiriliyor...\nBu işlem biraz zaman alabilir.")
                status_label.pack(pady=20)
                
                progress = ctk.CTkProgressBar(loading)
                progress.pack(pady=10, padx=20, fill="x")
                progress.set(0)
                
                def update_progress(current, total, filename):
                    if total > 0:
                        progress.set(current / total)
                    status_label.configure(text=f"İndiriliyor: {filename}\n{current} / {total} bytes")
                
                download_complete = threading.Event()
                download_success = threading.Event()
                
                def download_thread():
                    try:
                        fails = gerek.otomatik_indir(
                            callback=lambda hook: self.after(0, update_progress,
                                hook.get('current', 0),
                                hook.get('total', 0),
                                hook.get('file', '')
                            )
                        )
                        if not fails:
                            download_success.set()
                    finally:
                        download_complete.set()
                
                thread = threading.Thread(target=download_thread, daemon=True)
                thread.start()
                
                # Check download status periodically
                def check_download():
                    if download_complete.is_set():
                        loading.destroy()
                    else:
                        self.after(100, check_download)
                
                self.after(100, check_download)
                loading.wait_window()
                
                if not download_success.is_set():
                    messagebox.showerror("Hata", "Gerekli bileşenler yüklenemedi.")
                    return False
            
            return True
            
        except Exception as e:
            messagebox.showerror("Hata", f"Bileşenler kontrol edilirken bir hata oluştu:\n{str(e)}")
            return False

    def create_widgets(self):
        # Search Frame styling
        self.search_frame = ctk.CTkFrame(self.anime_list_frame, fg_color=FRAME_COLOR, corner_radius=CORNER_RADIUS)
        self.search_frame.grid(row=0, column=0, sticky="ew", padx=PADDING, pady=PADDING)
        self.search_frame.grid_columnconfigure(0, weight=1)
        self.search_frame.grid_columnconfigure(1, weight=0)  # For dropdown

        # Modern search entry
        self.search_entry = ctk.CTkEntry(
            self.search_frame,
            placeholder_text="Anime adı girin",
            height=40,
            corner_radius=CORNER_RADIUS,
            border_width=0,
            fg_color=ENTRY_COLOR,
            text_color=TEXT_COLOR,
            placeholder_text_color="#666666"
        )
        self.search_entry.grid(row=0, column=0, padx=PADDING, pady=PADDING, sticky="ew")
        self.search_entry.bind("<KeyRelease>", self.on_key_release)

        # Items per page dropdown
        self.items_options = ["10", "20", "50", "100"]
        self.items_dropdown = ctk.CTkOptionMenu(
            self.search_frame,
            values=self.items_options,
            command=self.change_items_per_page,
            width=100,
            height=40,
            corner_radius=CORNER_RADIUS,
            fg_color=BUTTON_COLOR,
            button_color=BUTTON_HOVER_COLOR,
            button_hover_color=BUTTON_HOVER_COLOR,
        )
        self.items_dropdown.grid(row=0, column=1, padx=PADDING, pady=PADDING)
        self.items_dropdown.set("20")  # Default value

        # Results Frame
        self.results_frame = ctk.CTkScrollableFrame(
            self.anime_list_frame,
            fg_color=FRAME_COLOR,
            corner_radius=CORNER_RADIUS
        )
        self.results_frame.grid(row=1, column=0, sticky="nsew", padx=PADDING, pady=(0, PADDING))
        
        # Configure grid weights
        self.anime_list_frame.grid_rowconfigure(1, weight=1)
        self.anime_list_frame.grid_columnconfigure(0, weight=1)

        # Pagination Controls styling
        self.pagination_frame = ctk.CTkFrame(self.anime_list_frame, fg_color=FRAME_COLOR, corner_radius=CORNER_RADIUS)
        self.pagination_frame.grid(row=2, column=0, pady=PADDING, padx=PADDING, sticky="ew")
        self.pagination_frame.grid_columnconfigure(1, weight=1)

        # Modern pagination buttons
        self.prev_button = ctk.CTkButton(
            self.pagination_frame,
            text="←",  # Arrow symbol
            width=50,
            height=40,
            corner_radius=CORNER_RADIUS,
            fg_color=BUTTON_COLOR,
            hover_color=BUTTON_HOVER_COLOR,
            command=self.prev_page
        )
        self.prev_button.grid(row=0, column=0, padx=PADDING, pady=PADDING)

        self.page_label = ctk.CTkLabel(
            self.pagination_frame,
            text="Sayfa 1 / 1",
            text_color=TEXT_COLOR
        )
        self.page_label.grid(row=0, column=1, padx=PADDING, pady=PADDING)

        self.next_button = ctk.CTkButton(
            self.pagination_frame,
            text="→",  # Arrow symbol
            width=50,
            height=40,
            corner_radius=CORNER_RADIUS,
            fg_color=BUTTON_COLOR,
            hover_color=BUTTON_HOVER_COLOR,
            command=self.next_page
        )
        self.next_button.grid(row=0, column=2, padx=PADDING, pady=PADDING)

    def on_closing(self):
        # Stop all download threads
        for control in self.download_controls.values():
            if 'stop_event' in control:
                control['stop_event'].set()
        self.driver.quit()
        self.destroy()  

    def on_key_release(self, event):
        # Immediate search on key release
        self.search_anime()

    def search_anime(self):
        query = self.search_entry.get().lower()
        if not query:
            # Show full anime list if no search query
            self.search_results = self.anime_list
        else:
            # Filter anime list based on query
            self.search_results = [(slug, title) for slug, title in self.anime_list if query in title.lower()]
        self.current_page = 0  # Reset to first page after search
        self.update_search_results()

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        if event.num == 5 or event.delta == -120 or event.delta == -1:
            self.canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta == 120 or event.delta == 1:
            self.canvas.yview_scroll(-1, "units")
        elif event.delta:
            # For other platforms
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_canvas_configure(self, event):
        """Update the scroll region when the canvas is resized"""
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def update_search_results(self):
        # Clear existing results
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        results = self.search_results

        # Pagination
        start_index = self.current_page * self.items_per_page
        end_index = start_index + self.items_per_page
        paginated_results = results[start_index:end_index]

        for slug, title in paginated_results:
            anime_button = ctk.CTkButton(
                self.results_frame,
                text=title,
                height=40,
                corner_radius=CORNER_RADIUS,
                fg_color=ENTRY_COLOR,
                hover_color=BUTTON_HOVER_COLOR,
                command=lambda s=slug: self.show_episodes(s)
            )
            anime_button.pack(pady=5, fill="x", padx=PADDING)

        # Update pagination label
        total_pages = len(results) // self.items_per_page + (1 if len(results) % self.items_per_page > 0 else 0)
        if total_pages == 0:
            total_pages = 1
        self.page_label.configure(text=f"Sayfa {self.current_page + 1} / {total_pages}")
        
        # Update button states
        self.prev_button.configure(state="normal" if self.current_page > 0 else "disabled")
        self.next_button.configure(state="normal" if self.current_page < total_pages - 1 else "disabled")

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_search_results()

    def next_page(self):
        total_pages = len(self.search_results) // self.items_per_page + (1 if len(self.search_results) % self.items_per_page > 0 else 0)
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.update_search_results()

    def show_episodes(self, slug):
        # Clear previous episode data
        self.episode_vars = []
        self.episode_frames = []
        
        # Hide the anime list frame and show the episode list frame
        self.anime_list_frame.grid_remove()
        self.episode_list_frame.grid()

        self.current_anime = Anime(self.driver, slug)
        episodes = self.current_anime.bolumler
        self.selected_episodes = []
        self.download_threads = {}
        self.download_controls = {}

        # Clear any existing widgets in episode_list_frame
        for widget in self.episode_list_frame.winfo_children():
            widget.destroy()

        # Configure grid for episode_list_frame
        self.episode_list_frame.grid_rowconfigure(1, weight=1)
        self.episode_list_frame.grid_columnconfigure(0, weight=1)

        # Header frame for back button and search
        header_frame = ctk.CTkFrame(self.episode_list_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=PADDING, pady=PADDING)
        header_frame.grid_columnconfigure(1, weight=1)

        # Modern back button
        self.back_button = ctk.CTkButton(
            header_frame,
            text="←",  # Using arrow symbol
            width=50,
            height=40,
            corner_radius=CORNER_RADIUS,
            fg_color=BUTTON_COLOR,
            hover_color=BUTTON_HOVER_COLOR,
            command=self.back_to_anime_list
        )
        self.back_button.grid(row=0, column=0, padx=(0, PADDING))

        # Modern search entry
        self.episode_search_entry = ctk.CTkEntry(
            header_frame,
            height=40,
            placeholder_text="Bölüm ara...",
            corner_radius=CORNER_RADIUS,
            border_width=0,
            fg_color=ENTRY_COLOR,
            text_color=TEXT_COLOR,
            placeholder_text_color="#666666"
        )
        self.episode_search_entry.grid(row=0, column=1, sticky="ew", padx=PADDING)
        self.episode_search_entry.bind("<KeyRelease>", self.on_episode_search)

        # Episode list container with scrollbar
        episodes_container = ctk.CTkScrollableFrame(
            self.episode_list_frame,
            fg_color=FRAME_COLOR,
            corner_radius=CORNER_RADIUS
        )
        episodes_container.grid(row=1, column=0, sticky="nsew", padx=PADDING, pady=(0, PADDING))
        episodes_container.grid_columnconfigure(0, weight=1)

        # Add Select All Episodes Checkbox
        self.select_all_var = ctk.BooleanVar()
        self.select_all_checkbox = ctk.CTkCheckBox(
            episodes_container,
            text="Tüm Bölümleri Seç",
            height=30,
            corner_radius=CORNER_RADIUS,
            border_width=2,
            variable=self.select_all_var,
            command=self.on_select_all_episodes
        )
        self.select_all_checkbox.pack(pady=PADDING)

        # Style the download button
        self.download_button = ctk.CTkButton(
            episodes_container,
            text="Seçili Bölümleri İndir",
            height=40,
            corner_radius=CORNER_RADIUS,
            fg_color=BUTTON_COLOR,
            hover_color=BUTTON_HOVER_COLOR,
            command=self.download_selected_episodes
        )
        self.download_button.pack(pady=PADDING)

        watched_episodes = []
        downloaded_episodes = []
        
        # Get watched episodes
        if self.current_anime.slug in self.dosyalar.gecmis["izlendi"]:
            watched_episodes = self.dosyalar.gecmis["izlendi"][self.current_anime.slug]
            
        # Get downloaded episodes
        if self.current_anime.slug in self.dosyalar.gecmis["indirildi"]:
            downloaded_episodes = self.dosyalar.gecmis["indirildi"][self.current_anime.slug]

        for bolum in episodes:
            episode_frame = ctk.CTkFrame(
                episodes_container,
                fg_color=ENTRY_COLOR,
                corner_radius=CORNER_RADIUS,
                height=50  # Set fixed height for all frames
            )
            episode_frame.pack(fill="x", pady=5, padx=PADDING)
            episode_frame.pack_propagate(False)  # Prevent frame from shrinking to fit content
            
            # Configure grid columns
            episode_frame.grid_columnconfigure(2, weight=1)  # Make title expand
            
            # Checkbox (now on the left)
            var = ctk.BooleanVar()
            episode_checkbox = ctk.CTkCheckBox(
                episode_frame,
                text="",  # Empty text since we'll show title separately
                variable=var,
                width=20,
                command=lambda b=bolum, v=var: self.on_episode_select(b, v)
            )
            episode_checkbox.grid(row=0, column=0, padx=(PADDING, 5), pady=PADDING)
            self.episode_vars.append(var)

            # Indicators frame - always create it even if empty
            indicator_frame = ctk.CTkFrame(
                episode_frame,
                fg_color="transparent",
                height=40  # Match the height of indicators
            )
            indicator_frame.grid(row=0, column=1, padx=5, pady=PADDING)

            # Add watched indicator
            if bolum.slug in watched_episodes:
                watched_indicator = ctk.CTkLabel(
                    indicator_frame,
                    text="👁",
                    width=INDICATOR_SIZE,
                    fg_color=WATCHED_COLOR,
                    corner_radius=CORNER_RADIUS,
                    text_color=TEXT_COLOR
                )
                watched_indicator.pack(side="left", padx=2)

            # Add downloaded indicator
            if bolum.slug in downloaded_episodes:
                downloaded_indicator = ctk.CTkLabel(
                    indicator_frame,
                    text="⤓",
                    width=INDICATOR_SIZE,
                    fg_color=DOWNLOADED_COLOR,
                    corner_radius=CORNER_RADIUS,
                    text_color=TEXT_COLOR
                )
                downloaded_indicator.pack(side="left", padx=2)

            # Episode title
            title_label = ctk.CTkLabel(
                episode_frame,
                text=bolum.title,
                anchor="w",  # Align text to the left
                text_color=TEXT_COLOR
            )
            title_label.grid(row=0, column=2, sticky="ew", padx=5, pady=PADDING)

            # Play button
            play_button = ctk.CTkButton(
                episode_frame,
                text="▶",
                width=40,
                height=40,
                corner_radius=CORNER_RADIUS,
                fg_color=BUTTON_COLOR,
                hover_color=BUTTON_HOVER_COLOR,
                command=lambda b=bolum: self.play_episode(b)
            )
            play_button.grid(row=0, column=3, sticky="e", padx=PADDING, pady=PADDING)

            self.episode_frames.append((episode_frame, bolum, var))

    def back_to_anime_list(self):
        # Hide the episode list frame and show the anime list frame
        self.episode_list_frame.grid_remove()
        self.anime_list_frame.grid()

    def on_episode_search(self, event):
        query = self.episode_search_entry.get().lower()
        for episode_frame, bolum, var in self.episode_frames:
            if query in bolum.title.lower():
                episode_frame.pack(fill="x", pady=2)
            else:
                episode_frame.pack_forget()

    def on_select_all_episodes(self):
        select_all = self.select_all_var.get()
        for episode_frame, bolum, var in self.episode_frames:
            var.set(select_all)
            if select_all:
                if bolum not in self.selected_episodes:
                    self.selected_episodes.append(bolum)
            else:
                if bolum in self.selected_episodes:
                    self.selected_episodes.remove(bolum)

    def on_episode_select(self, bolum, var):
        if var.get():
            if bolum not in self.selected_episodes:
                self.selected_episodes.append(bolum)
        else:
            if bolum in self.selected_episodes:
                self.selected_episodes.remove(bolum)
        # Update select all checkbox state
        if all(var.get() for _, _, var in self.episode_frames):
            self.select_all_var.set(True)
        else:
            self.select_all_var.set(False)

    def play_episode(self, bolum):
        if self.is_playing_episode:
            messagebox.showwarning("Uyarı", "Zaten bir bölüm oynatılıyor.")
            return
        self.is_playing_episode = True

        # Show loading animation
        self.loading_window = ctk.CTkToplevel(self)
        self.loading_window.title("Yükleniyor...")
        self.loading_window.geometry("300x100")
        self.loading_window.resizable(False, False)
        self.loading_window.grab_set()  # Make it modal

        loading_label = ctk.CTkLabel(self.loading_window, text="Bölüm yükleniyor, lütfen bekleyin...")
        loading_label.pack(pady=10)

        self.loading_progress = ctk.CTkProgressBar(self.loading_window)
        self.loading_progress.set(0)
        self.loading_progress.pack(pady=10, padx=20, fill="x")
        self.loading_progress.start()  # Start indeterminate mode

        threading.Thread(target=self._play_video, args=(bolum,), daemon=True).start()

    def _play_video(self, bolum):
        try:
            video = bolum.best_video()
            if video:
                # Get the video URL
                video_url = video.url

                # Use mpv from TurkAnimu directory
                mpv_path = os.path.join(self.dosyalar.ta_path, "mpv", "mpv.exe") if os.name == "nt" else "mpv"
                
                # Start mpv using subprocess.Popen
                mpv_command = [mpv_path, video_url]

                mpv_process = subprocess.Popen(
                    mpv_command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    encoding='utf-8',
                    errors='replace'
                )

                # Read mpv output line by line
                def read_output():
                    for line in iter(mpv_process.stdout.readline, ''):
                        print(f"mpv output: {line.strip()}")  # Debug output
                        if "VO:" in line or "AO:" in line:
                            # Playback has started
                            # Close loading animation
                            self.after(0, self.close_loading_animation)

                threading.Thread(target=read_output, daemon=True).start()

                # Wait for mpv process to finish
                mpv_process.wait()

                # Video playback finished
                self.is_playing_episode = False

                # Mark episode as watched
                self.dosyalar.set_gecmis(self.current_anime.slug, bolum.slug, "izlendi")

                # Update the episode list on the main thread
                self.after(0, self.show_episodes, self.current_anime.slug)
            else:
                self.is_playing_episode = False
                self.after(0, self.close_loading_animation)
                messagebox.showerror("Hata", f"{bolum.title} oynatılamadı.")
        except Exception as e:
            self.is_playing_episode = False
            self.after(0, self.close_loading_animation)
            messagebox.showerror("Hata", f"{bolum.title} oynatılırken bir hata oluştu.\n{str(e)}")


    def close_loading_animation(self):
        if hasattr(self, 'loading_window') and self.loading_window.winfo_exists():
            self.loading_progress.stop()
            self.loading_window.grab_release()
            self.loading_window.destroy()

    def download_selected_episodes(self):
        if not self.selected_episodes:
            messagebox.showwarning("Uyarı", "Lütfen indirilecek bölümleri seçin.")
            return

        # Style the progress window
        self.progress_window = ctk.CTkToplevel(self)
        self.progress_window.title("İndirme Durumu")
        self.progress_window.geometry("600x500")
        self.progress_window.configure(fg_color="#1a1a1a")

        # Scrollable frame for progress bars
        self.progress_canvas = ctk.CTkCanvas(self.progress_window)
        self.progress_canvas.grid(row=0, column=0, sticky="nsew")
        self.progress_scrollbar = ctk.CTkScrollbar(self.progress_window, command=self.progress_canvas.yview)
        self.progress_scrollbar.grid(row=0, column=1, sticky="ns")
        self.progress_canvas.configure(yscrollcommand=self.progress_scrollbar.set)

        self.progress_frame = ctk.CTkFrame(self.progress_canvas)
        self.progress_canvas.create_window((0, 0), window=self.progress_frame, anchor="nw")

        self.progress_frame.bind(
            "<Configure>",
            lambda e: self.progress_canvas.configure(
                scrollregion=self.progress_canvas.bbox("all")
            )
        )

        self.progress_bars = {}
        for bolum in self.selected_episodes:
            frame = ctk.CTkFrame(self.progress_frame)
            frame.pack(fill="x", pady=5)
            frame.grid_columnconfigure(1, weight=1)

            label = ctk.CTkLabel(frame, text=bolum.title)
            label.grid(row=0, column=0, padx=5, sticky="w")

            progress = ctk.CTkProgressBar(frame)
            progress.set(0)
            progress.grid(row=0, column=1, padx=5, sticky="ew")
            self.progress_bars[bolum.slug] = progress

            pause_button = ctk.CTkButton(frame, text="Duraklat", width=70,
                                         command=lambda b=bolum: self.pause_download(b))
            pause_button.grid(row=0, column=2, padx=5)
            self.download_controls[bolum.slug] = {'paused': False, 'pause_button': pause_button}

        threading.Thread(target=self._download_episodes, daemon=True).start()

    def _download_episodes(self):
        for bolum in self.selected_episodes:
            video = bolum.best_video()
            if video:
                # Prepare output directory
                output_dir = os.path.join(os.getcwd(), "Downloads", self.current_anime.slug)
                os.makedirs(output_dir, exist_ok=True)

                # Initialize download control variables
                stop_event = threading.Event()
                self.download_controls[bolum.slug]['stop_event'] = stop_event

                # Start download in a separate thread
                download_thread = threading.Thread(
                    target=self.download_video,
                    args=(video, bolum, output_dir, stop_event),
                    daemon=True
                )
                download_thread.start()
                self.download_threads[bolum.slug] = download_thread
            else:
                messagebox.showerror("Hata", f"{bolum.title} indirilemedi.")

    def download_video(self, video, bolum, output_dir, stop_event):
        # Update progress bar
        def progress_hook(d):
            if stop_event.is_set():
                raise Exception("Download paused")
            if d['status'] == 'downloading':
                total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
                downloaded_bytes = d.get('downloaded_bytes', 0)
                if total_bytes:
                    progress = downloaded_bytes / total_bytes
                    self.progress_bars[bolum.slug].set(progress)

        try:
            # Use settings from dosyalar
            use_aria2c = self.dosyalar.ayarlar.get("aria2c kullan", False)
            download_path = self.dosyalar.ayarlar.get("indirilenler", ".")
            
            # If custom download path is set, use it instead of default
            if download_path != ".":
                output_dir = os.path.join(download_path, self.current_anime.slug)
                os.makedirs(output_dir, exist_ok=True)

            # Download using video.indir which will use the correct downloader
            video.indir(
                callback=progress_hook, 
                output=output_dir,
                use_aria2c=use_aria2c
            )

            # Mark episode as downloaded
            self.dosyalar.set_gecmis(self.current_anime.slug, bolum.slug, "indirildi")
            # Update progress bar to 100%
            self.progress_bars[bolum.slug].set(1.0)
            # Change pause button to disabled
            self.download_controls[bolum.slug]['pause_button'].configure(state='disabled')
            # Refresh episode list
            self.after(0, self.show_episodes, self.current_anime.slug)
        except Exception as e:
            # Handle pause
            if str(e) == "Download paused":
                pass  # Do nothing, download is paused
            else:
                messagebox.showerror("Hata", f"{bolum.title} indirilemedi.\n{str(e)}")

    def pause_download(self, bolum):
        control = self.download_controls[bolum.slug]
        if control['paused']:
            # Resume download
            control['paused'] = False
            control['pause_button'].configure(text='Duraklat')
            # Create a new stop_event
            stop_event = threading.Event()
            control['stop_event'] = stop_event
            # Restart the download thread
            video = bolum.best_video()
            output_dir = os.path.join(os.getcwd(), "Downloads", self.current_anime.slug)
            download_thread = threading.Thread(
                target=self.download_video,
                args=(video, bolum, output_dir, stop_event),
                daemon=True
            )
            download_thread.start()
            self.download_threads[bolum.slug] = download_thread
        else:
            # Pause download
            control['paused'] = True
            control['pause_button'].configure(text='Devam Et')
            # Signal the download thread to stop
            control['stop_event'].set()

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        if event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, "units")

    def _on_canvas_configure(self, event):
        """Update the scroll region when the canvas is resized"""
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def change_items_per_page(self, choice):
        self.items_per_page = int(choice)
        self.current_page = 0  # Reset to first page
        self.update_search_results()

if __name__ == "__main__":
    app = TurkanimeGUI()
    app.mainloop()

import os
import threading
import json
import re
import requests
import queue
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from io import BytesIO
from urllib.parse import urlparse, unquote
from dotenv import load_dotenv



"""
If you guys are familiar with dotenv then just create .env file in the same dir as this.
Then in .env -> 
GOOGLE_API_KEY="YOUR_API_KEY"
GOOGLE_CX="GOOGLE_CX"
and else ......
"""

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX = os.getenv("GOOGLE_CSE_ID")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
UNSPLASH_ENDPOINT = 'https://api.unsplash.com/search/photos'

class ImageDownloaderApp:
    def __init__(self, root):
        self.root = root
        root.title("Image Downloader Pro")
        self.stop_event = threading.Event()
        self.setup_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_ui(self):
        # Category selection dropdown
        categories = [
            "ထမင်းပေါင်း", "ကြာဇံချက်", "ကတ်ကြေးကိုက်", "ကြေးအိုးဆီချက်", "ကောက်ညှင်းပေါင်း",
            "ခေါက်ဆွဲသုပ်", "တိုဖူးနွေး", "ထမနဲ", "နန်းကြီးသုပ်", "မုန့်ဖက်ထုပ်", "မုန့်လက်ဆောင်း", "မုန့်လင်မယား",
            "မုန့်ဟင်းခါး", "ရွှေရင်အေး", "ရှမ်းခေါက်ဆွဲ", "လက်ဖက်သုပ်", "သာကူ", "အာပူလျှာပူ", "အုန်းနို့ခေါက်ဆွဲ", 
            "ဝက်သားဒုတ်ထိုး", "cats" # Just for testing XDXD, I ain't gonna eat the cats...
        ]
        self.category_var = tk.StringVar(value=categories[0])
        tk.Label(self.root, text="Category:").grid(row=0, column=0, sticky="e")
        self.category_menu = tk.OptionMenu(self.root, self.category_var, *categories)
        self.category_menu.grid(row=0, column=1)

        # Engine selection 
        tk.Label(self.root, text="Engine:").grid(row=1, column=0, sticky="e")
        self.engine = tk.StringVar(value="Google API")
        tk.OptionMenu(self.root, self.engine, "Google API", "Google", "Unsplash").grid(row=1, column=1, sticky="w")

        tk.Label(self.root, text="Number:").grid(row=2, column=0, sticky="e")
        self.n = tk.Entry(self.root, width=10)
        self.n.grid(row=2, column=1, sticky="w")
        self.n.insert(0, "20")

        tk.Label(self.root, text="Type:").grid(row=3, column=0, sticky="e")
        self.ftype = tk.StringVar(value="any")
        tk.OptionMenu(self.root, self.ftype, "any", "jpg", "png").grid(row=3, column=1, sticky="w")

        tk.Label(self.root, text="Folder:").grid(row=4, column=0, sticky="e")
        self.fld = tk.Label(self.root, width=30, text="(none)")
        self.fld.grid(row=4, column=1, sticky="w")
        tk.Button(self.root, text="Choose", command=self.choose_folder).grid(row=4, column=2)

        self.btn = tk.Button(self.root, text="Download", command=self.start)
        self.btn.grid(row=5, column=1, pady=10)

        self.pb = ttk.Progressbar(self.root, length=400, mode="determinate")
        self.pb.grid(row=6, column=0, columnspan=3, pady=5)

        self.canvas = tk.Canvas(self.root, height=200)
        self.scroll = ttk.Scrollbar(self.root, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=self.scroll.set)
        self.thumb_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.thumb_frame, anchor="nw")
        self.canvas.grid(row=7, column=0, columnspan=3)
        self.scroll.grid(row=8, column=0, columnspan=3, sticky="ew")

        tk.Label(self.root, text="Error Log:").grid(row=9, column=0, sticky="w")
        self.log = tk.Listbox(self.root, width=80, height=5)
        self.log.grid(row=10, column=0, columnspan=3)

    def choose_folder(self):
        d = filedialog.askdirectory()
        if d:
            self.folder = d
            self.fld.config(text=d)

    def start(self):
        # Reset
        self.thread = None
        self.update_queue = queue.Queue()
        # Clean
        self.pb["value"] = 0  # Reset 
        try:
            max_n = int(self.n.get())
        except ValueError:
            max_n = 1
        self.pb["maximum"] = max_n
        self.log.delete(0, tk.END)
        for widget in self.thumb_frame.winfo_children():
            widget.destroy()
        self.log.insert("end", "[DEBUG] Starting new download...")
        if hasattr(self, "thread") and self.thread is not None and self.thread.is_alive():
            messagebox.showinfo("Please wait", "Download is already running")
            return
       
        query = self.category_var.get().strip()
        if not query or not hasattr(self, "folder"):
            messagebox.showwarning("", "Please fill all fields")
            return
        self.stop_event.clear()
        self.btn.config(state=tk.DISABLED) 
        self.thread = threading.Thread(target=self._download_worker, args=(self.update_queue, query, self.engine.get(), self.ftype.get(), max_n))
        self.thread.daemon = True  
        self.thread.start()
        self.root.after(100, self._process_queue)

    def _process_queue(self):
        finished_processed = False
        try:
            while True:
                message, data = self.update_queue.get_nowait()
                if message == "log":
                    self.log.insert("end", data)
                    self.log.yview(tk.END)
                elif message == "progress":
                    self.pb["value"] = data
                elif message == "thumbnail":
                    self.add_thumbnail(data)
                elif message == "finished":
                    downloaded, errors = data
                    self.pb["value"] = self.pb["maximum"]  
                    self.log.insert("end", f"[DEBUG] Download finished. Downloaded: {downloaded}, Errors: {errors}")
                    messagebox.showinfo("Finished", f"Downloaded: {downloaded}, Errors: {errors}")
                    self.btn.config(state=tk.NORMAL)  
                    self.thread = None  
                    finished_processed = True
        except queue.Empty:
            pass

        if not finished_processed:
            self.root.after(100, self._process_queue)
        elif self.thread is not None and not self.thread.is_alive():
            self.log.insert("end", "[ERROR] Worker thread exited without sending 'finished'.")

    def _download_worker(self, q, query, engine, ftype, max_n):
        def log(message):
            q.put(("log", message))

        def google_api_search(query, num=10):
            url = 'https://www.googleapis.com/customsearch/v1'
            params = {
                'q': query,
                'cx': GOOGLE_CX,
                'key': GOOGLE_API_KEY,
                'searchType': 'image',
                'num': min(num, 10),
                'imgType': 'photo',
                'safe': 'medium'
            }
            results = []
            start = 1
            while len(results) < num:
                params['start'] = start
                try:
                    log(f"[DEBUG] Google API request: {url} params={params}")
                    resp = requests.get(url, params=params, timeout=10)
                    log(f"[DEBUG] Google API response status: {resp.status_code}")
                    resp.raise_for_status()
                    data = resp.json()
                    log(f"[DEBUG] Google API response keys: {list(data.keys())}")
                    items = data.get('items', [])
                    log(f"[DEBUG] Google API got {len(items)} items in this batch.")
                    if not items:
                        break
                    for item in items:
                        log(f"[DEBUG] Google API item: {item.get('link')}")
                    results.extend([item['link'] for item in items])
                    start += len(items)
                    if len(items) < 10:
                        break
                except Exception as e:
                    log(f"[ERROR] Google API error: {e}")
                    break
            log(f"[DEBUG] Google API final URL list: {results}")
            return results[:num]

        def unsplash_api_search(query, num=10):
            """
            Kindly reminder that unsplash isn't good for Burmese Foods, I just overdid and 
            don't wanna remove it so that why it is here!
            """
            url = UNSPLASH_ENDPOINT
            params = {
                'query': query,
                'client_id': UNSPLASH_ACCESS_KEY,
                'per_page': min(num, 30),
                'orientation': 'landscape'
            }
            results = []
            page = 1
            while len(results) < num:
                params['page'] = page
                try:
                    log(f"[DEBUG] Unsplash API request: {url} params={params}")
                    resp = requests.get(url, params=params, timeout=10)
                    log(f"[DEBUG] Unsplash API response status: {resp.status_code}")
                    resp.raise_for_status()
                    data = resp.json()
                    items = data.get('results', [])
                    log(f"[DEBUG] Unsplash API got {len(items)} items in this batch.")
                    if not items:
                        break
                    for item in items:
                        img_url = item['urls'].get('full') or item['urls'].get('regular')
                        log(f"[DEBUG] Unsplash API item: {img_url}")
                        results.append(img_url)
                    page += 1
                    if len(items) < params['per_page']:
                        break
                except Exception as e:
                    log(f"[ERROR] Unsplash API error: {e}")
                    break
            log(f"[DEBUG] Unsplash API final URL list: {results}")
            return results[:num]

        downloaded_count = 0
        error_count = 0
        try:
            if engine == "Google API":
                log("Using Google Custom Search API for high-res images...")
                image_urls = google_api_search(query, max_n)
                log(f"Google API: Got {len(image_urls)} image URLs.")
                # --- Download loop for Google API ---
                for img_url in image_urls:
                    if downloaded_count >= max_n or self.stop_event.is_set():
                        break
                    # HTTPS only
                    if not urlparse(img_url).scheme == "https":
                        continue
                    try:
                        headers = {
                            'User-Agent': 'Mozilla/5.0',
                            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                            'Referer': img_url
                        }
                        resp = requests.get(img_url, headers=headers, timeout=15, stream=True)
                        if resp.status_code != 200:
                            error_count += 1
                            log(f"Skipped: {img_url[:70]}... | HTTP {resp.status_code}")
                            continue
                        ext = img_url.split('.')[-1].split('?')[0].lower()
                        if len(ext) > 5 or '/' in ext:
                            ext = 'jpg'
                        fn = os.path.join(self.folder, f"{query.replace(' ', '_')}_{downloaded_count + 1}.{ext}")
                        try:
                            with open(fn, 'wb') as f:
                                for chunk in resp.iter_content(1024):
                                    f.write(chunk)
                            img = Image.open(fn)
                            img.verify()
                            img = Image.open(fn)
                            target_min_width, target_min_height = 600, 400
                            if img.width < target_min_width or img.height < target_min_height:
                                scale = max(target_min_width / img.width, target_min_height / img.height)
                                new_size = (int(img.width * scale), int(img.height * scale))
                                img = img.resize(new_size, Image.LANCZOS)
                                img.save(fn)
                                log(f"Upscaled image to {new_size} for {img_url[:70]}...")
                            downloaded_count += 1
                            q.put(("progress", downloaded_count))
                            with open(fn, 'rb') as fthumb:
                                q.put(("thumbnail", fthumb.read(1024*50)))
                        except Exception as e:
                            error_count += 1
                            log(f"Skipped (not a valid image after save): {img_url[:70]}... | Error: {e}")
                            if os.path.exists(fn):
                                os.remove(fn)
                            continue
                        if downloaded_count >= max_n:
                            break
                    except Exception as e:
                        error_count += 1
                        log(f"Skipped: {img_url[:70]}... | Download error: {e}")
            elif engine == "Unsplash":
                log("Using Unsplash API for high-res images...")
                image_urls = unsplash_api_search(query, max_n)
                log(f"Unsplash API: Got {len(image_urls)} image URLs.")
                for img_url in image_urls:
                    if downloaded_count >= max_n or self.stop_event.is_set():
                        break
                    if not urlparse(img_url).scheme == "https":
                        continue
                    try:
                        headers = {
                            'User-Agent': 'Mozilla/5.0',
                            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                            'Referer': img_url
                        }
                        resp = requests.get(img_url, headers=headers, timeout=15, stream=True)
                        if resp.status_code != 200:
                            error_count += 1
                            log(f"Skipped: {img_url[:70]}... | HTTP {resp.status_code}")
                            continue
                        ext = img_url.split('.')[-1].split('?')[0].lower()
                        if len(ext) > 5 or '/' in ext:
                            ext = 'jpg'
                        fn = os.path.join(self.folder, f"{query.replace(' ', '_')}_{downloaded_count + 1}.{ext}")
                        try:
                            with open(fn, 'wb') as f:
                                for chunk in resp.iter_content(1024):
                                    f.write(chunk)
                            img = Image.open(fn)
                            img.verify()
                            img = Image.open(fn)
                            target_min_width, target_min_height = 600, 400
                            if img.width < target_min_width or img.height < target_min_height:
                                scale = max(target_min_width / img.width, target_min_height / img.height)
                                new_size = (int(img.width * scale), int(img.height * scale))
                                img = img.resize(new_size, Image.LANCZOS)
                                img.save(fn)
                                log(f"Upscaled image to {new_size} for {img_url[:70]}...")
                            downloaded_count += 1
                            q.put(("progress", downloaded_count))
                            with open(fn, 'rb') as fthumb:
                                q.put(("thumbnail", fthumb.read(1024*50)))
                        except Exception as e:
                            error_count += 1
                            log(f"Skipped (not a valid image after save): {img_url[:70]}... | Error: {e}")
                            if os.path.exists(fn):
                                os.remove(fn)
                            continue
                        if downloaded_count >= max_n:
                            break
                    except Exception as e:
                        error_count += 1
                        log(f"Skipped: {img_url[:70]}... | Download error: {e}")
            else:
                # --- Google scraping logic only ---
                url, params = "https://www.google.com/search", {"q": query, "tbm": "isch", "start": 0}
                resp = requests.get(url, params=params, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")
                img_tags = soup.find_all("img")
                candidate_imgs = []
                for img_tag in img_tags:
                    img_url = img_tag.get("data-src") or img_tag.get("src")
                    if img_url and img_url.startswith("https://") and not any(x in img_url for x in ["logo", "sprite"]):
                        candidate_imgs.append(img_url)
                image_urls = candidate_imgs[:max_n]
                log(f"Google: Found {len(img_tags)} <img> tags, using {len(candidate_imgs)} image URLs.")
                for img_url in image_urls:
                    if downloaded_count >= max_n or self.stop_event.is_set():
                        break
                    try:
                        headers = {'User-Agent': 'Mozilla/5.0'}
                        resp = requests.get(img_url, headers=headers, timeout=15)
                        if resp.status_code != 200:
                            error_count += 1
                            log(f"Skipped: {img_url[:70]}... | HTTP {resp.status_code}")
                            continue
                        data = resp.content
                        try:
                            img = Image.open(BytesIO(data))
                            img.verify()
                            img = Image.open(BytesIO(data))
                            target_min_width, target_min_height = 600, 400
                            if img.width < target_min_width or img.height < target_min_height:
                                scale = max(target_min_width / img.width, target_min_height / img.height)
                                new_size = (int(img.width * scale), int(img.height * scale))
                                img = img.resize(new_size, Image.LANCZOS)
                                log(f"Upscaled image to {new_size} for {img_url[:70]}...")
                        except Exception as e:
                            error_count += 1
                            log(f"Skipped (not a valid image): {img_url[:70]}... | Error: {e}")
                            continue
                        ext = img.format.lower() if img.format else "jpg"
                        if ftype != "any":
                            if ext != ftype:
                                log(f"Type mismatch: Detected {ext}, saving as {ftype} for {img_url[:70]}...")
                            ext = ftype
                        fn = os.path.join(self.folder, f"{query.replace(' ', '_')}_{downloaded_count + 1}.{ext}")
                        img.save(fn)
                        downloaded_count += 1
                        q.put(("progress", downloaded_count))
                        q.put(("thumbnail", data))
                        if downloaded_count >= max_n:
                            break
                    except Exception as e:
                        error_count += 1
                        log(f"Skipped: {img_url[:70]}... | Download error: {e}")
        finally:
            if not self.stop_event.is_set():
                q.put(("finished", (downloaded_count, error_count)))

    def on_close(self):
        self.stop_event.set()
        self.root.destroy()

    def check_thread_and_close(self):
        if self.thread.is_alive():
            self.root.after(100, self.check_thread_and_close)
        else:
            self.root.destroy()
            
    def add_thumbnail(self, data):
        try:
            img = Image.open(BytesIO(data))
            img.thumbnail((100, 100))
            tkimg = ImageTk.PhotoImage(img)
            lbl = tk.Label(self.thumb_frame, image=tkimg)
            lbl.image = tkimg
            lbl.pack(side="left", padx=5)
        except Exception as e:
            self.log.insert("end", f"Thumbnail error: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    ImageDownloaderApp(root)
    root.mainloop()

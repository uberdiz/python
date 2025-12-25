import os
import io
import time
import platform
from PIL import Image, ImageFilter, ImageChops, ImageStat, ImageGrab

class VisionProcessor:
    def __init__(self, root=None):
        self.root = root
        self._cache = {}

    def load_image(self, path):
        ext = os.path.splitext(path)[1].lower()
        if ext == ".svg":
            try:
                import cairosvg
                png_bytes = cairosvg.svg2png(url=path)
                return Image.open(io.BytesIO(png_bytes)).convert("RGBA")
            except Exception:
                return None
        try:
            img = Image.open(path)
            return img.convert("RGBA") if img.mode != "RGBA" else img
        except Exception:
            return None

    def capture_screen(self, monitor_index=None):
        try:
            import mss
            with mss.mss() as sct:
                mons = sct.monitors
                idx = 0 if monitor_index is None else int(monitor_index)
                idx = max(0, min(idx, len(mons) - 1))
                shot = sct.grab(mons[idx])
                img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
                return img.convert("RGBA")
        except Exception:
            try:
                return ImageGrab.grab().convert("RGBA")
            except Exception:
                return None

    def select_region(self):
        if not self.root:
            return None
        import tkinter as tk
        top = tk.Toplevel(self.root)
        top.attributes("-fullscreen", True)
        top.attributes("-alpha", 0.2)
        top.configure(bg="#000000")
        start = {"x": 0, "y": 0}
        end = {"x": 0, "y": 0}
        rect = None

        def on_press(e):
            start["x"], start["y"] = e.x, e.y
            nonlocal rect
            if rect:
                canvas.delete(rect)
            rect = canvas.create_rectangle(e.x, e.y, e.x, e.y, outline="#00ffff", width=2)

        def on_drag(e):
            end["x"], end["y"] = e.x, e.y
            canvas.coords(rect, start["x"], start["y"], e.x, e.y)

        def on_release(e):
            end["x"], end["y"] = e.x, e.y
            top.destroy()

        canvas = tk.Canvas(top, bg="black")
        canvas.pack(fill="both", expand=True)
        canvas.bind("<ButtonPress-1>", on_press)
        canvas.bind("<B1-Motion>", on_drag)
        canvas.bind("<ButtonRelease-1>", on_release)
        top.lift()
        top.focus_force()
        self.root.wait_window(top)
        x1 = min(start["x"], end["x"])
        y1 = min(start["y"], end["y"])
        x2 = max(start["x"], end["x"])
        y2 = max(start["y"], end["y"])
        if x1 == x2 or y1 == y2:
            return None
        try:
            return ImageGrab.grab(bbox=(x1, y1, x2, y2)).convert("RGBA")
        except Exception:
            return None

    def extract_palette(self, img, max_colors=8):
        small = img.copy()
        small.thumbnail((256, 256))
        pal = small.convert("P", palette=Image.ADAPTIVE, colors=max_colors)
        palette = pal.getpalette()[:max_colors * 3]
        counts = pal.getcolors()
        res = []
        if counts:
            for count, idx in counts[:max_colors]:
                r = palette[idx * 3]
                g = palette[idx * 3 + 1]
                b = palette[idx * 3 + 2]
                res.append({"rgb": [r, g, b], "count": int(count)})
        return res

    def ocr(self, img):
        try:
            import pytesseract
            return pytesseract.image_to_string(img)
        except Exception:
            return ""

    def alpha_mask(self, img):
        if img.mode == "RGBA":
            return img.split()[3]
        return None

    def edges(self, img):
        return img.convert("L").filter(ImageFilter.FIND_EDGES)

    def match_template(self, img, tmpl, threshold=12.0):
        t = tmpl.convert("RGBA")
        i = img.convert("RGBA")
        matches = []
        scales = [1.0, 0.75, 0.5]
        for s in scales:
            tw = max(1, int(t.width * s))
            th = max(1, int(t.height * s))
            ts = t.resize((tw, th))
            step = max(10, int(min(i.width, i.height) * 0.02))
            for x in range(0, i.width - tw, step):
                for y in range(0, i.height - th, step):
                    region = i.crop((x, y, x + tw, y + th))
                    diff = ImageChops.difference(region.convert("L"), ts.convert("L"))
                    stat = ImageStat.Stat(diff)
                    val = sum(stat.mean) / len(stat.mean)
                    if val < threshold:
                        matches.append({"x": x, "y": y, "w": tw, "h": th, "score": float(val)})
        return matches[:10]

    def analyze(self, img, config=None):
        if img is None:
            return {}
        key = (img.width, img.height, getattr(img, "mode", ""))
        if key in self._cache:
            cached = self._cache[key]
            if time.time() - cached["ts"] < 2.0:
                return cached["data"]
        data = {}
        data["size"] = {"w": img.width, "h": img.height}
        data["palette"] = self.extract_palette(img)
        data["ocr_text"] = self.ocr(img)
        am = self.alpha_mask(img)
        data["has_alpha"] = bool(am)
        data["edges_preview"] = True
        data["layers"] = {"alpha": bool(am), "edges": True}
        self._cache[key] = {"ts": time.time(), "data": data}
        return data

class UnityIntegration:
    def __init__(self, endpoint=None):
        self.endpoint = endpoint
    def capture_game_view(self):
        try:
            if self.endpoint:
                return None
        except Exception:
            return None
        return None
    def capture_scene_view(self):
        try:
            if self.endpoint:
                return None
        except Exception:
            return None
        return None
    def asset_preview(self, asset_id):
        try:
            if self.endpoint and asset_id:
                return None
        except Exception:
            return None
        return None

class RobloxIntegration:
    def __init__(self, endpoint=None):
        self.endpoint = endpoint
    def capture_viewport(self):
        try:
            if self.endpoint:
                return None
        except Exception:
            return None
        return None
    def script_context(self):
        try:
            if self.endpoint:
                return {}
        except Exception:
            return {}
        return {}

class WebIntegration:
    def __init__(self, driver=None):
        self.driver = driver
    def full_page_screenshot(self):
        try:
            if self.driver and hasattr(self.driver, 'get_screenshot_as_png'):
                try:
                    original_size = self.driver.execute_script("return [document.body.scrollWidth, document.body.scrollHeight]")
                    self.driver.set_window_size(original_size[0], original_size[1])
                except Exception:
                    pass
                import io
                from PIL import Image
                png = self.driver.get_screenshot_as_png()
                return Image.open(io.BytesIO(png)).convert("RGBA")
        except Exception:
            return None
        return None
    def element_screenshot(self, selector):
        try:
            if self.driver:
                el = self.driver.find_element("css selector", selector) if hasattr(self.driver, 'find_element') else None
                if el:
                    loc = el.location
                    size = el.size
                    img = self.full_page_screenshot()
                    if img:
                        box = (int(loc['x']), int(loc['y']), int(loc['x'] + size['width']), int(loc['y'] + size['height']))
                        return img.crop(box)
        except Exception:
            return None
        return None

class VisualPipeline:
    def __init__(self, processor):
        self.processor = processor
        self.stages = []
    def add(self, stage_name, **kwargs):
        self.stages.append((stage_name, kwargs))
        return self
    def run(self, source=None):
        img = None
        data = None
        for name, kwargs in self.stages:
            if name == 'load' and source:
                img = self.processor.load_image(source)
            elif name == 'capture_screen':
                img = self.processor.capture_screen(kwargs.get('monitor_index'))
            elif name == 'select_region':
                img = self.processor.select_region()
            elif name == 'analyze':
                data = self.processor.analyze(img, kwargs)
            elif name == 'ocr':
                if img:
                    text = self.processor.ocr(img)
                    if data is None:
                        data = {}
                    data['ocr_text'] = text
            elif name == 'palette':
                if img:
                    pal = self.processor.extract_palette(img, kwargs.get('max_colors', 8))
                    if data is None:
                        data = {}
                    data['palette'] = pal
        return img, data

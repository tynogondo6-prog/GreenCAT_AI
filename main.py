import os
import io
import requests
from PIL import Image as PILImage
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.slider import Slider
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.image import Image as CoreImage
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, Rectangle

POLLINATIONS_API_KEY = "sk_1LLrsSpySlmWSPO7ExaqdMb1GvyHYvJW"

class ShutterButton(ButtonBehavior, Image):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.create_square_texture()

    def create_square_texture(self):
        size = 200
        img = PILImage.new('RGBA', (size, size), (0, 0, 0, 0))
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle((10, 10, size-10, size-10), radius=30, fill=(255, 255, 255, 255))
        data = io.BytesIO()
        img.save(data, format='png')
        data.seek(0)
        self.texture = CoreImage(data, ext='png').texture

class CameraApp(App):
    def build(self):
        self.title = 'GreenCAT AI Camera'
        Window.size = (400, 700) 
        self.current_ratio = 'Full'
        
        root = FloatLayout()
        
        # 1. КАМЕРА (Всегда на весь экран)
        self.camera_view = Image(size_hint=(1, 1), pos_hint={'x': 0, 'y': 0})
        img = PILImage.new('RGB', (1280, 720), color=(80, 80, 80))
        data = io.BytesIO()
        img.save(data, format='png')
        data.seek(0)
        self.camera_view.texture = CoreImage(data, ext='png').texture
        root.add_widget(self.camera_view)
        
        # 2. СЛОЙ ДЛЯ ОБРЕЗКИ (Черные полосы)
        self.crop_overlay = Widget(size_hint=(1, 1), pos_hint={'x': 0, 'y': 0})
        with self.crop_overlay.canvas:
            Color(0, 0, 0, 0.7) # Черный цвет с прозрачностью 70%
            self.mask_top = Rectangle()
            self.mask_bottom = Rectangle()
            self.mask_left = Rectangle()
            self.mask_right = Rectangle()
            
        self.crop_overlay.opacity = 0 # Скрыт по умолчанию (Full)
        root.add_widget(self.crop_overlay)
        
        Window.bind(size=self.update_masks)
        
        # 3. ВЕРХНЯЯ ПАНЕЛЬ
        top_bar = BoxLayout(size_hint=(1, 0.1), pos_hint={'top': 1}, padding=(10, 10, 10, 10), spacing=10)
        
        self.btn_flash = Button(text='⚡', font_size=24, size_hint=(None, 1), width=50, background_color=(0.2, 0.2, 0.2, 0.5))
        self.btn_flash.bind(on_press=self.toggle_flash)
        
        self.btn_settings = Button(text='⚙', font_size=24, size_hint=(None, 1), width=50, background_color=(0.2, 0.2, 0.2, 0.5))
        self.btn_settings.bind(on_press=self.toggle_settings)
        
        top_bar.add_widget(self.btn_flash)
        top_bar.add_widget(self.btn_settings)
        top_bar.add_widget(Widget()) 
        root.add_widget(top_bar)
        
        # 4. ПАНЕЛЬ НАСТРОЕК
        self.settings_panel = BoxLayout(orientation='vertical', size_hint=(0.8, 0.5), pos_hint={'center_x': 0.5, 'center_y': 0.6}, spacing=5, padding=5)
        with self.settings_panel.canvas.before:
            Color(0, 0, 0, 0.8)
            self.settings_bg = Rectangle(pos=self.settings_panel.pos, size=self.settings_panel.size)
        self.settings_panel.bind(pos=self.update_settings_bg, size=self.update_settings_bg)
        
        self.settings_panel.add_widget(Label(text="Формат кадра:", size_hint_y=0.15, bold=True))
        ratios_layout = BoxLayout(spacing=5, size_hint_y=0.25)
        for ratio in ['Full', '1:1', '9:16', '16:9', '3:4']:
            btn = Button(text=ratio, background_color=(0.3, 0.3, 0.3, 1), font_size=12)
            btn.bind(on_press=self.change_format)
            ratios_layout.add_widget(btn)
        self.settings_panel.add_widget(ratios_layout)
        
        self.settings_panel.add_widget(Label(text="Ориентация (для ПК):", size_hint_y=0.15, bold=True))
        orient_layout = BoxLayout(spacing=5, size_hint_y=0.25)
        btn_vert = Button(text='Вертикально', background_color=(0.3, 0.3, 0.3, 1), font_size=12)
        btn_vert.bind(on_press=self.set_vertical)
        orient_layout.add_widget(btn_vert)
        btn_horiz = Button(text='Горизонтально', background_color=(0.3, 0.3, 0.3, 1), font_size=12)
        btn_horiz.bind(on_press=self.set_horizontal)
        orient_layout.add_widget(btn_horiz)
        self.settings_panel.add_widget(orient_layout)
        
        self.settings_panel.opacity = 0
        self.settings_panel.disabled = True
        root.add_widget(self.settings_panel)
        
        # 5. НИЖНЯЯ ПАНЕЛЬ
        bottom_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.35), pos_hint={'x': 0, 'y': 0}, padding=20)
        
        zoom_layout = BoxLayout(size_hint_y=0.2)
        zoom_layout.add_widget(Label(text='Зум:', size_hint_x=0.15, bold=True))
        self.zoom_slider = Slider(min=1, max=20, value=1, step=0.1)
        self.zoom_label = Label(text='1.0x', size_hint_x=0.15, bold=True)
        self.zoom_slider.bind(value=self.update_zoom_label)
        zoom_layout.add_widget(self.zoom_slider)
        zoom_layout.add_widget(self.zoom_label)
        bottom_layout.add_widget(zoom_layout)
        
        action_layout = BoxLayout(size_hint_y=0.8)
        
        ai_layout = BoxLayout(orientation='vertical', size_hint_x=0.3)
        ai_layout.add_widget(Label(text='ИИ:', bold=True))
        self.ai_slider = Slider(min=0, max=1, value=0, step=1)
        self.ai_label = Label(text='Выкл', bold=True)
        self.ai_slider.bind(value=lambda i, v: setattr(self.ai_label, 'text', 'Вкл' if v == 1 else 'Выкл'))
        ai_layout.add_widget(self.ai_slider)
        ai_layout.add_widget(self.ai_label)
        action_layout.add_widget(ai_layout)
        
        center_btn_layout = BoxLayout(size_hint_x=0.4, padding=(20, 10, 20, 10))
        self.shutter_btn = ShutterButton(size_hint=(1, 1))
        self.shutter_btn.bind(on_press=self.take_photo)
        center_btn_layout.add_widget(self.shutter_btn)
        action_layout.add_widget(center_btn_layout)
        
        action_layout.add_widget(BoxLayout(size_hint_x=0.3))
        bottom_layout.add_widget(action_layout)
        
        self.status = Label(text='', size_hint_y=0.1, color=(1, 0.5, 0, 1), bold=True)
        bottom_layout.add_widget(self.status)
        
        root.add_widget(bottom_layout)
        
        # 6. Вспышка
        self.flash_overlay = Widget(size_hint=(1, 1), pos_hint={'x': 0, 'y': 0})
        with self.flash_overlay.canvas:
            self.flash_color = Color(0, 0, 0, 1)
            self.flash_rect = Rectangle(size=Window.size)
        self.flash_overlay.opacity = 0
        root.add_widget(self.flash_overlay)
        
        Clock.schedule_once(lambda dt: self.change_format(type('obj', (object,), {'text': 'Full'})), 0.5)
        
        return root

    def update_zoom_label(self, instance, value):
        self.zoom_label.text = f"{value:.1f}x"

    def update_settings_bg(self, instance, value):
        self.settings_bg.pos = instance.pos
        self.settings_bg.size = instance.size

    def update_window_size(self, instance, value):
        self.flash_rect.size = value

    def update_masks(self, instance, value):
        # Пересчитываем полосы при изменении размера окна
        if hasattr(self, 'current_ratio'):
            self.change_format(type('obj', (object,), {'text': self.current_ratio}))

    def change_format(self, instance):
        ratio = instance.text
        self.current_ratio = ratio
        self.status.text = f"Формат: {ratio}"
        
        w, h = Window.size
        
        # Рассчитываем размеры "окна" (видимой части)
        target_w = w
        target_h = h
        
        if ratio == 'Full':
            self.crop_overlay.opacity = 0
            self.mask_top.size = (0, 0)
            self.mask_bottom.size = (0, 0)
            self.mask_left.size = (0, 0)
            self.mask_right.size = (0, 0)
            return
        else:
            self.crop_overlay.opacity = 1
            
        if ratio == '1:1':
            target_size = min(w, h)
            target_w, target_h = target_size, target_size
        elif ratio == '9:16':
            target_h = h
            target_w = h * (9/16)
            if target_w > w:
                target_w = w
                target_h = w * (16/9)
        elif ratio == '16:9':
            target_w = w
            target_h = w * (9/16)
            if target_h > h:
                target_h = h
                target_w = h * (16/9)
        elif ratio == '3:4':
            target_h = h
            target_w = h * (3/4)
            if target_w > w:
                target_w = w
                target_h = w * (4/3)
                
        # Вычисляем координаты центра
        x = (w - target_w) / 2
        y = (h - target_h) / 2
        
        # Настраиваем черные маски (шторки)
        # Верхняя
        self.mask_top.pos = (0, y + target_h)
        self.mask_top.size = (w, h - (y + target_h))
        # Нижняя
        self.mask_bottom.pos = (0, 0)
        self.mask_bottom.size = (w, y)
        # Левая
        self.mask_left.pos = (0, y)
        self.mask_left.size = (x, target_h)
        # Правая
        self.mask_right.pos = (x + target_w, y)
        self.mask_right.size = (w - (x + target_w), target_h)

    def set_vertical(self, instance):
        Window.size = (400, 700)
        self.status.text = "Окно: Вертикально"

    def set_horizontal(self, instance):
        Window.size = (700, 400)
        self.status.text = "Окно: Горизонтально"

    def toggle_flash(self, instance):
        if self.btn_flash.background_color == [0.2, 0.2, 0.2, 0.5]:
            self.btn_flash.background_color = (1, 1, 0, 1)
        else:
            self.btn_flash.background_color = (0.2, 0.2, 0.2, 0.5)

    def toggle_settings(self, instance):
        if self.settings_panel.opacity == 0:
            self.settings_panel.opacity = 1
            self.settings_panel.disabled = False
        else:
            self.settings_panel.opacity = 0
            self.settings_panel.disabled = True

    def take_photo(self, instance):
        self.flash_overlay.opacity = 1
        Clock.schedule_once(self.end_flash, 0.2)
        
        texture = self.camera_view.texture
        if not texture:
            return
            
        w, h = texture.size
        zoom = float(self.zoom_slider.value) 
        
        crop_w = int(w / zoom)
        crop_h = int(h / zoom)
        x = (w - crop_w) // 2
        y = (h - crop_h) // 2
        cropped = texture.get_region(x, y, crop_w, crop_h)
        
        # Тут в будущем мы применим обрезку по формату, но пока сохраняем то, что есть
        cropped.save('temp_photo.png')
        
        if self.ai_slider.value == 1:
            self.status.text = 'ИИ улучшает...'
            Clock.schedule_once(lambda dt: self.send_to_ai('temp_photo.png'), 0.3)
        else:
            self.status.text = f'Сохранено ({self.current_ratio})'
            Clock.schedule_once(lambda dt: setattr(self.status, 'text', ''), 2)

    def end_flash(self, dt):
        from kivy.animation import Animation
        anim = Animation(opacity=0, duration=0.3)
        anim.start(self.flash_overlay)

    def send_to_ai(self, filename):
        try:
            filepath = os.path.abspath(filename)
            prompt = "ultra realistic, high detail"
            url = f"https://image.pollinations.ai/prompt/{prompt}?model=flux&nologo=true"
            headers = {"Authorization": f"Bearer {POLLINATIONS_API_KEY}"}
            
            with open(filepath, 'rb') as f:
                files = {'file': (filename, f, 'image/png')}
                response = requests.post(url, files=files, headers=headers, timeout=120)
            
            if response.status_code == 200:
                with open('result_ai.jpg', 'wb') as f:
                    f.write(response.content)
                self.status.text = 'Успех! ИИ улучшил фото'
            else:
                self.status.text = f'Ошибка ИИ: {response.status_code}'
        except Exception as e:
            self.status.text = f'Ошибка: {str(e)[:40]}'
        finally:
            Clock.schedule_once(lambda dt: setattr(self.status, 'text', ''), 3)

if __name__ == '__main__':
    CameraApp().run()
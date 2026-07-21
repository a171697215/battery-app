"""
智能电池工序追溯系统 - 手机采集端（集成摄像头实时扫码）
"""
import os
import json
import base64
from datetime import datetime
import requests
from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.graphics import Color, Line, RoundedRectangle
from kivy.lang import Builder
from kivy.properties import StringProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.widget import Widget
from kivy.utils import platform
from kivy_garden.xcamera import XCamera  # 需要 pip install kivy_garden.xcamera
from pyzbar.pyzbar import decode as zbar_decode  # 需要 pip install pyzbar
from PIL import Image as PILImage
from plyer import uniqueid, vibrator

# ---------- Android 权限请求（如有需要） ----------
if platform == 'android':
    from android.permissions import request_permissions, Permission  # 需要 pyjnius

# ---------- 字体 ----------
if os.path.exists("NotoSansCJKsc-Regular.otf"):
    LabelBase.register(name='NotoSansCJK', fn_regular="NotoSansCJKsc-Regular.otf")
    DEFAULT_FONT = 'NotoSansCJK'
else:
    DEFAULT_FONT = 'Roboto'

# ---------- 配置持久化 ----------
CONFIG_FILE = "server_config.json"
ACCOUNT_FILE = "account.json"

def load_server_url():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f).get('url', 'http://192.168.1.100:8000')
        except:
            pass
    return 'http://192.168.1.100:8000'

def save_server_url(url):
    with open(CONFIG_FILE, 'w') as f:
        json.dump({'url': url}, f)

def load_account():
    if os.path.exists(ACCOUNT_FILE):
        try:
            with open(ACCOUNT_FILE, 'r') as f:
                data = json.load(f)
                username = data.get('username', '')
                password_enc = data.get('password', '')
                if password_enc:
                    password = base64.b64decode(password_enc.encode()).decode()
                else:
                    password = ''
                return username, password
        except:
            pass
    return '', ''

def save_account(username, password):
    with open(ACCOUNT_FILE, 'w') as f:
        password_enc = base64.b64encode(password.encode()).decode()
        json.dump({'username': username, 'password': password_enc}, f)

def clear_account():
    if os.path.exists(ACCOUNT_FILE):
        os.remove(ACCOUNT_FILE)

# ---------- KV 布局 ----------
KV = f'''
<InfoLabel@Label>:
    font_name: "{DEFAULT_FONT}"
    color: 0.173, 0.243, 0.314, 1
    font_size: "15sp"

<LoginScreen>:
    BoxLayout:
        orientation: "vertical"
        padding: "10dp", "5dp", "10dp", "5dp"
        spacing: 0
        canvas.before:
            Color:
                rgba: 0.945, 0.957, 0.965, 1
            Rectangle:
                pos: self.pos
                size: self.size

        # 顶部：网络设置按钮
        BoxLayout:
            size_hint_y: None
            height: "40dp"
            orientation: "horizontal"
            Label:
                text: ""
                size_hint_x: 1
            Button:
                text: "设置网络"
                font_name: "{DEFAULT_FONT}"
                font_size: "14sp"
                background_normal: ""
                background_color: 0,0,0,0
                color: 0.231, 0.490, 0.847, 1
                size_hint: None, None
                size: "80dp", "40dp"
                on_press: app.show_server_settings()

        # 可滚动区域，避免软键盘遮挡
        ScrollView:
            do_scroll_x: False
            do_scroll_y: True
            BoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                padding: "20dp", "20dp"
                spacing: "20dp"

                # 标题
                InfoLabel:
                    text: "智能电池追溯系统"
                    font_size: "24sp"
                    halign: "center"
                    bold: True
                    size_hint_y: None
                    height: "50dp"

                # 卡片（登录框）
                BoxLayout:
                    orientation: "vertical"
                    spacing: "15dp"
                    padding: "25dp"
                    size_hint_y: None
                    height: "280dp"
                    canvas:
                        Color:
                            rgba: 1, 1, 1, 1
                        RoundedRectangle:
                            radius: [18]
                            pos: self.pos
                            size: self.size

                    TextInput:
                        id: username_input
                        hint_text: "工号"
                        font_name: "{DEFAULT_FONT}"
                        background_normal: ""
                        background_color: 0.945, 0.957, 0.965, 1
                        foreground_color: 0.173, 0.243, 0.314, 1
                        padding: "14dp"
                        cursor_color: 0.231, 0.490, 0.847, 1
                        size_hint_y: None
                        height: "52dp"

                    TextInput:
                        id: password_input
                        hint_text: "密码"
                        password: True
                        font_name: "{DEFAULT_FONT}"
                        background_normal: ""
                        background_color: 0.945, 0.957, 0.965, 1
                        foreground_color: 0.173, 0.243, 0.314, 1
                        padding: "14dp"
                        cursor_color: 0.231, 0.490, 0.847, 1
                        size_hint_y: None
                        height: "52dp"

                    # 记住密码左对齐
                    BoxLayout:
                        size_hint_y: None
                        height: "40dp"
                        spacing: "5dp"
                        # 确保左对齐，不额外占空间
                        CheckBox:
                            id: remember_check
                            size_hint: None, None
                            size: "30dp", "30dp"
                            pos_hint: {{"top": 1}}
                        Label:
                            text: "记住密码"
                            font_name: "{DEFAULT_FONT}"
                            color: 0.173, 0.243, 0.314, 1
                            size_hint_x: None
                            width: "80dp"

                    Button:
                        text: "登  录"
                        font_name: "{DEFAULT_FONT}"
                        font_size: "18sp"
                        bold: True
                        background_normal: ""
                        background_color: 0.231, 0.490, 0.847, 1
                        color: 1, 1, 1, 0.92
                        size_hint_y: None
                        height: "52dp"
                        on_press: app.login(username_input.text, password_input.text)

                # 底部占位
                Widget:
                    size_hint_y: None
                    height: "40dp"

<ScanScreen>:
    BoxLayout:
        orientation: "vertical"
        padding: "10dp"
        spacing: "8dp"

        BoxLayout:
            size_hint_y: None
            height: "65dp"
            spacing: "8dp"
            canvas:
                Color:
                    rgba: 1, 1, 1, 1
                RoundedRectangle:
                    radius: [14]
                    pos: self.pos
                    size: self.size
            InfoLabel:
                text: "工序: " + app.process_name
                halign: "left"
                padding: "10dp"
                bold: True
            InfoLabel:
                text: "操作员: " + app.operator_name
                halign: "right"
                padding: "10dp"

        # 扫描预览区域（虚线框 + 摄像头）
        RelativeLayout:
            id: scan_area
            size_hint: 1, 0.8  # 占用大部分空间
            # 虚线框绘制
            canvas.after:
                Color:
                    rgba: 0.231, 0.49, 0.847, 0.9
                Line:
                    rectangle: (self.x + dp(30), self.y + dp(30), self.width - dp(60), self.height - dp(90))
                    width: 1.5
                    dash_length: 12
                    dash_offset: 6

        # 扫码按钮（圆角卡片风格）
        Button:
            id: scan_btn
            text: "🔍 扫码"
            font_name: "{DEFAULT_FONT}"
            font_size: "22sp"
            background_normal: ""
            background_color: 0.231, 0.490, 0.847, 0.85
            color: 1, 1, 1, 0.95
            size_hint: 0.6, None
            height: "56dp"
            pos_hint: {{"center_x": 0.5}}
            canvas.after:
                Color:
                    rgba: 1, 1, 1, 0.1
                RoundedRectangle:
                    radius: [28]
                    pos: self.pos
                    size: self.size
            on_press: app.start_scan()

        InfoLabel:
            id: status_label
            text: ""
            color: 0.498, 0.549, 0.553, 1
            size_hint_y: None
            height: "30dp"

        BoxLayout:
            size_hint_y: None
            height: "35dp"
            spacing: "10dp"
            Button:
                text: "最近记录"
                font_name: "{DEFAULT_FONT}"
                background_normal: ""
                background_color: 0.153, 0.682, 0.376, 1
                color: 1, 1, 1, 0.9
                size_hint: 0.4, 1
            InfoLabel:
                id: last_sn_label
                text: ""
                size_hint: 0.6, 1

        BoxLayout:
            size_hint_y: None
            height: "50dp"
            spacing: "10dp"
            Button:
                text: "退出登录"
                font_name: "{DEFAULT_FONT}"
                background_normal: ""
                background_color: 0.498, 0.549, 0.553, 1
                color: 1, 1, 1, 0.92
                size_hint: 0.5, 1
                on_press: app.logout()
            Button:
                text: "关于"
                font_name: "{DEFAULT_FONT}"
                background_normal: ""
                background_color: 0.498, 0.549, 0.553, 1
                color: 1, 1, 1, 0.92
                size_hint: 0.5, 1
                on_press: app.show_settings()
'''


class BatteryApp(App):
    process_name = StringProperty("")
    operator_name = StringProperty("")
    server_url = StringProperty(load_server_url())

    def build(self):
        # 背景色与登录界面一致，消除启动闪变
        Window.clearcolor = (0.945, 0.957, 0.965, 1)
        Window.softinput_mode = 'pan'

        Builder.load_string(KV)
        self._token = None
        self.title = "电池追溯"

        try:
            self.device_id = uniqueid.id
        except:
            self.device_id = "unknown"

        # 摄像头相关变量
        self.camera = None
        self.decode_event = None

        saved_username, saved_password = load_account()
        if saved_username:
            Clock.schedule_once(lambda dt: self._fill_saved_credentials(saved_username, saved_password), 0)

        self.sm = ScreenManager()
        self.sm.add_widget(LoginScreen(name="login"))
        self.sm.add_widget(ScanScreen(name="scan"))
        return self.sm

    def _fill_saved_credentials(self, username, password):
        login_screen = self.sm.get_screen('login')
        if login_screen:
            login_screen.ids.username_input.text = username
            login_screen.ids.password_input.text = password
            login_screen.ids.remember_check.active = True

    # ---------- 扫码（摄像头实时解码）----------
    def start_scan(self):
        # 防止重复点击
        if self.camera:
            return

        # 请求摄像头权限（Android）
        if platform == 'android':
            request_permissions([Permission.CAMERA])
            # 简单等待权限结果，实际应使用回调，这里假设权限已授予
            Clock.schedule_once(self._on_android_permission_granted, 0.5)
        else:
            self._activate_camera()

    def _on_android_permission_granted(self, dt):
        # 可以在此检查权限，此处简化直接激活
        self._activate_camera()

    def _activate_camera(self):
        scan_screen = self.sm.get_screen("scan")
        if not scan_screen:
            return

        # 移除旧相机（如果有）
        if self.camera:
            scan_screen.ids.scan_area.remove_widget(self.camera)
            self.camera = None

        try:
            self.camera = XCamera(play=True)
            self.camera.size_hint = (1, 1)
            scan_screen.ids.scan_area.add_widget(self.camera, index=0)  # 放在虚线框下方
            # 开始解码循环
            self.decode_event = Clock.schedule_interval(self._decode_frame, 0.5)
            scan_screen.ids.status_label.text = "扫描中..."
        except Exception as e:
            self.show_error(f"摄像头启动失败：{e}")
            self.camera = None

    def _decode_frame(self, dt):
        if not self.camera or not self.camera.texture:
            return
        # 获取摄像头纹理的原始像素数据
        tex = self.camera.texture
        size = tex.size
        pixels = tex.pixels  # RGBA 字符串

        try:
            # 将 RGBA 转换为 PIL Image（灰度处理以加速）
            pil_image = PILImage.frombytes('RGBA', size, pixels)
            pil_image = pil_image.convert('L')  # 灰度
            # 使用 pyzbar 解码
            decoded = zbar_decode(pil_image)
            if decoded:
                data = decoded[0].data.decode('utf-8')
                self.on_barcode_detected(data)
        except Exception as e:
            pass  # 忽略解码错误

    @mainthread
    def on_barcode_detected(self, barcode_data):
        # 停止扫描
        self.stop_scan()
        self._handle_scan_result(barcode_data)

    def stop_scan(self):
        if self.decode_event:
            self.decode_event.cancel()
            self.decode_event = None
        if self.camera:
            self.camera.play = False
            scan_screen = self.sm.get_screen("scan")
            if scan_screen and self.camera.parent:
                self.camera.parent.remove_widget(self.camera)
            self.camera = None

    def _handle_scan_result(self, code):
        scan_screen = self.sm.get_screen("scan")
        success, msg = self.submit_record(code)
        scan_screen.ids.status_label.text = f'{"成功" if success else "失败"}：{msg}'
        if success:
            scan_screen.ids.last_sn_label.text = code

    # ---------- 登录相关 ----------
    def login(self, username, password):
        login_screen = self.sm.get_screen('login')
        remember = login_screen.ids.remember_check.active
        if remember:
            save_account(username, password)
        else:
            clear_account()

        try:
            resp = requests.post(
                f"{self.server_url}/api/login",
                json={"username": username, "password": password},
                timeout=5,
            )
            if resp.status_code == 200:
                data = resp.json()
                self._token = data["token"]
                self.operator_name = data["full_name"]
                self.process_name = data["process_name"]
                self.sm.current = "scan"
            else:
                self.show_error(resp.json().get("detail", "登录失败"))
        except requests.exceptions.ConnectionError:
            self.show_error("无法连接服务器，请检查网络")
        except Exception as e:
            self.show_error(f"登录失败：{e}")

    def submit_record(self, sn):
        if not self._token:
            return False, "未登录"
        sn = sn.strip()
        if not sn:
            return False, "SN码为空"

        headers = {"Authorization": f"Bearer {self._token}"}
        payload = {
            "battery_sn": sn,
            "process_name": self.process_name,
            "device_id": self.device_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
        try:
            resp = requests.post(
                f"{self.server_url}/api/record",
                json=payload,
                headers=headers,
                timeout=5,
            )
            if resp.status_code == 200:
                try:
                    vibrator.vibrate(0.2)
                except:
                    pass
                return True, "记录成功"
            elif resp.status_code == 409:
                return False, "重复扫码，已忽略"
            elif resp.status_code == 401:
                self._token = None
                return False, "登录已过期，请重新登录"
            else:
                return False, resp.json().get("detail", "服务器错误")
        except requests.exceptions.ConnectionError:
            return False, "网络连接失败"
        except Exception as e:
            return False, f"请求异常：{e}"

    def logout(self):
        self.stop_scan()  # 退出扫描界面时关闭摄像头
        self._token = None
        self.process_name = ""
        self.operator_name = ""
        self.sm.current = "login"

    # ---------- 界面工具 ----------
    def show_settings(self):
        popup = Popup(
            title="关于", title_font=DEFAULT_FONT,
            content=Label(text=f"服务器: {self.server_url}\n智能电池工序追溯系统 v1.0", font_name=DEFAULT_FONT),
            size_hint=(0.7, 0.3),
        )
        popup.open()

    def show_server_settings(self):
        # 修复弹窗内容显示不全的问题：使用 ScrollView + 固定高度
        box = BoxLayout(orientation="vertical", spacing=10, padding=10)
        box.add_widget(Label(text="服务器地址:", font_name=DEFAULT_FONT, size_hint_y=None, height=30))
        url_input = TextInput(text=self.server_url, font_name=DEFAULT_FONT, size_hint_y=None, height=40)
        box.add_widget(url_input)

        btn_box = BoxLayout(size_hint_y=None, height=40, spacing=10)
        popup = Popup(title="网络设置", title_font=DEFAULT_FONT, content=box,
                      size_hint=(0.8, None), height="220dp")

        def save(instance):
            new_url = url_input.text.strip()
            if new_url:
                self.server_url = new_url
                save_server_url(new_url)
            popup.dismiss()

        btn_ok = Button(text="保存", font_name=DEFAULT_FONT, background_normal="",
                        background_color=(0.231, 0.49, 0.847, 1), color=(1, 1, 1, 0.92))
        btn_ok.bind(on_press=save)
        btn_cancel = Button(text="取消", font_name=DEFAULT_FONT, background_normal="",
                            background_color=(0.498, 0.549, 0.553, 1), color=(1, 1, 1, 0.92))
        btn_cancel.bind(on_press=popup.dismiss)
        btn_box.add_widget(btn_ok)
        btn_box.add_widget(btn_cancel)
        box.add_widget(btn_box)
        popup.open()

    def show_error(self, msg):
        popup = Popup(title="错误", title_font=DEFAULT_FONT,
                      content=Label(text=msg, font_name=DEFAULT_FONT),
                      size_hint=(0.7, 0.3))
        popup.open()


class LoginScreen(Screen):
    pass


class ScanScreen(Screen):
    def on_enter(self, *args):
        # 清空状态文字（不再显示“点击下方扫码按钮”）
        self.ids.status_label.text = ""
        self.ids.last_sn_label.text = ""
        # 如果之前有摄像头残留，清除
        app = App.get_running_app()
        if app.camera:
            app.stop_scan()

    def on_leave(self, *args):
        # 离开扫描界面时关闭摄像头，避免资源占用
        app = App.get_running_app()
        app.stop_scan()


if __name__ == "__main__":
    BatteryApp().run()

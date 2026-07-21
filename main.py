"""
智能电池工序追溯系统 - 手机采集端（纯文字版，震动反馈，记住密码，动态服务器地址）
Windows: 模拟扫码  |  Android: 真实摄像头 + 震动反馈
"""
import os
import json
import base64
from datetime import datetime
import requests
from kivy.app import App
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.checkbox import CheckBox
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.utils import platform
from plyer import uniqueid, vibrator

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

# ---------- KV 布局（纯文字）----------
KV = f'''
<InfoLabel@Label>:
    font_name: "{DEFAULT_FONT}"
    color: 0.173, 0.243, 0.314, 1
    font_size: "15sp"

<LoginScreen>:
    BoxLayout:
        orientation: "vertical"
        padding: "10dp"
        spacing: "5dp"
        canvas.before:
            Color:
                rgba: 0.945, 0.957, 0.965, 1
            Rectangle:
                pos: self.pos
                size: self.size

        # 顶部：网络设置按钮（右对齐）
        BoxLayout:
            size_hint_y: None
            height: "40dp"
            Button:
                text: "设置网络"
                font_name: "{DEFAULT_FONT}"
                font_size: "14sp"
                background_normal: ""
                background_color: 0,0,0,0
                color: 0.231, 0.490, 0.847, 1
                size_hint: None, None
                size: "80dp", "40dp"
                pos_hint: {{"right": 1}}
                on_press: app.show_server_settings()

        # 中间主体：垂直居中
        ScrollView:
            do_scroll_x: False
            do_scroll_y: True
            BoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: "15dp"
                padding: "20dp"
                pos_hint: {{"center_x": 0.5, "center_y": 0.5}}
                canvas:
                    Color:
                        rgba: 1, 1, 1, 1
                    RoundedRectangle:
                        radius: [18]
                        pos: self.pos
                        size: self.size

                InfoLabel:
                    text: "智能电池追溯系统"
                    font_size: "24sp"
                    halign: "center"
                    bold: True
                    size_hint_y: None
                    height: "50dp"

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

                BoxLayout:
                    size_hint_y: None
                    height: "40dp"
                    spacing: "5dp"
                    CheckBox:
                        id: remember_check
                        size_hint: None, None
                        size: "30dp", "30dp"
                    Label:
                        text: "记住密码"
                        font_name: "{DEFAULT_FONT}"
                        color: 0.173, 0.243, 0.314, 1

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

                # 底部留白（占位）
                Widget:
                    size_hint_y: None
                    height: "30dp"

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

        RelativeLayout:
            id: camera_box

        InfoLabel:
            id: status_label
            text: "等待扫码..."
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
        # 提前设置背景色，减少黑色闪屏
        Window.clearcolor = (0.945, 0.957, 0.965, 1)
        Window.softinput_mode = 'pan'  # 保留 pan 模式，配合 ScrollView 实现滚动

        Builder.load_string(KV)
        self._token = None
        self.title = "电池追溯"
        try:
            self.device_id = uniqueid.id
        except:
            self.device_id = "unknown"

        saved_username, saved_password = load_account()
        if saved_username:
            from kivy.clock import Clock
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

    def mock_scan_popup(self):
        box = BoxLayout(orientation="vertical", padding=10, spacing=10)
        sn_input = TextInput(hint_text="输入电池SN", font_name=DEFAULT_FONT, size_hint_y=None, height=40)
        box.add_widget(sn_input)
        btn_box = BoxLayout(size_hint_y=None, height=40, spacing=10)
        popup = Popup(title="模拟扫码", title_font=DEFAULT_FONT, content=box, size_hint=(0.8, 0.3))

        def do_submit(instance):
            sn = sn_input.text.strip()
            popup.dismiss()
            success, msg = self.submit_record(sn)
            scan_screen = self.sm.get_screen("scan")
            scan_screen.ids.status_label.text = f'{"成功" if success else "失败"}：{msg}'
            if success:
                scan_screen.ids.last_sn_label.text = sn

        btn_ok = Button(text="确定", font_name=DEFAULT_FONT, background_normal="",
                        background_color=(0.231, 0.49, 0.847, 1), color=(1, 1, 1, 0.92))
        btn_ok.bind(on_press=do_submit)
        btn_cancel = Button(text="取消", font_name=DEFAULT_FONT, background_normal="",
                            background_color=(0.498, 0.549, 0.553, 1), color=(1, 1, 1, 0.92))
        btn_cancel.bind(on_press=popup.dismiss)
        btn_box.add_widget(btn_ok)
        btn_box.add_widget(btn_cancel)
        box.add_widget(btn_box)
        popup.open()

    def logout(self):
        self._token = None
        self.process_name = ""
        self.operator_name = ""
        self.sm.current = "login"

    def show_settings(self):
        popup = Popup(
            title="关于", title_font=DEFAULT_FONT,
            content=Label(text=f"服务器: {self.server_url}\n智能电池工序追溯系统 v1.0", font_name=DEFAULT_FONT),
            size_hint=(0.7, 0.3),
        )
        popup.open()

    def show_server_settings(self):
        box = BoxLayout(orientation="vertical", padding=10, spacing=10)
        url_input = TextInput(text=self.server_url, font_name=DEFAULT_FONT, size_hint_y=None, height=50)
        box.add_widget(Label(text="服务器地址:", font_name=DEFAULT_FONT, size_hint_y=None, height=30))
        box.add_widget(url_input)
        btn_box = BoxLayout(size_hint_y=None, height=50, spacing=10)
        popup = Popup(title="网络设置", title_font=DEFAULT_FONT, content=box, size_hint=(0.85, 0.45))

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
        app = App.get_running_app()
        camera_box = self.ids.camera_box
        camera_box.clear_widgets()

        if platform == 'android':
            from kivy_garden.zbarcam import ZBarCam
            zbarcam = ZBarCam()
            zbarcam.bind(symbols=self.on_symbols)
            camera_box.add_widget(zbarcam)
        else:
            btn = Button(
                text="点此模拟扫码",
                font_name=DEFAULT_FONT,
                background_color=(0.231, 0.490, 0.847, 0.6),
                color=(1, 1, 1, 0.9),
                font_size="18sp",
            )
            btn.bind(on_press=lambda x: app.mock_scan_popup())
            camera_box.add_widget(btn)

    def on_symbols(self, instance, symbols):
        if not symbols:
            return
        code = symbols[0].data.decode('utf-8').strip()
        if not code:
            return
        app = App.get_running_app()
        success, msg = app.submit_record(code)
        self.ids.status_label.text = f'{"成功" if success else "失败"}：{msg}'
        if success:
            self.ids.last_sn_label.text = code


if __name__ == "__main__":
    BatteryApp().run()

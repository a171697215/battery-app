"""
智能电池工序追溯系统 - 手机采集端（Android 使用系统扫码 Intent，Windows 模拟）
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

# ---------- Android 扫码 Intent 所需依赖 ----------
if platform == 'android':
    try:
        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Intent = autoclass('android.content.Intent')
        RESULT_OK = autoclass('android.app.Activity').RESULT_OK
        RESULT_CANCELED = autoclass('android.app.Activity').RESULT_CANCELED
        # 可选：检测 ZXing 是否存在（不强制）
    except ImportError:
        print("⚠️ pyjnius 未安装，Android 扫码功能将不可用")

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

                # 底部占位，让卡片居中
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

        # 扫码按钮区域（替换原来的 camera_box）
        RelativeLayout:
            id: scan_button_box
            Button:
                id: scan_btn
                text: "📷 扫码"
                font_name: "{DEFAULT_FONT}"
                font_size: "24sp"
                background_color: 0.231, 0.490, 0.847, 0.85
                color: 1, 1, 1, 0.95
                pos_hint: {{"center_x": 0.5, "center_y": 0.5}}
                size_hint: 0.6, 0.5
                on_press: app.start_scan()

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
        Window.clearcolor = (0.945, 0.957, 0.965, 1)
        Window.softinput_mode = 'pan'

        Builder.load_string(KV)
        self._token = None
        self.title = "电池追溯"

        try:
            self.device_id = uniqueid.id
        except:
            self.device_id = "unknown"

        # 保存 Activity 回调引用（Android）
        self._scan_request_code = 12345
        self._pending_scan = False

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

    # ---------- Android Activity 结果回调 ----------
    def on_activity_result(self, request_code, result_code, intent):
        if request_code == self._scan_request_code and self._pending_scan:
            self._pending_scan = False
            if result_code == RESULT_OK and intent:
                scan_result = intent.getStringExtra('SCAN_RESULT')
                if scan_result:
                    self._handle_scan_result(scan_result)
                else:
                    self.show_error("扫码结果为空")
            else:
                self.show_error("扫码取消或失败")
                scan_screen = self.sm.get_screen("scan")
                scan_screen.ids.status_label.text = "扫码取消"

    def _handle_scan_result(self, code):
        scan_screen = self.sm.get_screen("scan")
        success, msg = self.submit_record(code)
        scan_screen.ids.status_label.text = f'{"成功" if success else "失败"}：{msg}'
        if success:
            scan_screen.ids.last_sn_label.text = code

    # ---------- 启动扫码（Android Intent）----------
    def start_scan(self):
        if platform != 'android':
            # Windows 模拟扫码
            self.mock_scan_popup()
            return

        try:
            # 创建 Intent（ZXing 标准扫码）
            intent = Intent()
            intent.setAction('com.google.zxing.client.android.SCAN')
            # 可添加 extra 参数
            intent.putExtra('SCAN_MODE', 'QR_CODE_MODE')  # 可选
            # 检测是否有应用能处理
            if not PythonActivity.mActivity.getPackageManager().queryIntentActivities(intent, 0).size():
                self.show_error("未安装扫码应用（如ZXing）")
                return
            # 启动 Activity 并等待结果
            PythonActivity.mActivity.startActivityForResult(intent, self._scan_request_code)
            self._pending_scan = True
        except Exception as e:
            self.show_error(f"启动扫码失败：{e}")

    def mock_scan_popup(self):
        box = BoxLayout(orientation="vertical", padding=10, spacing=10)
        sn_input = TextInput(hint_text="输入电池SN", font_name=DEFAULT_FONT, size_hint_y=None, height=40)
        box.add_widget(sn_input)
        btn_box = BoxLayout(size_hint_y=None, height=40, spacing=10)
        popup = Popup(title="模拟扫码", title_font=DEFAULT_FONT, content=box, size_hint=(0.8, 0.3))

        def do_submit(instance):
            sn = sn_input.text.strip()
            popup.dismiss()
            self._handle_scan_result(sn)

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
        box = BoxLayout(orientation="vertical", padding=10, spacing=10)
        url_input = TextInput(text=self.server_url, font_name=DEFAULT_FONT, size_hint_y=None, height=40)
        box.add_widget(Label(text="服务器地址:", font_name=DEFAULT_FONT, size_hint_y=None, height=30))
        box.add_widget(url_input)
        btn_box = BoxLayout(size_hint_y=None, height=40, spacing=10)

        popup = Popup(title="网络设置", title_font=DEFAULT_FONT, content=box, size_hint=(0.8, 0.5))

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
        # 清空状态
        self.ids.status_label.text = "点击下方扫码按钮"
        self.ids.last_sn_label.text = ""


if __name__ == "__main__":
    BatteryApp().run()

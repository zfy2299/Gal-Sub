import difflib
import sys
import os
import json
import time
import threading

import requests
import win32gui
from PIL import Image
import pynput
from PyQt5.QtWidgets import QApplication

from GUI import TextWindow
from rect_co import get_rect

window_name = ['深淵のラビリントス', '1.00']  # 可写部分
search_hwnd = -1
search_window_name = ''
keyword_listen = [
    pynput.keyboard.Key.enter,
    # pynput.keyboard.Key.space,
    pynput.keyboard.Key.down,
    pynput.keyboard.Key.right,
]
mouse_listen = [
    # pynput.mouse.Button.left
]
# 这个为主动无延迟
keyword_listen_immediately = [
    pynput.keyboard.Key.f4,
    pynput.keyboard.KeyCode(char="'"),
]
window_obj = None
rate_limit = 0.4  # 防抖
shot_delay = 0.35

# 不用管的变量
o_width = -1
o_height = -1
rect = []
all_text_content = {}
old_txt_index = -1


def run_rate_limit(func):
    last_called = 0

    def wrapper(*args, **kwargs):
        nonlocal last_called

        now = time.time()
        if now - last_called >= rate_limit:
            last_called = now
            return func(*args, **kwargs)

    return wrapper


def get_window_turtle():
    """
    获取所有的窗口，返回列表，列表每个元素为（窗口句柄，窗口名）
    :return:
    """

    def check_name(name):
        for sub_name in window_name:
            if sub_name not in name:
                return False
        return True

    def enum_windows_callback(hwnd_, windows__):
        if check_name(win32gui.GetWindowText(hwnd_)):
            windows__.append((hwnd_, win32gui.GetWindowText(hwnd_)))

    windows_ = []
    win32gui.EnumWindows(enum_windows_callback, windows_)
    return windows_


def similarity(s1, s2):
    return difflib.SequenceMatcher(None, s1, s2).ratio()


def post_ocr(jpg=os.path.join(os.getcwd(), 'ocr_temp.jpg'), ocr_url='http://127.0.0.1:6666/ocr/api'):
    body = {
        "Language": 'JAP',
        "ImagePath": jpg,
    }
    try:
        response = requests.post(ocr_url, data=json.dumps(body), verify=False)
        if response.status_code != 200:
            return '-1'
        if 'Data' not in json.loads(response.text):
            return '-1'
        res_text = ''
        for i in json.loads(response.text)['Data']:
            res_text += i['Words']
    except:
        res_text = 'OCR网络错误!'
    return res_text


def screenshot(hwnd_, crop_rect, origin_width, origin_height):
    # 循环截图
    img_q_ = screen.grabWindow(hwnd_).toImage()
    image__ = Image.fromqimage(img_q_)
    now_width = image__.width
    now_height = image__.height
    w_scale = now_width / origin_width
    h_scale = now_height / origin_height
    # 裁剪
    image__ = image__.crop(
        (crop_rect[0] * w_scale, crop_rect[1] * h_scale, crop_rect[2] * w_scale, crop_rect[3] * h_scale))
    image__.save("./ocr_temp.jpg")


def parse_txt_file(ocr_text):
    global old_txt_index
    if not os.path.exists(os.path.join(window_obj.txt_dir, '原文.txt')):
        return {}
    # 读取文本
    # print(all_text_content.keys())
    for file_name in window_obj.txt_file:
        if file_name not in all_text_content and os.path.exists(os.path.join(window_obj.txt_dir, f'{file_name}.txt')):
            with open(os.path.join(window_obj.txt_dir, f'{file_name}.txt'), encoding='utf-8') as f:
                all_text_content[file_name] = f.read().split('\n')
        elif file_name in all_text_content and not os.path.exists(os.path.join(window_obj.txt_dir, f'{file_name}.txt')):
            all_text_content.pop(file_name)
    # 寻找索引
    # print(all_text_content.keys())
    print(old_txt_index, end='  ')
    text_match = []
    if old_txt_index > 30:
        text_match = difflib.get_close_matches(ocr_text,
                                               all_text_content['原文'][old_txt_index - 30:old_txt_index + 30],
                                               1, 0.62)
        pass
    if len(text_match) > 0:
        index = all_text_content['原文'][old_txt_index - 30:old_txt_index + 30].index(text_match[0]) + old_txt_index - 30

    else:
        text_match = difflib.get_close_matches(ocr_text, all_text_content['原文'], 1, 0.6)
        if len(text_match) > 0:
            index = all_text_content['原文'].index(text_match[0])
        else:
            text_match = difflib.get_close_matches(ocr_text, all_text_content['原文'], 1, 0.5)
            if len(text_match) > 0:
                index = all_text_content['原文'].index(text_match[0])
            else:
                return {}
    old_txt_index = index
    # 加载各个译文
    res_ = {}
    for name_ in window_obj.txt_file:
        res_[name_] = all_text_content[name_][index]
    return res_


@run_rate_limit
def screenshot_ocr(delay=shot_delay):
    if win32gui.GetForegroundWindow() == search_hwnd:
        print('确认点击', end='  ')
        time.sleep(delay)
        screenshot(search_hwnd, rect, o_width, o_height)
        print('截图完成', end='  ')
        ocr_res = post_ocr()
        print('OCR完成', end='  ')
        txt_res = parse_txt_file(ocr_res)
        txt_res['识别'] = ocr_res
        print('解析完成')
        print(txt_res)
        # window_obj.text_browser_content['谷歌'].setHtml(window_obj.text_gen(txt_res['谷歌']))
        # window_obj.text_browser_flush(txt_res)
        return txt_res
    return {}


class MouseKeyboardListener(threading.Thread):

    def __init__(self):
        super().__init__()

    def run(self):
        pynput.mouse.Listener(on_click=self.on_click).start()
        with pynput.keyboard.Listener(on_press=self.on_press) as listener_:
            listener_.join()

    def on_click(self, _, __, button, pressed):
        if button in mouse_listen and pressed:
            temp = screenshot_ocr()
            self.emit(temp)
            temp = screenshot_ocr()
            self.emit(temp)
        return True

    def on_press(self, key):
        if key in keyword_listen:
            temp = screenshot_ocr()
            self.emit(temp)
            temp = screenshot_ocr()
            self.emit(temp)
        elif key in keyword_listen_immediately:
            temp = screenshot_ocr(0)
            self.emit(temp)
        return True

    @staticmethod
    def emit(t):
        if t != {} and t is not None:
            window_obj.text_accept_emit(t)


# 寻找窗口
windows = get_window_turtle()
if len(windows) == 0:
    input('没有找到指定窗口!')
    exit()
elif len(windows) == 1:
    search_hwnd = windows[0][0]
    search_window_name = windows[0][1]
else:
    for hwnd, title in windows:
        print(f"{hwnd}: {title}")
    print('------------')
    print('找到以上窗口，请确认目标是第几个')
    user_select = eval(input())
    search_hwnd = windows[user_select - 1][0]
    search_window_name = windows[user_select - 1][1]
print(f'锁定窗口：《{search_window_name}》，窗口句柄：{search_hwnd}')

# 初始化截图位置
app_1 = QApplication(sys.argv)
screen = QApplication.primaryScreen()
img_q = screen.grabWindow(search_hwnd).toImage()
image = Image.fromqimage(img_q)
o_width = image.width
o_height = image.height
image.save("./ocr_temp.jpg")
rect = get_rect('./ocr_temp.jpg')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window_obj = TextWindow()
    window_obj.text_browser_content['识别'].setHtml(window_obj.text_gen('等待文本'))
    # 监听鼠标与键盘
    listener = MouseKeyboardListener()
    listener.start()
    sys.exit(app.exec_())

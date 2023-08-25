import threading
import subprocess
import time
import psutil
from flask import Flask
import pygetwindow as gw
import sys
app = Flask(__name__)


class SandTimer:
    def __init__(self, timeout, callback):
        self.timeout = timeout
        self.callback = callback
        self.timer = None

    def start(self):
        if self.timer is not None:
            self.timer.cancel()
        self.timer = threading.Timer(self.timeout, self.callback)
        self.timer.start()

    def cancel(self):
        if self.timer is not None:
            self.timer.cancel()


def request_handler():
    print("接收到请求，重置沙漏")

    timer.start()

def restart_process():
    # 关闭已有进程
    for process in psutil.process_iter():
        if process.name() == 'python.exe' and 'app.py' in process.cmdline():
            process.kill()

    # 打印重启提示
    print('重启中...')

    # 启动新进程
    subprocess.Popen(['python', 'app.py'], shell=True)
def callback():
    print("沙子漏完了，执行某个函数")
    # 关闭已有进程
    # for process in psutil.process_iter():
    #     if process.name() == 'python.exe' and 'app.py' in process.cmdline():
    #         process.kill()

    restart_process()
    # 获取所有Python窗口
    # python_windows = gw.getWindowsWithTitle('Python')
    #
    # # 遍历窗口并关闭
    # for window in python_windows:
    #     if 'app.py' in window.title:
    #         window.close()
    #
    # # 打印重启提示
    # print('重启中...')
    #
    #
    # # 启动新进程
    # subprocess.Popen('cmd /c start cmd.exe /K python app.py', shell=True)


@app.route("/", methods=["GET", "POST"])
def hello():
    request_handler()
    return '1'


if __name__ == '__main__':
    part = int(input('输入沙漏翻转间隔'))
    timer = SandTimer(part, callback)
    import subprocess

    subprocess.Popen('cmd /c start cmd.exe /K python app.py', shell=True)
    # 打开新的CMD窗口并执行命令

    app.run(host="0.0.0.0", port=3000)
# while True:
#     # 模拟接收到请求
#     input('发送')
#     request_handler()

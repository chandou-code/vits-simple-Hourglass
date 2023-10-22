# vits-simple-Hourglass
基于https://github.com/Artrajz/vits-simple-api    的内存溢出问题:合成完一次语音以后无法释放内存，导致内存占用高达4g无法得到释放

通过翻转'沙漏'自动重启cmd以达到释放内存，在上一次请求过后的一段时间内如果没有新的请求，就重启cmd,重启以后内存恢复正常，并且处于正常开启状态。 可以自定义释放间隔。
两种用法:
1.直接替换app.py
2.在原项目的app.py里内加两行代码:

    url = 'http://127.0.0.1:3000/'
    r = requests.get(url)
    
  具体位置:

    @require_api_key
    def voice_vits_api():
        url = 'http://127.0.0.1:3000/'
        r = requests.get(url)

    try:

        if request.method == "GET":

最后只需要把Hourglass.py放到app.py的同级目录下，然后运行Hourglass.py即可

(改了一下 这回不会打团的时候突然弹出cmd了

import os
import logging
import time
import logzero
import uuid

import requests
from flask import Flask, request, send_file, jsonify, make_response, render_template

from werkzeug.utils import secure_filename
from flask_apscheduler import APScheduler
from functools import wraps
from utils.utils import clean_folder, check_is_none
from utils.merge import merge_model
from io import BytesIO
import torch

# from flask_caching import Cache


app = Flask(__name__)
# cache = Cache(app)
app.config.from_pyfile("config.py")
# app.config['CACHE_TYPE'] = 'simple'
scheduler = APScheduler()
scheduler.init_app(app)
if app.config.get("CLEAN_INTERVAL_SECONDS", 3600) > 0:
    scheduler.start()

logzero.loglevel(logging.WARNING)
logger = logging.getLogger("vits-simple-api")
level = app.config.get("LOGGING_LEVEL", "DEBUG")
level_dict = {'DEBUG': logging.DEBUG, 'INFO': logging.INFO, 'WARNING': logging.WARNING, 'ERROR': logging.ERROR,
              'CRITICAL': logging.CRITICAL}
logging.basicConfig(level=level_dict[level])
logging.getLogger('numba').setLevel(logging.WARNING)
# os.environ["CUDA_VISIBLE_DEVICES"] = "0"
tts = merge_model(app.config["MODEL_LIST"])

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

if not os.path.exists(app.config['CACHE_PATH']):
    os.makedirs(app.config['CACHE_PATH'], exist_ok=True)


def require_api_key(func):
    @wraps(func)
    def check_api_key(*args, **kwargs):
        if not app.config.get('API_KEY_ENABLED', False):
            return func(*args, **kwargs)
        else:
            api_key = request.args.get('api_key') or request.headers.get('X-API-KEY')
            if api_key and api_key == app.config['API_KEY']:
                return func(*args, **kwargs)
            else:
                return make_response(jsonify({"status": "error", "message": "Invalid API Key"}), 401)

    return check_api_key


@app.route('/', methods=["GET", "POST"])
def index():
    kwargs = {
        "speakers": tts.voice_speakers,
        "speakers_count": tts.speakers_count
    }
    return render_template("index.html", **kwargs)


@app.route('/voice', methods=["GET", "POST"])
@app.route('/voice/vits', methods=["GET", "POST"])
# @cache.cached(timeout=300)  # 设置缓存时间为 300 秒
@require_api_key
def voice_vits_api():

    url = 'http://127.0.0.1:3000/'
    r = requests.get(url)

        # print('3000端口未开')

    try:

        if request.method == "GET":
            text = request.args.get("text", "")
            id = int(request.args.get("id", app.config.get("ID", 0)))
            format = request.args.get("format", app.config.get("FORMAT", "wav"))
            lang = request.args.get("lang", app.config.get("LANG", "auto"))
            length = float(request.args.get("length", app.config.get("LENGTH", 1)))
            noise = float(request.args.get("noise", app.config.get("NOISE", 0.34)))
            noisew = float(request.args.get("noisew", app.config.get("NOISEW", 0.8)))
            max = int(request.args.get("max", app.config.get("MAX", 300)))
            use_streaming = request.args.get('streaming', False, type=bool)
        elif request.method == "POST":
            content_type = request.headers.get('Content-Type')
            if content_type == 'application/json':
                data = request.get_json()
            else:
                data = request.form
            text = data.get("text", "")
            id = int(data.get("id", app.config.get("ID", 0)))
            format = data.get("format", app.config.get("FORMAT", "wav"))
            lang = data.get("lang", app.config.get("LANG", "auto"))
            length = float(data.get("length", app.config.get("LENGTH", 1)))
            noise = float(data.get("noise", app.config.get("NOISE", 0.34)))
            noisew = float(data.get("noisew", app.config.get("NOISEW", 0.8)))
            max = int(data.get("max", app.config.get("MAX", 300)))
            use_streaming = request.form.get('streaming', False, type=bool)
    except Exception as e:
        logger.error(f"[VITS] {e}")
        return make_response("parameter error", 400)

    logger.info(f"[VITS] id:{id} format:{format} lang:{lang} length:{length} noise:{noise} noisew:{noisew}")
    logger.info(f"[VITS] len:{len(text)} text：{text}")

    if check_is_none(text):
        logger.info(f"[VITS] text is empty")
        return make_response(jsonify({"status": "error", "message": "text is empty"}), 400)

    if check_is_none(id):
        logger.info(f"[VITS] speaker id is empty")
        return make_response(jsonify({"status": "error", "message": "speaker id is empty"}), 400)

    if id < 0 or id >= tts.vits_speakers_count:
        logger.info(f"[VITS] speaker id {id} does not exist")
        return make_response(jsonify({"status": "error", "message": f"id {id} does not exist"}), 400)

    # 校验模型是否支持输入的语言
    speaker_lang = tts.voice_speakers["VITS"][id].get('lang')
    if lang.upper() != "AUTO" and lang.upper() != "MIX" and len(speaker_lang) != 1 and lang not in speaker_lang:
        logger.info(f"[VITS] lang \"{lang}\" is not in {speaker_lang}")
        return make_response(jsonify({"status": "error", "message": f"lang '{lang}' is not in {speaker_lang}"}), 400)

    # 如果配置文件中设置了LANGUAGE_AUTOMATIC_DETECT则强制将speaker_lang设置为LANGUAGE_AUTOMATIC_DETECT
    if app.config.get("LANGUAGE_AUTOMATIC_DETECT", []) != []:
        speaker_lang = app.config.get("LANGUAGE_AUTOMATIC_DETECT")

    if use_streaming and format.upper() != "MP3":
        format = "mp3"
        logger.warning("Streaming response only supports MP3 format.")

    fname = f"{str(uuid.uuid1())}.{format}"
    file_type = f"audio/{format}"
    task = {"text": text,
            "id": id,
            "format": format,
            "length": length,
            "noise": noise,
            "noisew": noisew,
            "max": max,
            "lang": lang,
            "speaker_lang": speaker_lang}

    if app.config.get("SAVE_AUDIO", False):
        logger.debug(f"[VITS] {fname}")

    if use_streaming:
        audio = tts.stream_vits_infer(task, fname)
        response = make_response(audio)
        response.headers['Content-Disposition'] = f'attachment; filename={fname}'
        response.headers['Content-Type'] = file_type
        return response
    else:
        t1 = time.time()
        audio = tts.vits_infer(task, fname)
        t2 = time.time()
        logger.info(f"[VITS] finish in {(t2 - t1):.2f}s")
        return send_file(path_or_file=audio, mimetype=file_type, download_name=fname)


@app.route('/if', methods=["GET"])
def if_online():
    return 'True'


# regular cleaning
@scheduler.task('interval', id='clean_task', seconds=app.config.get("CLEAN_INTERVAL_SECONDS", 3600),
                misfire_grace_time=900)
def clean_task():
    clean_folder(app.config["UPLOAD_FOLDER"])
    clean_folder(app.config["CACHE_PATH"])


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=app.config.get("PORT", 23456), debug=app.config.get("DEBUG", False),
            threaded=False)  # 对外开放
    # app.run(host='127.0.0.1', port=app.config.get("PORT",23456), debug=True)  # 本地运行、调试

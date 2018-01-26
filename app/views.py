#-*- coding=utf-8 -*-
from app import app, db
from app.models import *
from flask import render_template, redirect, request, url_for, flash, session, jsonify, make_response
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import subprocess
import os
from datetime import datetime
#from .tumblr_task import TumblrGet
import re
import requests
import os
from hashlib import md5
import string
import random
from .capture import ImageChar
import StringIO
from app import db
from app.models import Context
import parser
from config import *


basedir = os.path.abspath('.')
clawer = os.path.join(basedir, 'tumblr.py')

#VIDEOREGEX = re.compile('http://media.tumblr.com/(.*?)_frame1')
VIDEOREGEX = re.compile(
    '<meta property="og:image".*?media.tumblr.com/tumblr_(.*?)_')
POSTERREGEX = re.compile('<meta property="og:image" content="(.*?)"')
IMAGEREGEX = re.compile(
    '<meta property="og:image" content="(.*?)" /><meta property="og:image:height"')
vhead = 'https://vt.tumblr.com/tumblr_%s.mp4'
HOME = 'http://%s.tumblr.com/api/read?&num=50'


def check(uid):
    url = HOME % uid
    try:
        cont = requests.get(url)
        if cont.ok:
            if int(re.findall('<posts start="0" total="(.*?)">', cont.content)[0]) != 0:
                return True
            else:
                return False
        else:
            return False
    except:
        return False


def getmd5():
    a = md5()
    letters = string.ascii_letters + string.digits
    randchar = ''.join(random.sample(letters, 5))
    a.update(randchar)
    return a.hexdigest()


@app.context_processor
def form_trans():
    return dict(method='method')


@app.route('/')
def index():
    hash_ = getmd5()
    session['hash'] = hash_
    return render_template('base.html', hash_=hash_)


@app.route('/api', methods=['POST'])
def api():
    url = request.form.get('url')
    hash_ = request.form.get('hash')
    captcha_code = request.form.get('captcha_code')
    if captcha_code is not None:
        if captcha_code == session.get('captcha'):
            return jsonify({'captcha': 'pass'})
    if hash_ != session.get('hash'):
        return jsonify({'captcha': 'ok'})
    else:
        retdata = {}
        # tumblr单个视频解析
        if 'tumblr.com/post' in url:
            try:
                video = ''
                cont = requests.get(url).content
                pictures = IMAGEREGEX.findall(cont)
                vid = VIDEOREGEX.findall(cont)
                poster = POSTERREGEX.findall(cont)
                isvideo = 0
                if vid:
                    video = vhead % vid[0]
                    poster = poster[0]
                    isvideo = 1
                    # flash('解析成功')
                    retdata['status'] = 'ok'
                    retdata['total'] = 1
                    retdata['pages'] = 1
                    retdata['video'] = [
                        {'url': video, 'desc': '', 'thumb': poster}]
                    return jsonify(retdata)
                else:
                    # flash('解析失败')
                    retdata['status'] = 'fail'
                    retdata['message'] = '解析失败，请联系站长解决'
                    return jsonify(retdata)
            except Exception, e:
                print e
                # flash('解析失败')
                retdata['status'] = 'fail'
                retdata['message'] = '解析失败，请联系站长解决'
                return jsonify(retdata)
        # tumblr批量解析
        if 'tumblr.com' in url:
            id = re.findall('://(.*?)\.', url)[0]
            if check(id):
                is_exists = ID.query.filter_by(id=id).first()
                if is_exists is None:
                    now = datetime.now()
                    inserttime = now.strftime('%Y%m%d %H:%M:%S')
                    a = ID(id=id, updateTime=inserttime, parseTimes=1)
                    db.session.add(a)
                    db.session.commit()
                    retdata['status'] = 'fail'
                    retdata['message'] = '正在解析，请稍等15s再试！'
                    subprocess.Popen('python {clawer} {id}'.format(
                        clawer=clawer, id=id), shell=True)
                    return jsonify(retdata)
                else:
                    now = datetime.now()
                    is_exists.updateTime = now.strftime('%Y%m%d %H:%M:%S')
                    is_exists.parseTimes += 1
                    db.session.add(is_exists)
                    db.session.commit()
                    subprocess.Popen('python {clawer} {id}'.format(
                        clawer=clawer, id=id), shell=True)
                    retdata['status'] = 'ok'
                    retdata['total'] = 50
                    retdata['pages'] = 1
                    videos = Context.query.filter_by(
                        id=id, isvideo=1).limit(50).all()
                    for video in videos:
                        retdata.setdefault('video', []).append(
                            {'url': video.urls, 'desc': '', 'thumb': video.poster})
                    return jsonify(retdata)
            else:
                # flash('解析失败')
                retdata['status'] = 'fail'
                retdata['message'] = '解析失败，请联系站长解决'
                return jsonify(retdata)
        # 2mm
        else:
            try:
                video,title,picture=parser.main(url)
                retdata['status'] = 'ok'
                retdata['total'] = 1
                retdata['pages'] = 1
                retdata['video'] = [
                    {'url': video, 'desc': title, 'thumb': picture}]
                return jsonify(retdata)
            except Exception,e:
                print e
                retdata['status'] = 'fail'
                retdata['message'] = '解析网站不存在'
                return jsonify(retdata)



@app.route('/captcha', methods=['POST'])
def captcha():
    ic = ImageChar(fontColor=(100, 211, 90))
    strs, code_img = ic.randChinese(4)
    session['captcha'] = strs
    buf = StringIO.StringIO()
    code_img.save(buf, 'JPEG', quality=80)
    buf_str = buf.getvalue()
    response = current_app.make_response(buf_str)
    response.headers['Content-Type'] = 'image/jpeg'
    return response


@app.route('/get', methods=['POST', 'GET'])
def getTumblr():
    if request.method == 'POST':
        id = request.form.get('id')
        if 'tumblr.com/post' in id:
            try:
                video = ''
                cont = requests.get(id).content
                pictures = IMAGEREGEX.findall(cont)
                vid = VIDEOREGEX.findall(cont)
                poster = POSTERREGEX.findall(cont)
                isvideo = 0
                if vid:
                    video = vhead % vid[0]
                    poster = poster[0]
                    isvideo = 1
                if len(vid) + len(pictures) <> 0:
                    flash('解析成功')
                    return render_template('show_single.html', video=video, pictures=pictures, poster=poster, isvideo=isvideo)
                else:
                    flash('解析失败')
                    return redirect(url_for('index'))
            except Exception, e:
                print e
                flash('解析失败')
                return redirect(url_for('index'))
        else:
            if check(id):
                is_exists = ID.query.filter_by(id=id).first()
                if is_exists is None:
                    now = datetime.now()
                    inserttime = now.strftime('%Y%m%d %H:%M:%S')
                    a = ID(id=id, updateTime=inserttime, parseTimes=1)
                    db.session.add(a)
                    db.session.commit()
                else:
                    now = datetime.now()
                    is_exists.updateTime = now.strftime('%Y%m%d %H:%M:%S')
                    is_exists.parseTimes += 1
                    db.session.add(is_exists)
                    db.session.commit()
                subprocess.Popen('python {clawer} {id}'.format(
                    clawer=clawer, id=id), shell=True)
                return redirect(url_for('showid', id=id))
            else:
                flash('解析失败')
                return redirect(url_for('index'))
    return 'hello world'


@app.route('/show/<id>')
def showid(id):
    videos = Context.query.filter_by(id=id, isvideo=1).limit(10).all()
    pictures = Context.query.filter_by(id=id, isvideo=0).limit(10).all()
    if len(videos) + len(pictures) == 0:
        isparse = 0
    else:
        isparse = 1
    return render_template('show.html', id=id, videos=videos, pictures=pictures, isparse=isparse)


@app.route('/showmore')
def showmore():
    id = request.args.get('id')
    type = request.args.get('type')
    page = request.args.get('page', 1, type=int)
    if type == 'video':
        pagination = Context.query.filter_by(id=id, isvideo=1).paginate(
            page, per_page=20, error_out=False)
    else:
        pagination = Context.query.filter_by(id=id, isvideo=0).paginate(
            page, per_page=20, error_out=False)
    items = pagination.items
    return render_template('showmore.html', id=id, pagination=pagination, type=type, items=items)


@app.route('/download')
def download():
    id = request.args.get('id')
    type = request.args.get('type')
    if type == 'video':
        isvideo = 1
    else:
        isvideo = 0
    query_result = Context.query.filter_by(id=id, isvideo=isvideo).all()
    if len(query_result) <> 0:
        content = ''
        for line in query_result:
            content += '%s\n' % line.urls
        response = make_response(content)
        response.headers["Content-Disposition"] = "attachment; filename=%s.txt" % (
            id + "_" + type)
        return response
    else:
        return redirect(url_for('index'))

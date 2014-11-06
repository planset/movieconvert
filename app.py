#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import subprocess
import sys
import urllib
import re
from flask import (Flask, request, session, g, redirect,
                   url_for, render_template, flash, 
                   abort, send_from_directory, jsonify)
from flask.ext.sqlalchemy import SQLAlchemy
from werkzeug import secure_filename

ALLOWD_EXTENSIONS = set(['wmv', 'avi', 'flv'])
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['UPLOAD_FOLDER'] = os.path.join(CURRENT_DIR, 'data/')
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024 * 1024 # 1G まで

db = SQLAlchemy(app)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.Text)
    mp4_filename = db.Column(db.Text)
    path = db.Column(db.Text)
    state = db.Column(db.Integer)

db.create_all()


@app.route('/')
def index():
    return 'ok'

@app.route('/upload', methods=['POST'])
def upload():
    res = {
            'result': 'ng',
            'id' : 0
            }

    f = request.files.get('file')

    if f and allowed_file(f.filename):
        filename = urllib.parse.unquote_plus(f.filename)

        movie = Movie()
        movie.filename = filename
        movie.mp4_filename = to_mp4_filename(filename)
        movie.state = 0
        db.session.add(movie)
        db.session.commit()

        _, ext = os.path.splitext(filename)
        savepath = os.path.join(app.config['UPLOAD_FOLDER'], str(movie.id) + ext)
        f.save(savepath)

        movie.path = savepath
        db.session.add(movie)
        db.session.commit()

        res['result'] = 'ok'
        res['id'] = movie.id
        res['mp4_filename'] = movie.mp4_filename

    return jsonify(res)


@app.route('/download/<int:id>', methods=['GET'])
def download(id):
    movie = Movie.query.get_or_404(id)

    output_filename = str(movie.id) + '.mp4'
    if movie.state == 0:
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)

        result = convert(movie.path, output_path)

        if not result:
            return jsonify(result='ng')

        movie.state = 1
        db.session.add(movie)
        db.session.commit()

    return send_from_directory(app.config['UPLOAD_FOLDER'], 
            output_filename, as_attachment=True)


def to_mp4_filename(filename):
    filename, ext = os.path.splitext(filename)
    return filename + '.mp4'

def allowed_file(filename):
    return '.' in filename and \
         filename.rsplit('.', 1)[1] in ALLOWD_EXTENSIONS


def movieinfo(movie_path):
    """
    stderr sample 
    
avconv version 9.16-6:9.16-0ubuntu0.14.04.1, Copyright (c) 2000-2014 the Libav developers
  built on Aug 10 2014 18:16:02 with gcc 4.8 (Ubuntu 4.8.2-19ubuntu1)
[mpeg4 @ 0x15d4580] Invalid and inefficient vfw-avi packed B frames detected
Guessed Channel Layout for  Input Stream #0.1 : stereo
Input #0, mov,mp4,m4a,3gp,3g2,mj2, from 'data/99.mp4':
  Metadata:
    major_brand     : isom
    minor_version   : 512
    compatible_brands: isomiso2mp41
    encoder         : Lavf54.20.4
  Duration: 00:04:03.90, start: 0.000000, bitrate: 933 kb/s
    Stream #0.0(und): Video: mpeg4, yuv420p, 720x576 [PAR 1:1 DAR 5:4], 771 kb/s, 20.02 fps, 20.02 tbr, 8000k tbn, 30k tbc
    Stream #0.1(und): Audio: mp3, 32000 Hz, stereo, s16p, 159 kb/s
At least one output file must be specified
    """
    out = ""
    err = ""
    try:
        p = subprocess.Popen(['/usr/bin/avconv','-i',movie_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        m = re.search(r'Stream.*?Video:.+?,.+?, ([0-9]+)x([0-9]+),.*', err.decode()).groups()
        return int(m[0]), int(m[1])
    except Exception as e:
        print(e.message)
        pass

def _fix_divisible_by_2_cmd(w, h, input_path, output_path):
    if (w % 2 == 1):
        w += 1
    if (h % 2 == 1):
        h += 1

    return ['/usr/bin/avconv',
            '-i', input_path,
            '-ar', '22050',
            '-c:v', 'libx264',
            '-s', str(w)+'x'+str(h),
            '-y',
            '-strict', 'experimental',
            output_path
            ]
    
res = _fix_divisible_by_2_cmd(463, 275, 'a', 'b')
assert res == ['/usr/bin/avconv',
            '-i', 'a',
            '-ar', '22050',
            '-c:v', 'libx264',
            '-s', '464x276',
            '-y',
            '-strict', 'experimental',
            'b' 
            ]


def convert(input_path, output_path):

    CMD1 = ['/usr/bin/avconv',
            '-i', input_path,
            '-vcodec', 'copy',
            '-acodec', 'copy',
            '-y',
            '-strict', 'experimental',
            output_path
            ]

    CMD2 = ['/usr/bin/avconv',
            '-i', input_path,
            '-ar', '22050',
            '-c:v', 'libx264',
            '-y',
            '-strict', 'experimental',
            output_path
            ]

    out = ""
    err = ""
    try:
        print('EXECUTE: ' + ' '.join(CMD1))
        p = subprocess.Popen(CMD1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        print("")
        print('OUTPUT: ' + err.decode())
        print("")

        if p.returncode == 0:
            os.remove(input_path)
            return True
    except Exception as ex:
        print(ex)

    try:
        print('EXECUTE: ' + ' '.join(CMD2))
        p = subprocess.Popen(CMD2, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        print("")
        print('OUTPUT: ' + err.decode())
        print("")
        if p.returncode == 0:
            os.remove(input_path)
            return True
    except Exception as ex:
        print(ex)

    try:
        w, h = movieinfo(input_path)
        if(w%2 == 1 or h%2 == 1):
            CMD3 = _fix_divisible_by_2_cmd(w, h, input_path, output_path)
            print('EXECUTE: ' + ' '.join(CMD3))
            p = subprocess.Popen(CMD3, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate()
            print("")
            print('OUTPUT: ' + err.decode())
            print("")
            if p.returncode == 0:
                os.remove(input_path)
                return True
    except Exception as ex:
        print(ex)

    sys.stderr.write('CONVERT ERROR : ' + input_path + '\n')
    os.remove(output_path)
    return False



if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)

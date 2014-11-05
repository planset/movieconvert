#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import subprocess
import sys
import urllib
from flask import (Flask, request, session, g, redirect,
                   url_for, render_template, flash, 
                   abort, send_from_directory, jsonify)
from flask.ext.sqlalchemy import SQLAlchemy
from werkzeug import secure_filename

ALLOWD_EXTENSIONS = set(['wmv', 'avi', 'flv'])

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['UPLOAD_FOLDER'] = '/home/daisuke/videoconverter/data/'
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

    try:
        p = subprocess.Popen(CMD1)
        p.communicate()
        if p.returncode == 0:
            os.remove(input_path)
            return True
    except:
        pass

    try:
        p = subprocess.Popen(CMD2)
        p.communicate()
        if p.returncode == 0:
            os.remove(input_path)
            return True
    except:
        pass

    sys.stderr.write('CONVERT ERROR : ' + input_path + '\n')
    os.remove(output_path)
    return False



if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)

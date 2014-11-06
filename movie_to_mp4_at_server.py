#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import urllib
import requests
from requests_toolbelt import MultipartEncoderMonitor

HOST = '10.1.3.81'
PORT = 5000
server = 'http://{host}:{port}/'.format(host=HOST, port=PORT)
upload_url = server + 'upload'
download_url = server + 'download'

def upload(url, input_path):
    if not os.path.exists(input_path):
        sys.exit(2)
    filesize = os.stat(input_path).st_size

    filename = os.path.basename(input_path)
    filename = urllib.parse.quote_plus(filename)

    def callback(monitor):
        print('\ruploading:     ', end="")
        print('\ruploading: ' + str(round(100*monitor.bytes_read/filesize)) + '%', end="")

    m = MultipartEncoderMonitor.from_fields(
            fields={'file': (filename, open(input_path, 'rb'))},
            callback=callback
            )

    r = requests.post(upload_url, data=m,
            headers={'Content-Type': m.content_type})

    d = r.json()
    if d['result'] == 'ng':
        sys.stderr.write('upload fail \n')
        sys.exit(1)

    print("")
    print('id=' + str(d['id']) +', mp4_filename=' + d['mp4_filename'])

    return d['id'], d['mp4_filename']

def download(url, id, output_path):

    r = requests.get(url + '/' + str(id), stream=True)

    if r.headers.get('Content-Type', '') == 'application/json':
        print('ERROR')
        return False

    print(r.headers)
    filesize = int(r.headers.get('Content-Length', 1))

    chunk_size = 8192
    bytes_read = 0
    with open(output_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size):
            f.write(chunk)
            bytes_read += chunk_size
            print('\rdownloading:     ', end="")
            print('\rdownloading: ' + str(round(100*bytes_read/filesize)) + '%', end="")

    print("")
    return True

def main():
    if len(sys.argv) != 2:
        print('USAGE: ./movie_to_mp4_at_server.py INPUT_FILE_PATH')
        sys.exit(1)

    input_path = sys.argv[1]
    input_dir = os.path.dirname(input_path)

    print('target: ' + input_path)
    id, mp4_filename = upload(upload_url, input_path)

    output_path = os.path.join(input_dir, mp4_filename)
    result = download(download_url, id, output_path)

    if result:
        os.remove(input_path)

    print("")
    sys.exit(0)

if __name__ == '__main__':
    main()

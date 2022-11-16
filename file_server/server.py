#!/usr/bin/env python

import os
from flask import Flask, make_response, send_file, abort
import zipfile
from hashlib import sha256

port = 5001
app = Flask(__name__)


def generate_digest(file_name):    
    BUF_SIZE = 65536
    digest = sha256()

    with open(file_name, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break            
            digest.update(data)

    return digest.hexdigest()

@app.route('/get-digest/<path:filename>')
def get_digest(filename):
    print("[info] requested digest")
    update_archive_pathname = f"data/{filename}"
    print("[info]", update_archive_pathname)
    update_source_pathname = "data/app-update.py"
    arcname = 'app.py'    
    try:
        # repack the source file for simplicity
        update_file = zipfile.ZipFile(update_archive_pathname, 'w', compression = zipfile.ZIP_DEFLATED)
        update_file.write(update_source_pathname, arcname=arcname,compresslevel=1)
        update_file.close()
        
        digest = generate_digest(update_archive_pathname)        
        return f"{digest} sha256 {filename}"        
    except FileNotFoundError as e:
        print("[error]", e, os.getcwd())
        abort(404)

@app.route('/download-update/<path:filename>')
def get_update(filename):
    update_archive_pathname = f"data/{filename}"
    update_source_pathname = "data/app-update.py"
    arcname = 'app.py'
    try:
        update_file = zipfile.ZipFile(update_archive_pathname, 'w', compression = zipfile.ZIP_DEFLATED)
        update_file.write(update_source_pathname, arcname=arcname,compresslevel=1)
        update_file.close()
        
        response = make_response(
            send_file(
                path_or_file=f'data/{filename}', 
                mimetype = 'zip', 
                as_attachment=True, 
                download_name=filename
                )
            )
        response.headers['digest'] = generate_digest(update_archive_pathname)
        response.headers['digest_alg'] = 'sha256'

        return response        
    except FileNotFoundError as e:
        print("[error]", e, os.getcwd())
        abort(404)

if __name__ == "__main__":        # on running python app.py
    app.run(port=port, host="0.0.0.0")
from flask import Flask, render_template, request, send_from_directory, redirect, url_for
from cryptography.fernet import Fernet
import qrcode
import os
from pathlib import Path
import uuid
import zipfile

app = Flask(__name__)

@app.route('/', methods=('GET', 'POST'))
def index():
    if request.method == "POST":
        batch = request.form.get("batch", True)
        amount = request.form.get("amount", True)
        dueDate = request.form.get("dueDate", True)

        dict_variables = {"batch": batch, "amount": amount, "dueDate": dueDate}

        uuid_list = []
        
        for i in range(int(amount)):
            uuid_name = uuid.uuid4()
            dict_variables['uuid'] = uuid_name
            uuid_list.append(uuid_name)
            dict_serializer = str(dict_variables)

            key = Fernet.generate_key()

            fernet = Fernet(key)

            enctex = fernet.encrypt(dict_serializer.encode())
            
            img = qrcode.make(enctex)
        
            path_to_download_folder = str(os.path.join(Path.home(), "Downloads"))
            img.save(f'{path_to_download_folder}/{uuid_name}')

        
        with zipfile.ZipFile(f"{path_to_download_folder}/{batch}.zip", mode='a') as my_zip:
            # add each file to the ZIP archive
            for file in uuid_list:
                my_zip.write(f'{path_to_download_folder}/{file}')
                os.remove(f'{path_to_download_folder}/{file}')
        
        
        return render_template('index.html')

    
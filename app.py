from flask import Flask, render_template, request, jsonify
from cryptography.fernet import Fernet
import qrcode
import os
from pathlib import Path
import uuid
import zipfile
from flask import Flask,render_template, request
from flask_mysqldb import MySQL

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'mysql'
app.config['MYSQL_DB'] = 'c4i'
 
mysql = MySQL(app)

@app.route('/', methods=('GET', 'POST'))
def index():
    if request.method == "POST":
        batch = request.form.get("batch", True)
        amount = request.form.get("amount", True)
        dueDate = request.form.get("dueDate", True)

        dict_variables = {"batch": batch, "amount": amount, "dueDate": dueDate}

        internal_list = []
        external_list = []

        cursor = mysql.connection.cursor()
        
        for i in range(int(amount)):
            uuid_internal = uuid.uuid4()
            internal_list.append(str(uuid_internal)+f'__{i}')
            uuid_external = uuid.uuid3(uuid.NAMESPACE_URL, str(dict_variables))
            external_list.append(str(uuid_external)+f'__{i}')

            dict_variables["uuid"] = uuid_external

            dict_serializer = str(dict_variables)

            hash_value = hash(dict_serializer)

            key = Fernet.generate_key()

            fernet = Fernet(key)

            enctex_internal = fernet.encrypt(str(uuid_internal).encode())
            enctex_external = fernet.encrypt(str(dict_serializer).encode())
            
            img_internal = qrcode.make(enctex_internal)
            img_external = qrcode.make(enctex_external)
        
            path_to_download_folder = str(os.path.join(Path.home(), "Downloads"))
            img_internal.save(f'{path_to_download_folder}/{uuid_internal}__{i}')
            img_external.save(f'{path_to_download_folder}/{uuid_external}__{i}')

            cursor.execute(''' INSERT INTO identificadores (internal_qr, external_qr, hash) VALUES(%s,%s,%s)''',(enctex_internal,enctex_external, hash_value))
        
        mysql.connection.commit()
        cursor.close()

        
        with zipfile.ZipFile(f"{path_to_download_folder}/{batch}_internal.zip", mode='a') as my_zip:
            for file in internal_list:
                my_zip.write(f'{path_to_download_folder}/{file}')
                os.remove(f'{path_to_download_folder}/{file}')

        with zipfile.ZipFile(f"{path_to_download_folder}/{batch}_external.zip", mode='a') as my_zip:
            for file in external_list:
                my_zip.write(f'{path_to_download_folder}/{file}')
                os.remove(f'{path_to_download_folder}/{file}')
        
        return render_template('index.html')


@app.route('/qrs', methods=['POST'])                                                                                                    
def add():                                                                                                                              
    data = request.json
    internal_qr = request.json["internal_qr"]
    external_qr = request.json["external_qr"]

    cursor = mysql.connection.cursor()
    result = cursor.execute(''' SELECT id FROM identificadores WHERE internal_qr=%s AND external_qr=%s''',(internal_qr,external_qr))
    mysql.connection.commit()
    cursor.close()

    if(result == 0): 
        return jsonify(
            match=False
        )
    else: 
        return jsonify(
            match=True
        )
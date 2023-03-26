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

            qr1 = qrcode.QRCode(box_size=5, border=1)
            qr1.add_data(enctex_internal)

            qr2 = qrcode.QRCode(box_size=1, border=1)
            qr2.add_data(enctex_external)

            qr1_image = qr1.make_image()
            qr2_image = qr2.make_image()

            path_to_download_folder = str(os.path.join(Path.home(), "Downloads"))

            qr1_image.save(f'{path_to_download_folder}/{uuid_internal}__{i}')
            qr2_image.save(f'{path_to_download_folder}/{uuid_external}__{i}')                

            counter = 0

            cursor.execute(''' INSERT INTO identificadores (internal_qr, external_qr, hash, counter) VALUES(%s,%s,%s,%s)''',(enctex_internal,enctex_external, hash_value, counter))
        
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
    cursor.execute(''' SELECT id, counter FROM identificadores WHERE internal_qr=%s AND external_qr=%s''',(internal_qr,external_qr))
    results = cursor.fetchall()

    counter = int(results[0][1]) + 1
    cursor.execute(''' UPDATE identificadores SET counter = %s WHERE internal_qr=%s AND external_qr=%s''',(counter, internal_qr,external_qr))
    cursor.execute(''' SELECT id, counter FROM identificadores WHERE internal_qr=%s AND external_qr=%s''',(internal_qr,external_qr))
    results = cursor.fetchall()

    mysql.connection.commit()
    cursor.close()

    if(results[0][0] == 0): 
        return jsonify(
            match=False,
            counter=results[0][1]
        )
    else: 
        return jsonify(
            match=True,
            counter=results[0][1]
        )
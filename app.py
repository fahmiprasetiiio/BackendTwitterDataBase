from flask import Flask, request, abort, jsonify
from flask_cors import CORS

import os, json, jwt
import psycopg2, psycopg2.extras

app = Flask(__name__)
cors = CORS(app)
secret_key = 'marinirinfantri'

#membuat Koneksi ke database di postgreSQL
con = psycopg2.connect(database=os.getenv('DATABASE'),user=os.getenv('USER'),password=os.getenv('PASSWORD'),host=os.getenv('HOSTDB'),port=os.getenv('PORTDB'))

@app.route('/signUp', methods=['POST'])
def signUp():
    #mengambil data dari inputan user yang ada di main.js
    username = request.json['username']
    fullname = request.json['fullname']
    email = request.json['email']
    password = request.json['password']
    bio = request.json['bio']
    photoprofile = request.json['photoprofile']

    cursorSignUp = con.cursor()
    cursorSignUp.execute("Insert into person (username,fullname,email,password,bio, photoprofile) values(%s,%s,%s,%s,%s,%s)",(username, fullname, email, password, bio, photoprofile))
    con.commit()

    return "SignUp sukses", 201

@app.route('/login', methods=['POST'])
def login():

    username = request.json['username']
    password = request.json['password']

    cursorLogin = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursorLogin.execute("Select * from person where username = %s and password = %s",(username,password))
    jml = cursorLogin.rowcount

    # return str(cursorLogin.fetchall())
    
    dataUser = []
    for row in cursorLogin.fetchall():
        encode = jwt.encode({'id':row[0]},secret_key,algorithm='HS256').decode('utf-8')
        # print(encode)
        dataUser.append(dict(row))

    con.commit()
    #merge json
    dataUser[0].update({'token':str(encode)})
    if jml > 0:
        return jsonify(dataUser), 200
    else:
        "Gagal", 400   


@app.route('/addtweet', methods=['POST'])
def add_tweet():

    if request.method == 'POST':
        token = request.json['id']
        decode = jwt.decode(token, secret_key, algorithms=['HS256'])
        id = (decode['id'])
        tweet = request.json['content']

        curInsertTweet = con.cursor()
        curInsertTweet.execute("Insert into tweets (content, date, person_id) values (%s,now(),%s)",(tweet, id))
        
        con.commit()
        return "Tweet sukses", 201
    else:
        return "Method not allowed", 400

@app.route('/readtweet', methods=['GET'])
def read_tweet():
   
    curTweet = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
    curTweet.execute("select person.id as id, person.username as username, person.fullname as fullname, person.email as email, person.password as password, person.bio as bio, person.photoprofile as photoprofile, tweets.id as idtweet, tweets.content as content, tweets.date as date from tweets inner join person on tweets.person_id=person.id") # Untuk menampilkan data tweet dari db

    dataTweet = []
    data_TokenID = []
    for row in curTweet.fetchall():
        encode = jwt.encode({'id':row[0]},secret_key,algorithm='HS256').decode('utf-8')
        
        data_TokenID.append(encode)
        dataTweet.append(dict(row))

    for index, tokenID in enumerate(data_TokenID):
        dataTweet[int(index)].update({"token":str(tokenID)})

    con.commit()
    return jsonify(dataTweet), 200  


# read tweet personal di dalam halaman profile
@app.route('/readPersonaltweet', methods=['POST'])
def read_personal_tweet():

    token = request.json['id']
    decode = jwt.decode(token, secret_key, algorithms=['HS256'])
    id = (decode['id'])

    #mengambil data dari data base
    cursorLogin = con.cursor(cursor_factory = psycopg2.extras.DictCursor) #key di dictionary
    cursorLogin.execute("select * from person inner join tweets on person.id = tweets.person_id and person.id=%s",(id,))

    dataTweetPersonal = []
    for row in cursorLogin.fetchall():
        dataTweetPersonal.append(dict(row))

    con.commit()

    return jsonify(dataTweetPersonal), 201

#Menampilkan user yang akan difollow
@app.route('/getfollowlist', methods=['POST'])
def get_following_list():

    token = request.json['id']
    decode = jwt.decode(token, secret_key, algorithms=['HS256'])
    id = (decode['id'])

    #mengambil data dari database
    cursorgetfollow = con.cursor(cursor_factory = psycopg2.extras.DictCursor)
    cursorgetfollow.execute("select * from person where id not in (select following from follow where id_person=%s) and id != %s",(id,id))

    dataFollowlist = []
    for row in cursorgetfollow.fetchall():
        dataFollowlist.append(dict(row))

    con.commit()

    return jsonify(dataFollowlist), 201


@app.route('/getprofileHome', methods=['POST'])
def get_Userprofile():

    token = request.json['id']
    decode = jwt.decode(token, secret_key, algorithms=['HS256'])
    id = (decode['id'])

    cursorProfilhome = con.cursor(cursor_factory = psycopg2.extras.DictCursor)
    cursorProfilhome.execute("select * from person where id = %s",(id,))

    dataprofilHome = []
    for row in cursorProfilhome.fetchall():
        dataprofilHome.append(dict(row))

    con.commit()

    return jsonify(dataprofilHome), 201

@app.route('/getfollowing', methods=['POST','GET'])
def addfollow():
    if request.method == 'POST':

        token = request.json['id']
        decode = jwt.decode(token, secret_key, algorithms=['HS256'])
        id = (decode['id'])

        idfollowing = request.json['id_following']

        curInsertFollow = con.cursor()
        curInsertFollow.execute("Insert into follow(id_person,following) values (%s,%s)",(id,idfollowing))
        con.commit()

        return "Followed", 201
    else:
        return "Method Not Allowed", 400 

@app.route('/deletetweet', methods=['POST'])
def deletetweet():
    if request.method == 'POST' :

        id = request.json['id']

        # curdeltweet = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
        curdeltweet = con.cursor()
        curdeltweet.execute("DELETE from tweets where id=%s", (id,))
        con.commit()

        return "Tweet has been delete", 201
    else:
        return "",400

@app.route('/editprofil', methods=['POST'])
def editprofil():
    
    token = request.json['id']
    decode = jwt.decode(token, secret_key, algorithms=['HS256'])
    id = (decode['id'])

    username = request.json['username']
    fullname = request.json['fullname']
    email = request.json['email']
    bio = request.json['bio']

    curUbahAkun = con.cursor()
    curUbahAkun.execute("update person set username=%s, fullname=%s, email=%s, bio=%s where id=%s",(username,fullname,email,bio,id))
    con.commit()

    return "Sukses Ubah Akun", 200

    
@app.route('/editpassword', methods=['POST'])
def editpassword():

    token = request.json['id']
    decode = jwt.decode(token, secret_key, algorithms=['HS256'])
    id = (decode['id'])

    password_Cur = request.json['curr_pass']
    password_New = request.json['new_pass']
    password_Verr = request.json['ver_pass']

    check_Pass = con.cursor()
    check_Pass.execute("Select * from person where id=%s and password=%s",(id,password_Cur))
    jml = check_Pass.rowcount

    if (jml > 0):
        curUbahPass = con.cursor()
        curUbahPass.execute("Update person set password=%s where id=%s and password=%s",(password_New,id,password_Cur))
        con.commit()
        return "Password berhasil diubah", 200
    else:
        return "Password Not Found", 400

    return "Password berhasil diubah", 200

if __name__ == '__main__' :
     app.run(debug=True, host=os.getenv('HOST'),port =os.getenv('PORT'))  
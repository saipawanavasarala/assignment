from flask import Flask,jsonify,request,Response
#from flask_cors import CORS
import sqlite3
import pandas as pd
import hashlib
import smtplib
from extras import sendMail
import smtplib
from flask_mail import Mail,  Message
conn=sqlite3.connect("social.db",check_same_thread=False)

def SSO(func):
    def inner(*args, **kwargs):
        
        token=True
        if "Authorization" not in request.headers:
            return Response("UnAuthorized access",401)

        

        token=request.headers["Authorization"].split(" ")[-1]

        if "username" in request.form:
            username=request.form['username']
            dbusername=pd.read_sql(f"select username from user where token='{token}'  ",conn)
            dbusername=dbusername.to_dict('records')[0]['username']
            if dbusername==username:
                pass
            else:
                return Response("UnAuthorized access",401)

        verifyToken=pd.read_sql(f"select verified from user where token='{token}' ",conn)
        verifiedUser=verifyToken.values[0][0]

        

        if len(verifyToken)>0:
            if int(verifiedUser)==0:
                return Response("please verify your account")
            return func(*args, **kwargs)

        else:
            return Response("UnAuthorized access",401)
        
    return inner

def sendMsg(receiver,message,title):
    msg = mail.send_message(
        title,
        sender='pavan@sujainfo.com',
        recipients=[receiver],
        body=message
    )
    return ""

secretKey=r"this is secret"
app=Flask(__name__)

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'pavan@sujainfo.com'
app.config['MAIL_PASSWORD'] = 'saiPavan@123'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True


mail = Mail(app)

baseUrl="http://127.0.0.1:5000"
@app.route("/")
def home():
    sendMsg('avasaralasaipavan@gmail.com',"hi")
    return "server is working"


@app.route("/login",methods=["POST"])
def login():
    if request.method=="POST":
        clinetData=request.form
        userName=clinetData['username']
        password=clinetData['password']
        details=pd.read_sql(f'''select username,password,token,verified from "user" where "username"='{userName}' ''',conn)

        if len(details)<1 :
            return "invalid credentials"

        userData=details.to_dict('records')[0]

        if userData['verified']==0:
            return "please verify using the following link : "+f"{baseUrl}/verify/{userName}"

        if userData["password"]==password and userData['verified']:
            print(userData["token"])

            return jsonify({"access-token":userData["token"],"verified":userData['verified']})
        else:
            return "invalid credentials"



@app.route("/signup",methods=["POST"])
def signup():
    clientData=request.form
    fullname=clientData["fullname"]
    username=clientData["username"]
    password=clientData['password']
    email=clientData["email"]

    dbusername=pd.read_sql(f'''select "username" from "user" where "username"='{username}'  ''',conn)
    if len(dbusername)>0:
        return "user already exists"

    dbemail=pd.read_sql(f''' select "email" from "user" where "email"='{email}'  ''',conn)
    if len(dbemail)>0:
        return "email already exists"

    

    token = hashlib.sha256(username.encode('utf-8')).hexdigest()

    dictt={
        "username":username,
        "password":password,
        "email":email,
        "fullname":fullname,
        "token":token

    }
    
    df=pd.DataFrame([dictt.values()],columns=dictt.keys())

    df.to_sql("user",conn,if_exists='append',index=False)
    
    gmail=mail.send_message(
        'activation link',
        sender='pavan@sujainfo.com',
        recipients=[email],
        body=f" The activation link is : {baseUrl}/veirfy/{username}")

    return "a verification has been send to your mail please check it" 



@app.route("/verify/<string:username>",methods=["GET"])
def verify(username):
    try:
        username=str(username)
        cursor=conn.cursor()
        cursor.execute(f"update user set verified=1 where username='{username}'")
        conn.commit()
        return "successfully verified"
    except Exception as e:
        import traceback
        
        return  str(traceback.format_exc())



@app.route("/postContent",methods=['GET','POST','PUT','DELETE'])
@SSO
def postContent():

    if request.method=="GET":
        
        data=pd.read_sql(f"select * from post",conn)
        data=data.to_dict('records')

        return jsonify(data)

    if request.method=="POST":
        clientData=request.form
        username=clientData['username']
        content=clientData['content']

        dictt={
            "username":username,
            "content":content,
        }

        df=pd.DataFrame([dictt.values()],columns=dictt.keys())

        df.to_sql("post",conn,if_exists='append',index=False)

        return "posted successfully"

    if request.method=="PUT":
        clientData=request.form
        postId=clientData['postid']
        username=clientData['username']

        cursor=conn.cursor()
        cursor.execute(f"update post set likes=likes+1 where postid={postId}")
        conn.commit()
        data=pd.read_sql(f"select email from user where username='{username}' ",conn)
        data=data.to_dict('records')[0]
        print(data['email'])
        sendMsg(data['email'],"you have liked the post","liking post")

        return username


    if request.method=="DELETE":
        clientData=request.form
        postId=clientData['postid']
        username=clientData['username']

        cursor=conn.cursor()
        cursor.execute(f"update post set dislikes=dislikes+1 where postid={postId}")
        conn.commit()
        data=pd.read_sql(f"select email from user where username='{username}' ",conn)
        data=data.to_dict('records')[0]
        print(data['email'])
        sendMsg(data['email'],f"you have dislike the post  ","disliking post")

        return "DISLIKED!!"


@app.route("/userPost",methods=['POST',"GET"])

def userPost():
    if request.method=="POST":
        username=request.form['username']
        data=pd.read_sql(f"select * from post where username='{username}' ",conn)

        if len(data)<1:
            return "no records found"

        data=data.to_dict("records")
        print(data)

        return jsonify(data)
    

if __name__=="__main__":
    app.run(debug=True)
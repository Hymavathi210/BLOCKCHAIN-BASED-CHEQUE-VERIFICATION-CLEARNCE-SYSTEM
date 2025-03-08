from django.shortcuts import render
from django.template import RequestContext
from django.contrib import messages
import json
from web3 import Web3, HTTPProvider
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
import os
import random
from datetime import date
import pyqrcode
import png
from pyqrcode import QRCode
import hashlib
import cv2
import smtplib

global uname, email, contract, web3
#function to call contract
def getContract():
    global contract, web3
    blockchain_address = 'http://127.0.0.1:9545'
    web3 = Web3(HTTPProvider(blockchain_address))
    web3.eth.defaultAccount = web3.eth.accounts[0]
    compiled_contract_path = 'Cheque.json' #cheque contract file
    deployed_contract_address = '0xCD198934CD9E82D95b44A0eDE09bf7B38Ef65B4b' #contract address
    with open(compiled_contract_path) as file:
        contract_json = json.load(file)  # load contract info as JSON
        contract_abi = contract_json['abi']  # fetch contract's abi - necessary to call its functions
    file.close()
    contract = web3.eth.contract(address=deployed_contract_address, abi=contract_abi)
getContract()


def index(request):
    if request.method == 'GET':
       return render(request, 'index.html', {})

def BankLogin(request):
    if request.method == 'GET':
       return render(request, 'BankLogin.html', {})

def Register(request):
    if request.method == 'GET':
       return render(request, 'Register.html', {})

def UserLogin(request):
    if request.method == 'GET':
       return render(request, 'UserLogin.html', {})

def RegisterAction(request):
    if request.method == 'POST':
        global contract
        username = request.POST.get('t1', False)
        password = request.POST.get('t2', False)
        contact = request.POST.get('t3', False)
        email = request.POST.get('t4', False)
        address = request.POST.get('t5', False)
        utype = request.POST.get('t6', False)
        count = contract.functions.getUserCount().call()
        status = "none"
        for i in range(0, count):
            user1 = contract.functions.getUsername(i).call()
            if username == user1:
                status = "exists"
                break
        if status == "none":
            msg = contract.functions.createUser(username, email, password, contact, address, utype).transact()
            tx_receipt = web3.eth.waitForTransactionReceipt(msg)
            context= {'data':'Signup Process Completed<br/>'+str(tx_receipt)}
            return render(request, 'Register.html', context)
        else:
            context= {'data':'Given username already exists'}
            return render(request, 'Register.html', context)

def BankLoginAction(request):
    if request.method == 'POST':
        global uname, email, contract
        username = request.POST.get('t1', False)
        password = request.POST.get('t2', False)
        status = 'none'
        count = contract.functions.getUserCount().call()
        status = "none"
        for i in range(0, count):
            user1 = contract.functions.getUsername(i).call()
            pass1 = contract.functions.getPassword(i).call()
            utype = contract.functions.getUsertype(i).call()
            email_id = contract.functions.getEmail(i).call()
            if user1 == username and pass1 == password and utype == "Bank":
                uname = username
                email = email_id
                status = "success"
                break
        if status == 'success':
            output = 'Welcome '+username
            context= {'data':output}
            return render(request, "BankScreen.html", context)
        if status == 'none':
            context= {'data':'Invalid login details'}
            return render(request, 'BankLogin.html', context)

def UserLoginAction(request):
    if request.method == 'POST':
        global uname, email, contract
        username = request.POST.get('t1', False)
        password = request.POST.get('t2', False)
        status = 'none'
        count = contract.functions.getUserCount().call()
        status = "none"
        for i in range(0, count):
            user1 = contract.functions.getUsername(i).call()
            pass1 = contract.functions.getPassword(i).call()
            utype = contract.functions.getUsertype(i).call()
            email_id = contract.functions.getEmail(i).call()
            if user1 == username and pass1 == password and utype == "User":
                uname = username
                email = email_id
                status = "success"
                break
        if status == 'success':
            output = 'Welcome '+username
            context= {'data':output}
            return render(request, "UserScreen.html", context)
        if status == 'none':
            context= {'data':'Invalid login details'}
            return render(request, 'UserLogin.html', context)

def GenerateCheque(request):
    if request.method == 'GET':
        global uname
        count = contract.functions.getUserCount().call()
        banklist = []
        userlist = []
        for i in range(0, count):
            user1 = contract.functions.getUsername(i).call()
            utype = contract.functions.getUsertype(i).call()
            if utype == 'Bank':
                banklist.append(user1)
            else:
                userlist.append(user1)
        output = '<tr><td><font size="3" color="black"><b>Bank&nbsp;Name</b></td>'
        output += '<td><select name="t1">'
        for i in range(len(banklist)):
            output += '<option value="'+banklist[i]+'">'+banklist[i]+'</option>'
        output += '</select></td></tr>'

        output += '<tr><td><font size="3" color="black"><b>Receiver&nbsp;Name</b></td>'
        output += '<td><select name="t2">'
        for i in range(len(userlist)):
            if userlist[i] != uname:
                output += '<option value="'+userlist[i]+'">'+userlist[i]+'</option>'
        output += '</select></td></tr>'
        context= {'data1':output}
        return render(request, "GenerateCheque.html", context)

def GenerateChequeAction(request):
    if request.method == 'POST':
        global contract, uname
        bank = request.POST.get('t1', False)
        receiver = request.POST.get('t2', False)
        amount = request.POST.get('t3', False)
        today = str(date.today())
        url = pyqrcode.create(uname+"#"+bank+"#"+receiver+"#"+amount+"#"+today)
        if os.path.exists('ChequeApp/static/files/test.png'):
            os.remove('ChequeApp/static/files/test.png')
        url.png('ChequeApp/static/files/test.png', scale = 6)
        with open('ChequeApp/static/files/test.png', 'rb') as file:
            data = file.read()
        file.close()
        sha256hash = hashlib.sha256(data).hexdigest()
        if os.path.exists('ChequeApp/static/files/test.png'):
            os.remove('ChequeApp/static/files/test.png')
        with open('ChequeApp/static/files/'+sha256hash+".png", 'wb') as file:
            file.write(data)
        file.close()
        msg = contract.functions.createCheque(sha256hash, "Pending").transact()
        tx_receipt = web3.eth.waitForTransactionReceipt(msg)
        context= {'data':'Cheque Generation Completed<br/>'+str(tx_receipt)}
        return render(request, 'UserScreen.html', context)
                

def getCode(hashcode):
    global uname
    image = cv2.imread('ChequeApp/static/files/'+hashcode+".png")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    qr_codes = cv2.QRCodeDetector().detectAndDecode(gray)
    return qr_codes[0]

def ViewStatus(request):
    if request.method == 'GET':
        global uname
        output = '<table border=1 align=center>'
        output+='<tr><th><font size=3 color=black>Sender Name</font></th>'
        output+='<th><font size=3 color=black>Bank Name</font></th>'
        output+='<th><font size=3 color=black>Receiver Name</font></th>'
        output+='<th><font size=3 color=black>Amount</font></th>'
        output+='<th><font size=3 color=black>Cheque Date</font></th>'
        output+='<th><font size=3 color=black>Hashcode</font></th>'
        output+='<th><font size=3 color=black>Status</font></th>'
        output+='<th><font size=3 color=black>QR Code</font></th></tr>'
        count = contract.functions.getChequeCount().call()
        for i in range(0, count):
            hashcode = contract.functions.getCode(i).call()
            status = contract.functions.getStatus(i).call()
            data = getCode(hashcode)
            print(type(data))
            arr = str(data).strip().split("#")
            if arr[0] == uname or arr[0] == uname:
                output+='<tr><td><font size=3 color=black>'+arr[0]+'</font></td>'
                output+='<td><font size=3 color=black>'+arr[1]+'</font></td>'
                output+='<td><font size=3 color=black>'+str(arr[2])+'</font></td>'
                output+='<td><font size=3 color=black>'+str(arr[3])+'</font></td>'
                output+='<td><font size=3 color=black>'+str(arr[4])+'</font></td>'
                output+='<td><font size=3 color=black>'+hashcode[0:30]+'</font></td>'
                output+='<td><font size=3 color=black>'+status+'</font></td>'
                output+='<td><img src="/static/files/'+hashcode+'.png" width="200" height="200"></img></td></tr>'                    
        output+="</table><br/><br/><br/><br/><br/><br/>"
        context= {'data':output}
        return render(request, 'UserScreen.html', context)              
        
def sendMail(sender_email, receiver_email, amount, sender, receiver):
    em = []
    em.append(sender_email)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as connection:
        email_address = 'kaleem202120@gmail.com'
        email_password = 'xyljzncebdxcubjq'
        connection.login(email_address, email_password)
        connection.sendmail(from_addr="kaleem202120@gmail.com", to_addrs=em, msg='Subject: {}\n\n{}'.format("Cheque Cleared Alert", "Your Cheque successfully cleared to receiver "+receiver+" of amount "+str(amount)))
    em1 = []
    em1.append(sender_email)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as connection:
        email_address = 'kaleem202120@gmail.com'
        email_password = 'xyljzncebdxcubjq'
        connection.login(email_address, email_password)
        connection.sendmail(from_addr="kaleem202120@gmail.com", to_addrs=em1, msg='Subject: {}\n\n{}'.format("Cheque Cleared Alert", "Your Cheque successfully received from sender "+sender+" of amount "+str(amount)))


def ClearCheque(request):
    if request.method == 'GET':
        global uname
        cheque = request.GET['chequeno']
        sender = request.GET['sender']
        receiver = request.GET['receiver']
        amount = request.GET['amount']
        sender_email = "none"
        receiver_email = "none"
        contract.functions.updateStatus(int(cheque)).transact()
        count = contract.functions.getUserCount().call()
        for i in range(0, count):
            user1 = contract.functions.getUsername(i).call()
            email_id = contract.functions.getEmail(i).call()
            if user1 == sender:
                sender_email = email_id
            if user1 == receiver:    
                receiver_email = email_id
        sendMail(sender_email, receiver_email, amount, sender, receiver)         
        context= {'data':'Cheque status successfully cleared'}
        return render(request, 'BankScreen.html', context)

def ViewPending(request):
    if request.method == 'GET':
        global uname
        output = '<table border=1 align=center>'
        output+='<tr><th><font size=3 color=black>Sender Name</font></th>'
        output+='<th><font size=3 color=black>Bank Name</font></th>'
        output+='<th><font size=3 color=black>Receiver Name</font></th>'
        output+='<th><font size=3 color=black>Amount</font></th>'
        output+='<th><font size=3 color=black>Cheque Date</font></th>'
        output+='<th><font size=3 color=black>Hashcode</font></th>'
        output+='<th><font size=3 color=black>Status</font></th>'
        output+='<th><font size=3 color=black>QR Code</font></th>'
        output+='<th><font size=3 color=black>Clear Cheque</font></th></tr>'
        count = contract.functions.getChequeCount().call()
        for i in range(0, count):
            hashcode = contract.functions.getCode(i).call()
            status = contract.functions.getStatus(i).call()
            if status == "Pending":
                data = getCode(hashcode)
                arr = str(data).strip().split("#")
                if len(arr) > 1 and arr[1] == uname:
                    output+='<tr><td><font size=3 color=black>'+arr[0]+'</font></td>'
                    output+='<td><font size=3 color=black>'+arr[1]+'</font></td>'
                    output+='<td><font size=3 color=black>'+str(arr[2])+'</font></td>'
                    output+='<td><font size=3 color=black>'+str(arr[3])+'</font></td>'
                    output+='<td><font size=3 color=black>'+str(arr[4])+'</font></td>'
                    output+='<td><font size=3 color=black>'+hashcode[0:30]+'</font></td>'
                    output+='<td><font size=3 color=black>'+status+'</font></td>'
                    output+='<td><img src="/static/files/'+hashcode+'.png" width="200" height="200"></img></td>'
                    output+='<td><a href=\'ClearCheque?chequeno='+str(i)+'&sender='+arr[0]+'&receiver='+arr[2]+'&amount='+arr[3]+'\'><font size=3 color=black>Click Here</font></a></td></tr>'
        output+="</table><br/><br/><br/><br/><br/><br/>"
        context= {'data':output}
        return render(request, 'BankScreen.html', context) 

def DailyTransaction(request):
    if request.method == 'GET':
        global uname
        output = '<table border=1 align=center>'
        output+='<tr><th><font size=3 color=black>Bank Name</font></th>'
        output+='<th><font size=3 color=black>Date</font></th>'
        output+='<th><font size=3 color=black>Daily Transaction</font></th></tr>'
        count = contract.functions.getChequeCount().call()
        transaction = {}
        for i in range(0, count):
            hashcode = contract.functions.getCode(i).call()
            status = contract.functions.getStatus(i).call()
            data = getCode(hashcode)
            arr = str(data).strip().split("#")
            if len(arr) > 1 and arr[1] == uname:
                if arr[4] not in transaction:
                    transaction[arr[4]] = float(arr[3])
                else:
                    transaction[arr[4]] += float(arr[3])
        for key, value in transaction.items():
            output+='<tr><td><font size=3 color=black>'+uname+'</font></td>'
            output+='<td><font size=3 color=black>'+str(key)+'</font></td>'
            output+='<td><font size=3 color=black>'+str(value)+'</font></td>'
        output+="</table><br/><br/><br/><br/><br/><br/>"
        context= {'data':output}
        return render(request, 'BankScreen.html', context)    

        
        
        

from flask import Flask, render_template, request, redirect, jsonify
import json
from datetime import datetime
import requests
import os
from postgres_com import *
from flask_cors import CORS
#variables
app_name=os.environ['EOH_NAME']
app_ip=os.environ['EOH_IP']

#######################
##FLASK CONFIGURATION##
#######################
app = Flask(__name__, template_folder='templates')
CORS(app)
###############################
##########POSTGRES_DB##########
###############################

connect_db= get_db_connection()
cur = connect_db.cursor()

#TABLE USER
sqlCreateTableIP = "create table if not exists CLIENT (\
id serial primary key,\
username varchar(200),\
access varchar(256) default 'DENIED',\
date_created timestamp default now(),\
email varchar(256),\
password varchar(256));"
cur.execute(sqlCreateTableIP)

#TABLE FILTER
sqlCreateTableIP = "create table if not exists FILTER (\
id serial primary key,\
date_created timestamp default now(),\
filters text);"
cur.execute(sqlCreateTableIP)

#TABLE LOG
sqlCreateTableHISTORY = "create table if not exists LOG (\
id serial primary key,\
username varchar(256),\
date_created timestamp default now(),\
action varchar(256),\
details varchar(256));"
cur.execute(sqlCreateTableHISTORY)
connect_db.commit()
cur.close()
connect_db.close()

############################################
##############REACT#########################
############################################

############################################
##############ROUTES########################
############################################

#DEFAULT ROUTE
@app.route('/')
def default():
    return redirect('/home')

#HOME
@app.route('/home', methods=['GET'])
def home():
    return render_template('home.html')

#CLIENTS
#HOME
@app.route('/clients', methods=['GET'])
def clients():
    clients=get_all_clients()
    return render_template('clients.html', clients=clients)

#LOGS
@app.route('/logs', methods=['GET'])
def logs():
    logs=get_all_logs()
    return render_template('logs.html',logs=logs)

#ADD CLIENT
@app.route('/addclient', methods=['POST','GET'])
def addclient():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        clients=get_all_clients()
        #CHECK IF IP EXISTS
        for client in clients:
            if client[1] == username:
                return redirect('/')
        try:
            add_client(username,email,password)
            action = "INSERT"
            details = "At {} CLIENT : {} added in system".format(datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),username)
            add_log(username,action,details)
            return redirect('/')
        except:
            return render_template('error.html', error='There was a problem with Database!')
    else:
        return render_template('add_client.html')

#POST FILTER
@app.route('/addfilter', methods=['POST','GET'])
def addfilter():
    if request.method == 'POST':
        try:
            request_data = request.data.decode('utf-8')  # Decode the raw request data
            #print('Received JSON data:', request_data)
            
            # Parse the JSON data into a Python dictionary
            data = json.loads(request_data)
            # Serialize the data into a JSON string
            data_str = json.dumps(data)
            selectedRegion = data.get('selectedRegion')
            rangeAirport = data.get('selectedRangeAirport')
            rangeCoastMax = data.get('selectedRangeCoastMax')
            rangeCoastMin = data.get('selectedRangeCoastMin')
            rangeHospital = data.get('selectedRangeHospital')
            rangePort = data.get('selectedRangePort')
            rangeRiver = data.get('selectedRangeRiver')
            rangeElevationMax = data.get('selectedRangeElevationMax')
            rangeElevationMin = data.get('selectedRangeElevationMin')
            add_filters(data_str)
            action = "INSERT"
            details = "At {}  filters added in system".format(datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
            add_log("alekos",action,details)
            # Return a JSON response with a success message
            response_data = searchTowns(selectedRegion,rangeAirport,rangeCoastMax, rangeCoastMin,rangeHospital,rangePort, rangeRiver, rangeElevationMin, rangeElevationMax)
            return jsonify(response_data)
        except Exception as e:
            # Return a JSON response with an error message
            response_data = {'error': 'Internal Server Error', 'details': str(e)}
            return jsonify(response_data), 500
    else:
        return 'Method not allowed', 405

        
#DELETE CLIENT
@app.route('/delete/<int:id>')
def delete(id):
    client=search_by_id(id)
    try:
        delete_client(id)
        action = "REMOVE"
        details = "At {} CLIENT : {} removed from system".format(datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),client[1])
        add_log(client[1],action,details)
        return redirect('/')
    except:
        return render_template('error.html', error='There was a problem with Database!')

#SERACH BY ACCESS
@app.route('/SearchByAccess/<string:access>')
def SearchByAccess(access):
    if access == "ALL":
        clients = get_all_clients()
        return render_template('clients.html', clients=clients)
    else:
        clients = search_by_access(access)
        return render_template('clients.html', clients=clients)
    
#UPDATE CLIENT
@app.route('/update/<int:id>', methods=['GET','POST'])
def update(id):
    client = search_by_id(id)
    client_id=client[0]
    client_username=client[1]
    client_access=client[2]
    client_date=client[3]
    client_email=client[4]
    client_password=client[5]
    if request.method == 'POST':
        try:
            client_username=request.form['username']
            client_access=request.form['access']
            update_client(client_id,client_username,client_access,client_date,client_email,client_password)
            action = "UPDATE"
            details = "At {} CLIENT : {} updated in system".format(datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),client_username)
            add_log(client_username,action,details)
            return redirect('/')
        except:
            return render_template('error.html', error='There was a problem with DB!')
    else:
        return render_template('update.html', ip=client)

#MAIN
if __name__ == '__main__':
    print("EarthObservationHub running!!")
    app.run(debug=True, host='0.0.0.0')
from flask import Flask, request, jsonify, send_file
# from flask_restful import Resource, Api, reqparse
import datetime
from flask_cors import CORS
import sqlite3
import json
app = Flask(__name__)
CORS(app)

@app.route('/generate', methods=["POST"])
def generate_file():
    headers  = {"Content-Type": "application/json"}
    if request.method == "POST" :
        data = request.json
        templateID = request.json["id_template"]
        
        textArray = []
        con = sqlite3.connect('example.db')

        cur = con.cursor()
        cur.execute("SELECT * FROM username WHERE id_template = " + str(templateID))
        my_query = cur.fetchall()
        for row in my_query:
            username = row[2]
            password = row[3]
            usernameCommand = "username " + username + " password " + password 
            textArray.append(usernameCommand)
            #print(usernameCommand)
        cur.close()

        cur = con.cursor()
        cur.execute("SELECT * FROM vty WHERE id_template = " + str(templateID))
        my_query = cur.fetchall()
        for row in my_query:  
            vtyCommand = "line vty " + row[2] + " " + row[3] + ",\n" + "access-class " + row[4] + " " + row[5].lower() + ",\n" + "password " + row[6]
            textArray.append(vtyCommand)
            #print(vtyCommand)
            
            query  = con.cursor()
            query.execute("SELECT * FROM transport WHERE id_vty = "+ str(row[0]))
            record = query.fetchall()
            for rec in record:
                transportCommand = "transport " + rec[2] + " " + rec[3]
                textArray.append(transportCommand)
                #print(transportCommand)
            query.close()    
        cur.close()

        cur = con.cursor()
        cur.execute("SELECT * FROM acl WHERE id_template = "+ str(templateID))
        my_query = cur.fetchall()
        for row in my_query:
            accesslistCommand = "access-list " + str(row[2]) + " " + row[3].lower() + " " + row[4].lower() + " " + str(row[5]) + " " + str(row[6])
            if str(row[7]) == "Yes" :
                accesslistCommand += " eq " + row[8]
            textArray.append(accesslistCommand)
            #print(accesslistCommand)
        cur.close()

        cur = con.cursor()
        cur.execute("SELECT * FROM Tacacs WHERE id_template = "+ str(templateID))
        my_query = cur.fetchall()
        for row in my_query:
            tacacsCommand = "tacacs-server " + row[2].lower() + " " + str(row[3])
            textArray.append(tacacsCommand)
            #print(tacacsCommand)
        cur.close()

        f = open("template.txt", "w")
        for i in textArray:
            f.write(str(i)+",\n")
        f.close()    
        
        return "10.100.100.154:5000/download" , 200
        #return send_file("template.txt", as_attachment=True)
        
@app.route('/download', methods=["GET"])
def download_file():
    path = "template.txt"
    return send_file(path, as_attachment=True)

@app.route('/software', methods=["GET"])
def software():
	con = sqlite3.connect('example.db')
	cur = con.cursor()
	cur.execute("SELECT * FROM software")
	my_query = cur.fetchall()
	json_output = json.dumps(my_query)
	con.commit()
	return json_output

@app.route('/device', methods=["GET"])
def device():
	con = sqlite3.connect('example.db')
	cur = con.cursor()
	cur.execute("SELECT * FROM network_device")
	my_query = cur.fetchall()
	json_output = json.dumps(my_query)
	con.commit()
	return json_output

@app.route('/insert', methods=["POST"])
def insert():
	headers  = {"Content-Type": "application/json"}
	if request.method == "POST" : 
		con = sqlite3.connect('example.db')
		c = con.cursor()
		c.execute("SELECT MAX(id_template) FROM template")
		my_query = c.fetchall()
		json_output = json.dumps(my_query)
		id_template = my_query[0][0]
		if my_query[0][0] == None :
			id_template = 1
		else :
			id_template +=  1

		c.execute("SELECT MAX(id_vty) FROM vty")
		my_query = c.fetchall()
		json_output = json.dumps(my_query)
		id_vty = my_query[0][0]
		if my_query[0][0] == None :
			id_vty = 1
		else :
			id_vty +=  1
		textfile = ''
		data = request.json
		c.execute("INSERT INTO template  VALUES (?, ?, ?, ?, ?)", (id_template, data["template"]["id_software"], data["template"]["id_device"], datetime.datetime.now(), data["template"]["name_template"]))
		con.commit()
		# file = open("conf_cisco.txt", "w")
		for data1 in data:
			try:
				if 'acl' in data1:
					acl_data = request.json["acl"]
					for key in acl_data :
						# file.write("access-list" + ' ' + key["acl_number"] + ' ' + key["option"] + ' ' + key["wildcard1"] + ' ' + key["wildcard2"] + ' ' + key["eq_option"] + ' ' + key["eq_port"] + '\n' )
						c.execute("INSERT INTO acl (id_template, acl_number, type, option, wildcard1, wildcard2, eq_option, eq_port) VALUES (?, ?, ?, ?, ?, ?, ?, ? )", (id_template, key["acl_number"], key["type"], key["option"], key["wildcard1"], key["wildcard2"], key["eq_option"], key["eq_port"] ))
						con.commit()
				if 'username' in data1:
					# user_data = request.json["username"]
					# for key in user_data :
						# file.write("username" + ' ' + key["username"] + ' ' + "password" + ' ' + key["password"]  + '\n' )
					c.execute("INSERT INTO username (id_template, username, password) VALUES (?, ?, ?)", (id_template, data["username"]["username"], data["username"]["password"]))
					con.commit()
				if 'Tacacs' in data1:
					Tacacs = request.json["Tacacs"]
					for key in Tacacs :
						c.execute("INSERT INTO Tacacs (id_template, option, detail) VALUES (?, ?, ?)", (id_template, key["option"], key["detail"]))
						con.commit()
				if 'vty' in data1:
					c.execute("INSERT INTO vty (id_vty, id_template, line1, line2, acc1, acc2, password ) VALUES (?, ?, ?, ?, ?, ?, ?)", (id_vty, id_template, data["vty"]["line1"], data["vty"]["line2"], data["vty"]["acc1"], data["vty"]["acc2"], data["vty"]["password"]))
					con.commit() 
			except KeyError:
				print("Some custom message here")

		for data in request.json["vty"]:
			try:
				if 'Transport' in data:
					Transport = request.json["vty"]["Transport"]
					for key in Transport :
						c.execute("INSERT INTO transport (id_vty, type, option) VALUES (?, ?, ?)", (id_vty, key["tpye"], key["option"]))
						con.commit()
			except KeyError:
				print("Some custom message here")
		con.close()
	return jsonify(
		status = "ok"
		# textfile
	),201

@app.route('/update', methods=["POST"])
def update():
	if request.method == "POST" : 
		con = sqlite3.connect('example.db')
		c = con.cursor()
		data = request.json
		update_data = (data["template"]["id_device"], data["template"]["id_software"], datetime.datetime.now(), data["template"]["name"],  data["template"]["id_template"])
		c.execute("UPDATE template SET id_device = ?, id_software = ?,date = ?, name = ? WHERE id_template = ?", update_data)
		con.commit()
		for data1 in data:
			try:
				if 'acl' in data1:
					acl_data = request.json["acl"]
					for key in acl_data :
						update_data = (key["acl_number"], key["type"], key["option"], key["wildcard1"], key["wildcard2"], key["eq_option"], key["eq_port"], key["id_acl"])
						c.execute("UPDATE acl SET acl_number = ?, type = ?, option= ?, wildcard1 = ?, wildcard2 = ?, eq_option = ?, eq_port = ? where id_acl = ?", update_data )
						con.commit()
				if 'username' in data1:
					# user_data = request.json["username"]
					# for key in user_data :
					update_data = (data["username"]["username"], data["username"]["password"], data["username"]["id_username"])
					c.execute("UPDATE username SET username = ?, password = ? where id_username = ?", update_data)
					con.commit()
				if 'Tacacs' in data1:
					Tacacs = request.json["Tacacs"]
					for key in Tacacs :
						update_data = (key["option"], key["detail"], key["id_tacacs"]) 
						c.execute("UPDATE Tacacs SET option = ?, detail = ? where id_tacacs = ? ",update_data ) 
						con.commit()
				if 'vty' in data1:
					update_data = (data["vty"]["line1"], data["vty"]["line2"], data["vty"]["acc1"], data["vty"]["acc2"], data["vty"]["password"], data["vty"]["id_vty"] )
					c.execute("UPDATE vty SET line1 = ?, line2 = ?, acc1 = ?, acc2 = ?, password = ? where id_vty = ? ", update_data)
					con.commit() 
			except KeyError:
				print("Some custom message here")

		for data in request.json["vty"]:
			try:
				if 'Transport' in data:
					Transport = request.json["vty"]["Transport"]
					# print(Transport)
					for key in Transport :
						update_data = (key["type"], key["option"], key["id_transport"])
						c.execute("UPDATE transport SET  type = ? , option = ? where id_transport = ? ", update_data)
						con.commit()
			except KeyError:
				print("Some custom message here111")
		con.close()
	return jsonify(
		status = "ok"
	),201

@app.route('/get_template', methods=["GET"])
def get_template():
	con = sqlite3.connect('example.db')
	c = con.cursor()
	data_template =  {
		"message" : []
	}
	c.execute("SELECT * FROM template t INNER join network_device d on t.id_device = d.id_device LEFT join  software s on s.id_software = t.id_device")
	my_query = c.fetchall()
	for key in my_query :
		data = {
			"id_template": key[0],
			"date": key[3],
			"name_template": key[4],
			"name_device": key[6],
			"version": key[8]
		}
		data_template["message"].append(data)
	# data_template.update(data_acl)
	return jsonify(
		data_template
	),201

@app.route('/detail', methods=["POST"])
def detail():
	if request.method == "POST" :
		id = (request.json["id_template"], )
		data_acl = {
			"acl" : []
		}
		# data_username = {
		# 	"username" : []
		# }
		data_vty = {
			"vty" : {
				"Transport" : []
			}
		}
		data_Tacacs = {
			"tacacs" : []
		}
		con = sqlite3.connect('example.db')
		c = con.cursor()
		c.execute("SELECT * FROM template t INNER join network_device d on t.id_device = d.id_device LEFT join  software s on s.id_software = t.id_device  where t.id_template = ? ", id)
		my_query = c.fetchall()
		data = {
			"template" : {
				"id_template": my_query[0][0],
				"id_device": my_query[0][2],
				"id_software": my_query[0][2],
				"date": my_query[0][3],
				"name_template": my_query[0][4],
				"name_device": my_query[0][6],
				"version": my_query[0][8]
			}
		}
		
		c.execute("SELECT * FROM acl where id_template = ? ", id)
		my_query = c.fetchall()
		for key in my_query :
			acl = { 
					"id_acl" : key[0],
					"id_template" : key[1],
					"acl_number" : key[2],
					"type":  key[3],
					"option": key[4],
					"wildcard1": key[5],
					"wildcard2": key[6],
					"eq_option": key[7],
					"eq_port": key[8]
				}
			data_acl["acl"].append(acl)
		data.update(data_acl)	
		c.execute("SELECT * FROM username where id_template = ? ", id)
		my_query = c.fetchall()
		# for key in my_query : 
		username = {
			"username" : {
				"id_username" : key[0],
				"id_template" : key[1],
				"username" : key[2],
				"password" : key[3],
			}
		}
			
			# data_username["username"].append(username)
		data.update(username)
		c.execute("SELECT * FROM vty where id_template = ? ", id)
		my_query = c.fetchall()
		for key in my_query : 
			vty = {
					"id_vty" : key[0],
					"line1" : key[2],
					"line2" : key[3],
					"acc1" : key[4],
					"acc2" : key[5],
					"password" : key[6],
			}
			id_vty = (key[0], )
			data_vty["vty"].update(vty)
		c.execute("SELECT * FROM transport where id_vty = ? ", id_vty)
		my_query = c.fetchall()
		for key in my_query : 
			vty = {
					"id_transport" : key[0],
					"type" : key[2],
					"option" : key[3]
				}
			
			data_vty["vty"]["Transport"].append(vty)
		data.update(data_vty)
		c.execute("SELECT * FROM Tacacs where id_template = ? ", id)
		my_query = c.fetchall()
		for key in my_query : 
			Tacacs = {
					"id_tacacs" : key[0],
					"option" : key[2],
					"detail" : key[3]
				}
			
			data_Tacacs["tacacs"].append(Tacacs)
		data.update(data_Tacacs)
	return jsonify(
		# my_query
		# request.json["id_template"]
		data
	),201
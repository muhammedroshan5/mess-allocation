import sqlite3
import openpyxl

connection=sqlite3.connect('database.db')

with open('student_content.sql') as f:
	connection.executescript(f.read())
	
cur=connection.cursor()

# read data from the XLSX file
wb = openpyxl.load_workbook('students.xlsx')
ws = wb.active

for row in ws.iter_rows(min_row=2, values_only=True):
    # insert the data into the table
    name=row[1]
    fname=name.split()
    email=fname[0].lower()+'_'+row[0].lower()+'@nitc.ac.in'
    cur.execute('INSERT INTO student (username,name,pwd,due,email) VALUES (?, ?, ?, ?, ?)', (row[0], row[1], row[0], row[2], email))

cur.execute("insert into mess (name,capacity,owner,category) values ('PGII',3,'Shaju V','B')")
cur.execute("insert into mess (name,capacity,owner,category) values ('A',2,'Biju B','B')")
cur.execute("insert into mess (name,capacity,owner,category) values ('OldMega',4,'Vijayan T K','M')")
cur.execute("insert into mess (name,capacity,owner,category) values ('G',3,'Gopinath','G')")
cur.execute("insert into mess (name,capacity,owner,category) values ('MLH',3,'Mohanan P','G')")


cur.execute("insert into admin (username,name,pwd) values ('A01','Manu R','A01')")
connection.commit()
connection.close()

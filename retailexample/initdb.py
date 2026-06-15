import sqlite3
import csv
import os
import json


def printhead(csvlist, n):
    for row in csvlist[:n]:
        print(row)

def printall(csvlist):
    for row in csvlist:
        print(row)

def getcsvlist(csvpath):
    csvlist = list()
    with open(csvpath) as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            csvlist.append(row)
    return csvlist

def getuniquevalues(csvlist, columnindex):
    uniqueset = set()
    for row in csvlist[1:]:
        uniqueset.add(row[columnindex])
    return list(uniqueset)

def getuniquetags(csvlist, columnindex):
    uniqueset = set()
    for row in csvlist[1:]:
        for tag in row[columnindex].split(','):
            uniqueset.add(tag.strip())
    return list(uniqueset)

def createdb(dbname):
    con = sqlite3.connect(dbname)
    cur = con.cursor()
    return con,cur

def createtables(con,cur):
    cur.execute('''
    create table products (
    id text primary key,
    title text not null,
    vendor text not null,
    original_price integer not null,
    sale_price integer not null,
    is_sale integer not null,
    is_clearance integer not null,
    bestseller_score integer not null
    );''')
    cur.execute('''
    create table tags (
    products_id text not null references products(id),
    tag text not null,
    primary key (products_id, tag)
    );''')
    cur.execute('''
    create table stock (
    products_id text not null references products(id),
    size integer not null,
    quantity integer not null,
    primary key (products_id, size)
    );''')
    cur.execute('''
    create table orders (
    id text primary key,
    date text not null,
    products_id text not null references products(id),
    size integer not null,
    price_paid integer not null,
    customers_id text not null
    );''')
    con.commit()
    return

def gettagslist(productcsvlist):
    tagslist = list()
    for row in productcsvlist[1:]:
        productid = row[0]
        tagscsv = row[5]
        for tag in tagscsv.split(','):
            tagslist.append([productid,tag.strip()])
    return tagslist

def getstocklist(productcsvlist):
    stocklist = list()
    for row in productcsvlist[1:]:
        productid = row[0]
        stockjson = row[7].replace("'",'"')
        stockdict = json.loads(stockjson)
        for size,quantity in stockdict.items():
            stocklist.append([productid,int(size),int(quantity)])
    return stocklist

def insertdata(con,cur,productcsvlist,tagslist,stocklist,orderscsvlist):
    for row in productcsvlist[1:]:
        issale = 1 if row[8]=='True' else 0
        isclearance = 1 if row[9]=='True' else 0
        inserttuple = (row[0],row[1],row[2],row[4],row[3],issale,isclearance,row[10])
        cur.execute('insert into products (id,title,vendor,original_price,sale_price,is_sale,is_clearance,bestseller_score) values (?,?,?,?,?,?,?,?);', inserttuple)
    for row in tagslist:
        inserttuple = (row[0],row[1])
        cur.execute('insert into tags (products_id,tag) values (?,?);', inserttuple)
    for row in stocklist:
        inserttuple = (row[0],row[1],row[2])
        cur.execute('insert into stock (products_id,size,quantity) values (?,?,?);', inserttuple)
    for row in orderscsvlist[1:]:
        inserttuple = (row[0],row[1],row[2],row[3],row[4],row[5])
        cur.execute('insert into orders (id,date,products_id,size,price_paid,customers_id) values (?,?,?,?,?,?);', inserttuple)
    con.commit()

def main(dbname, productcsvpath, orderscsvpath):
    if os.path.exists(dbname):
        os.remove(dbname)
    productcsvlist = getcsvlist(productcsvpath)
    tags = getuniquetags(productcsvlist, 5)
    con,cur = createdb(dbname)
    createtables(con,cur)
    tagslist = gettagslist(productcsvlist)
    stocklist = getstocklist(productcsvlist)
    orderscsvlist = getcsvlist(orderscsvpath)
    insertdata(con,cur,productcsvlist,tagslist,stocklist,orderscsvlist)

if __name__=='__main__':
    dbname = 'retail.db'
    productcsvpath = 'files/product_inventory.csv'
    orderscsvpath = 'files/orders.csv'
    main(dbname, productcsvpath, orderscsvpath)

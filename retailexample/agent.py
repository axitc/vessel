# agent configurations and tool functions

model = 'qwen3.5:4b'

systemprompt = 'You are a fashion retail store agent who will attend customers on their queries. Never assume information. Use the given tools freely. Answer queries truthfully.'

tools = [
        {
            'type':'function',
            'function': {
                'name': 'get_valid_keywords',
                'description': 'Returns list of all predefined valid keywords to pick from. Use it to validate and adjust keywords.',
                'parameters': {
                    'type':'object',
                    'properties': {}
                    }
                }
            },
        {
            'type':'function',
            'function': {
                'name': 'search_products',
                'description': 'Get Product IDs filtered by specified product requirements.',
                'parameters': {
                    'type': 'object',
                    'required': [],
                    'properties': {
                        'keywords': {'type':'list of strings', 'description':'List of all the relevant query keywords. Always call get_valid_keywords tool to verify.'},
                        'minimum_price': {'type':'integer', 'description':'Minimum price of product.'},
                        'maximum_price': {'type':'integer', 'description':'Maximum price of product.'},
                        'sizes': {'type':'list of integers', 'description':'List of required garment sizes.'},
                        'is_sale': {'type':'boolean','description':'true if sale products required, else false.'}
                        }
                    }
                }
            },
        {
            'type':'function',
            'function': {
                'name': 'product_ids_to_product_names',
                'description': 'Takes list of Product IDs and fetches their user-friendly titles.',
                'parameters': {
                    'type':'object',
                    'required': ['product_id_list'],
                    'properties': {
                        'product_id_list': {'type':'list of strings', 'description':'Takes list of product ids to be converted to names'}
                        }
                    }
                }
            },
        {
            'type':'function',
            'function': {
                'name': 'get_product_details',
                'description': 'Get details for a specific product such as name, vendor, price, sizes, categories, clearance, rating.',
                'parameters': {
                    'type': 'object',
                    'required': ['product_id'],
                    'properties': {
                        'product_id': {'type':'string', 'description':'Product ID to get the product details for.'}
                        }
                    }
                }
            },
        {
            'type':'function',
            'function': {
                'name': 'get_current_date',
                'description': 'Returns current date in YYYY-MM-DD format. Use it to check return and exchange validity',
                'parameters': {
                    'type': 'object',
                    'properties': {}
                    }
                }
            },
        {
            'type':'function',
            'function': {
                'name': 'process_product_purchase',
                'description': 'Process the purchase of product and return Order ID',
                'parameters': {
                    'type': 'object',
                    'required': ['product_id', 'size'],
                    'properties': {
                        'product_id': {'type':'string', 'description':'Product ID of the product to be purchased'},
                        'size': {'type':'integer', 'description':'Size of the purchased product'}
                        }
                    }
                }
            },
        {
            'type':'function',
            'function': {
                'name': 'get_order_details',
                'description': 'Returns all order details for specific Order ID',
                'parameters': {
                    'type': 'object',
                    'required': ['order_id'],
                    'properties': {
                        'order_id': {'type':'string', 'description':'Order ID of the order to fetch details of'}
                        }
                    }
                }
            },
        {
            'type':'function',
            'function': {
                'name': 'get_policy',
                'description': 'Returns policy document to refer for exchange or return request',
                'parameters': {
                    'type': 'object',
                    'properties': {}
                    }
                }
            },
        {
            'type':'function',
            'function': {
                'name': 'process_product_return',
                'description': 'Process return of product request by user. Refer policy before processing',
                'parameters': {
                    'type': 'object',
                    'required': ['order_id'],
                    'properties': {
                        'order_id': {'type':'string', 'description':'Order ID of the product order to return'}
                        }
                    }
                }
            },
        {
            'type':'function',
            'function': {
                'name': 'process_product_exchange',
                'description': 'Process exchange of product request by user. Refer policy before processing',
                'parameters': {
                    'type': 'object',
                    'required': ['order_id','size'],
                    'properties': {
                        'order_id': {'type':'string', 'description':'Order ID of the product order to exchange'},
                        'size': {'type':'integer', 'description':'Size to exchange ordered product with'}
                        }
                    }
                }
            },
        ]


def executetoolcall(toolcall):
    function = toolcall['function']['name']
    args = toolcall['function']['arguments']
    match function:
        case 'search_products':
            return tool_search_products(args)
        case 'get_valid_keywords':
            return tool_get_available_tags()
        case 'product_ids_to_product_names':
            return tool_product_ids_to_product_names(args)
        case 'get_product_details':
            return tool_get_product_details(args)
        case 'get_current_date':
            return tool_get_current_date()
        case 'process_product_purchase':
            return tool_process_product_purchase(args)
        case 'get_order_details':
            return tool_get_order_details(args)
        case 'get_policy':
            return tool_get_policy()
        case 'process_product_exchange':
            return 'Exchange Request Successful.'
        case 'process_product_return':
            return 'Return Request Successful.'


import sqlite3
import json
import random

DATABASE = 'retail.db'
CUSTOMERID = 'CXYZ'

def tool_get_current_date():
    return '2026-02-25'  # the next date after the latest date in orders table

def tool_process_product_purchase(args):
    productid = args['product_id']
    size = args['size']
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    orderid = 'O' + str(int(1000*random.random()))
    date = tool_get_current_date()
    cur.execute('select sale_price from products where id=?;', (productid,))
    pricepaid = cur.fetchone()[0]
    cur.execute('insert into orders (id,date,products_id,size,price_paid,customers_id) values (?,?,?,?,?,?);', (orderid,date,productid,size,pricepaid,CUSTOMERID))
    con.commit()
    con.close()
    return 'Purchase Successful. Order ID - ' + orderid

def getallproductidset(cur):
    cur.execute('select id from products;')
    result = cur.fetchall()
    setproductids = set([row[0] for row in result])
    return setproductids

def intersecttags(cur,setproductids,args):
    if 'keywords' not in args:
        return setproductids
    tags = args['keywords']
    if type(tags)==str:
        tags = json.loads(tags)
    tags = [tag.lower() for tag in tags]
    atomictags = list()
    for tag in tags:
        atomictags.extend(tag.split(' '))
    settagproductids = set()
    for tag in atomictags:
        cur.execute('select p.id from products as p inner join tags as t on p.id=t.products_id where t.tag=?;', (tag,))
        result = cur.fetchall()
        settagproductids = settagproductids.union(set([row[0] for row in result]))
    #if len(settagproductids) != 0:
    #    setproductids = setproductids.intersection(settagproductids)
    setproductids = setproductids.intersection(settagproductids)
    return setproductids

def intersectsizes(cur,setproductids,args):
    if 'sizes' not in args:
        return setproductids
    sizes = args['sizes']
    if type(sizes)==str:
        sizes = json.loads(sizes)
    setsizeproductids = set()
    for size in sizes:
        cur.execute('select p.id from products as p inner join stock as s on p.id=s.products_id where size=? and quantity>0;', (size,))
        result = cur.fetchall()
        setsizeproductids = setsizeproductids.union(set([row[0] for row in result]))
    setproductids = setproductids.intersection(setsizeproductids)
    return setproductids

def intersectsale(cur,setproductids,args):
    if 'is_sale' not in args:
        return setproductids
    issale = args['is_sale']
    cur.execute('select id from products where is_sale=?;', ((1 if issale==True else 0),))
    result = cur.fetchall()
    setsaleproductids = set([row[0] for row in result])
    setproductids = setproductids.intersection(setsaleproductids)
    return setproductids

def intersectmaxprice(cur,setproductids,args):
    if 'maximum_price' not in args:
        return setproductids
    maxprice = args['maximum_price']
    cur.execute('select id from products where sale_price<?;', (maxprice,))
    result = cur.fetchall()
    setmaxpriceproductids = set([row[0] for row in result])
    setproductids = setproductids.intersection(setmaxpriceproductids)
    return setproductids

def intersectminprice(cur,setproductids,args):
    if 'minimum_price' not in args:
        return setproductids
    minprice = args['minimum_price']
    cur.execute('select id from products where sale_price>?;', (minprice,))
    result = cur.fetchall()
    setminpriceproductids = set([row[0] for row in result])
    setproductids = setproductids.intersection(setminpriceproductids)
    return setproductids

def getbestsellersortedproductids(cur,listproductids):
    idscorepairs = list()
    for i in range(len(listproductids)):
        cur.execute('select bestseller_score from products where id=?;', (listproductids[i],))
        bestsellerscore = cur.fetchone()[0]
        idscorepairs.append([listproductids[i],bestsellerscore])
    idscorepairs = reversed(sorted(idscorepairs, key=lambda x:x[1]))
    bestsellersortedproductids = [pair[0] for pair in idscorepairs]
    return bestsellersortedproductids

def tool_search_products(args):
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    setproductids = getallproductidset(cur)
    # - - - - -
    setproductids = intersectsale(cur,setproductids,args)
    setproductids = intersecttags(cur,setproductids,args)
    setproductids = intersectmaxprice(cur,setproductids,args)
    setproductids = intersectminprice(cur,setproductids,args)
    setproductids = intersectsizes(cur,setproductids,args)
    # - - - - -
    listproductids = list(setproductids)
    listproductids = getbestsellersortedproductids(cur,listproductids)
    con.close()
    listproductids = listproductids[:5]  # top n results only
    if len(listproductids)==0:
        return 'No products found with specified constraints.'
    formattedproductids = '\n'.join(listproductids)
    return formattedproductids

def productidtoproductname(cur,productid):
    cur.execute('select title from products where id=?;', (productid,))
    result = cur.fetchone()
    productname = result[0]
    return productname

def tool_product_ids_to_product_names(args):
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    productids = args['product_id_list']
    if type(productids)==str:
        productids = json.loads(productids)
    productnames = list(map(productidtoproductname,[cur for i in range(len(productids))],productids))
    con.close()
    formattedproductnames = '\n'.join(productnames)
    return formattedproductnames

def tool_get_available_tags():
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    cur.execute('select distinct tag from tags;')
    result = cur.fetchall()
    con.close()
    tags = [row[0] for row in result]
    formattedtags = '\n'.join(tags)
    return formattedtags

def tool_get_product_details(args):
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    productid = args['product_id']
    resultstring = ''
    cur.execute('select title,vendor,sale_price,original_price,is_clearance,bestseller_score from products where id=?;',(productid,))
    result = cur.fetchone()
    if result==None:
        return 'Error - Product not found'
    resultstring += 'Product ID - ' + productid + '\n'
    resultstring += 'Title - ' + result[0] + '\n'
    resultstring += 'Vendor - ' + result[1] + '\n'
    resultstring += 'Original Price - $' + str(result[3]) + '\n'
    resultstring += 'Sale Price - $' + str(result[2]) + '\n'
    resultstring += 'Limited (Clearance Item) - ' + ('Yes' if result[4]==1 else 'No') + '\n'
    resultstring += 'Bestseller Score - ' + str(result[5]) + '\n'
    cur.execute('select size from stock where quantity>0 and products_id=?;',(productid,))
    result = cur.fetchall()
    sizes = [row[0] for row in result]
    resultstring += 'Available Sizes - ' + str(sizes) + '\n'
    cur.execute('select tag from tags where products_id=?;',(productid,))
    result = cur.fetchall()
    tags = [row[0] for row in result]
    resultstring += 'Tags - ' + str(tags)
    return resultstring

def tool_get_order_details(args):
    orderid = args['order_id']
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    cur.execute('select date,products_id,size,price_paid,customers_id from orders where id=?;', (orderid,))
    result = cur.fetchone()
    con.close()
    if result==None:
        return 'Error - Order not found'
    resultstring = ''
    resultstring += 'Order ID - ' + orderid + '\n'
    resultstring += 'Order Date - ' + str(result[0]) + '\n'
    resultstring += 'Product ID - ' + result[1] + '\n'
    resultstring += 'Product Size - ' + str(result[2]) + '\n'
    resultstring += 'Price Paid - $' + str(result[3]) + '\n'
    resultstring += 'Customer ID - ' + result[4] + '\n'
    return resultstring

def tool_get_policy():
    with open('files/policy.txt') as f:
        policytext = f.read()
    policytext += '\nNote: All deliveries are done within order date.\n'
    return policytext

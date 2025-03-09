import pandas as pd
from flask import  render_template
import pymysql

def connect_db():
    return pymysql.connect(
        host='localhost',       # Host where MySQL is running
        user='root',            # Your MySQL username
        password='Vijaya@23',   # Your MySQL password
        database='dataset' ,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor      
    )

def sales_performance():
    conn = connect_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    query = """
    SELECT s.`Product ID`, p.`Product Name`, p.Category, 
           SUM(s.`Quantity Sold`) AS Total_Quantity_Sold, 
           SUM(s.Price * s.`Quantity Sold`) AS Total_Sales_Amount, 
           SUM(s.Price * s.`Quantity Sold`- p.`Actual Price` * s.`Quantity Sold`) AS Profit_Loss, 
           i.`Stock Level` 
    FROM sales_data s 
    JOIN product_data p ON s.`Product ID` = p.`Product ID`
    JOIN inventory_data i ON s.`Product ID` = i.`Product ID`
    GROUP BY s.`Product ID`, p.`Product Name`, p.Category, i.`Stock Level`
    ORDER BY Total_Sales_Amount DESC
    """
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()
    return render_template('sales_performance.html', data=data)

def customer_insights():
    conn = connect_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    query = """
    SELECT c.`Customer ID`, c.`Customer Name`, 
           SUM(s.Price * s.`Quantity Sold`) AS Total_Sales_Amount, 
           COUNT(s.`Sales ID`) AS Number_of_Purchases, 
           AVG(s.Price * s.`Quantity Sold`) AS Average_Sales_Per_Purchase
    FROM sales_data s
    JOIN customer_data c ON s.`Sales ID` = c.`Sales ID`
    GROUP BY c.`Customer ID`, c.`Customer Name`
    ORDER BY Total_Sales_Amount DESC
    """
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()
    return render_template('customer_insights.html', data=data)

def inventory_management():
    conn = connect_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    query = """
    SELECT i.`Product ID`, p.`Product Name`, p.Category, 
           i.`Stock Level`, p.`Reorder Level`, i.`Refill Quantity`, i.`Date of Last Refill` 
    FROM inventory_data i
    JOIN product_data p ON i.`Product ID` = p.`Product ID`
    ORDER BY i.`Stock Level` ASC
    """
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()
    return render_template('inventory_management.html', data=data)

def supplier_performance():
    conn = connect_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    query = """
    SELECT s.`Supplier ID`, s.`Supplier Name`, p.`Product Name`, 
           s.`Lead Time`, i.`Date of Last Refill` 
    FROM supplier_data s
    JOIN product_data p ON s.`Supplier Name` = p.`Supplier Name`
    JOIN inventory_data i ON p.`Product ID` = i.`Product ID`
    ORDER BY s.`Lead Time` ASC
    """
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()
    return render_template('supplier_performance.html', data=data)

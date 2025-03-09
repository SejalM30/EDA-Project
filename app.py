from flask import Flask, render_template, request, redirect, flash,send_from_directory,url_for,session
import os
import pandas as pd
import pymysql
from eda import get_plots
from common import common_plots
from customer import  customer_plots # function that generates plots
from queries import sales_performance, customer_insights, inventory_management, supplier_performance 
from datetime import date
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database connection function
def connect_db():
    return pymysql.connect(
        host='localhost',       # Host where MySQL is running
        user='root',            # Your MySQL username
        password='Vijaya@23',   # Your MySQL password
        database='dataset' ,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor      
    )

@app.route('/')
def s():
    return render_template('login.html')

# Registration Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        conn = connect_db()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                (username, email, password)
            )
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login_page'))
        except pymysql.MySQLError as err:
            flash(f"Registration error: {err}", 'danger')
        finally:
            cursor.close()
            conn.close()

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = connect_db()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM users WHERE username = %s AND password = %s", 
            (username, password)
        )
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            session['username'] = user['username']
            flash(f"Welcome {user['username']}!", 'success')
            return redirect(url_for('home'))
        else:
            flash("Invalid credentials. Please try again.", 'danger')

    return render_template('login.html')

@app.route('/home')
def home():
    return render_template('home.html')

# Start the Flask app in a separate thread
@app.route('/recommend_restock', methods=['GET', 'POST'])
def recommend_restock():
    conn = connect_db()

    # Monthly Sales Forecast
    monthly_sales_query = """
    SELECT DATE_FORMAT(`Date of Sale`, '%Y-%m') AS Month, SUM(`Quantity Sold`) AS Total_Sales
FROM sales_data
GROUP BY Month
ORDER BY Month;

    """
    cursor = conn.cursor()
    cursor.execute(monthly_sales_query)
    monthly_sales = cursor.fetchall()


    # ABC Analysis
    product_sales_query = """
    SELECT s.`Product ID`, p.`Product Name`, p.`Actual Price`, 
           SUM(s.`Quantity Sold`) AS Total_Sold,
           (SUM(s.`Quantity Sold`) * p.`Actual Price`) AS Total_Value
    FROM sales_data s
    JOIN product_data p ON s.`Product ID` = p.`Product ID`
    GROUP BY s.`Product ID`
    ORDER BY Total_Value DESC;
    """
    cursor.execute(product_sales_query)
    product_sales = cursor.fetchall()
    # Lead Time Check
    supplier_performance_query = """
     SELECT `Supplier Name`, 
       AVG(CAST(SUBSTRING_INDEX(`Lead Time`, ' ', 1) AS UNSIGNED)) AS Avg_Lead_Time
      FROM supplier_data
      GROUP BY `Supplier Name`
ORDER BY Avg_Lead_Time ASC;
    """
    cursor.execute(supplier_performance_query)
    supplier_performance = cursor.fetchall()

    conn.close()
    return render_template(
        'recommend_restock.html',
        monthly_sales=monthly_sales,
        product_sales=product_sales,
        supplier_performance=supplier_performance
    )


@app.route('/sales_dashboard', methods=['GET', 'POST'])
def sales_dashboard():
    selected_product = request.form.get('product_name', 'All')
    plots = get_plots(selected_product)
    # Get product names for dropdown
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='Vijaya@23',
        database='dataset'
    )
    product_df = pd.read_sql("SELECT DISTINCT `Product Name` FROM product_data", conn)
    conn.close()

    product_list = ["All"] + list(product_df["Product Name"])

    return render_template('dashboard.html', plots=plots, product_list=product_list)

# Serve static images (for plots)
@app.route('/static/plots/<filename>')
def plot_image(filename):
    return send_from_directory(os.path.join(app.root_path, 'static', 'plots'), filename)
    
@app.route('/customer_dashboard', methods=['GET', 'POST'])
def customer_dashboard():
    selected_customers = request.form.getlist('customer_name')  # Get selected customer names as a list

    if not selected_customers:  # Default to 'All' if no customers are selected
        selected_customers = ['All']

    # Call customer_plots with selected customers
    plots = customer_plots(selected_customers)

    # Get product names for dropdown
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='Vijaya@23',
        database='dataset'
    )
    customer_df = pd.read_sql("SELECT DISTINCT `Customer Name` FROM customer_data", conn)
    conn.close()

    customer_list = ["All"] + list(customer_df["Customer Name"])
    
    return render_template('customer_dashboard.html', customer_list=customer_list, plots=plots)

@app.route('/common_dashboard', methods=['GET', 'POST'])
def common_dashboard():
    plots= common_plots()  # Unpack the return values of common_plots

    # Pass both the plots and the data (top_customers) to the template
    return render_template('common.html', plots=plots)

@app.route('/get_product_details', methods=['POST'])
def get_product_details():
    product_id = request.form['product_id']
    conn = connect_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # Fetch product details
        cursor.execute("""
            SELECT p.`Product ID`, p.`Product Name`, p.`Category`, i.`Stock Level`, p.`Supplier Name`, p.`Reorder Level`
            FROM product_data p
            JOIN inventory_data i ON p.`Product ID` = i.`Product ID`
            WHERE p.`Product ID` = %s;
        """, (product_id,))
        product_details = cursor.fetchone()

        if product_details:
            return render_template('index.html', title='Sales Dashboard', product_details=product_details)
        else:
            flash('Product not found!', 'warning')
            return redirect('/home')

    except pymysql.MySQLError as e:
        flash(f'Error: {e}', 'danger')
        return redirect('/home')
    finally:
        cursor.close()
        conn.close()

@app.route('/refill_products', methods=['GET', 'POST'])
def refill_products():
    if request.method == 'POST':
        product_id = request.form['product_id']
        
        # Connect to the database
        conn = connect_db()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        try:
            # Fetch product details and check if it needs refill
            cursor.execute("""
                SELECT p.`Product ID`, p.`Product Name`, p.`Category`, i.`Stock Level`, p.`Reorder Level`,p.`Actual Price`
                FROM product_data p
                JOIN inventory_data i ON p.`Product ID` = i.`Product ID`
                WHERE p.`Product ID` = %s;
            """, (product_id,))
            product_details = cursor.fetchone()

            if product_details:
                # Get the current stock level and reorder level
                current_stock = product_details['Stock Level']
                reorder_level = product_details['Reorder Level']
                
                # Check if refill is needed
                refill_required = current_stock < reorder_level
                message = "Refill is required!" if refill_required else "Stock level is sufficient, no refill required."

                # Handle refill logic, if refill amount is provided
                if 'refill_amount' in request.form:
                    refill_amount = int(request.form['refill_amount'])
                    new_stock_level = current_stock + refill_amount

                    # Update the stock level and refill quantity
                    cursor.execute("""
                        UPDATE inventory_data
                        SET `Stock Level` = %s, `Refill Quantity` = `Refill Quantity` + %s, `Date of Last Refill` = CURDATE()
                        WHERE `Product ID` = %s;
                    """, (new_stock_level, refill_amount, product_id))
                    conn.commit()

                    # After refill, update message
                    message = f"Product {product_id} refilled by {refill_amount}. New stock level is {new_stock_level}."

                return render_template('refill_products.html', product_details=product_details, message=message)

            else:
                flash("Product not found.", 'warning')
                return redirect('/refill_products')

        except pymysql.MySQLError as e:
            flash(f"Error: {e}", 'danger')
            return redirect('/refill_products')
        finally:
            cursor.close()
            conn.close()

    return render_template('refill_products.html')

@app.route('/products_to_refill')
def products_to_refill():
    conn = connect_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    try:
        # Query to get products needing refill
        cursor.execute("""
            SELECT p.`Product ID`, p.`Product Name`, p.`Category`, i.`Stock Level`, p.`Reorder Level`
            FROM product_data p
            JOIN inventory_data i ON p.`Product ID` = i.`Product ID`
            WHERE i.`Stock Level` < p.`Reorder Level`;
        """)
        products_to_refill = cursor.fetchall()

        if not products_to_refill:
            flash('No products need refilling at the moment.', 'info')
        
        return render_template('products_to_refill.html', products=products_to_refill)

    except pymysql.MySQLError as e:
        flash(f'Error: {e}', 'danger')
        return redirect('/home')
    finally:
        cursor.close()
        conn.close()

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        product_name = request.form['product_name']
        category = request.form['category']
        actual_price = request.form['actual_price']
        supplier_name = request.form['supplier_name']
        reorder_level = request.form['reorder_level']
        

        conn = connect_db()
        cursor = conn.cursor()

        try:
            

            # Insert new product into the product_data table
            cursor.execute("""
                INSERT INTO product_data (`Product Name`, `Category`, `Actual Price`, `Supplier Name`, `Reorder Level`)
                VALUES (%s, %s, %s, %s, %s)
            """, ( product_name, category, actual_price, supplier_name, reorder_level))

            # Insert the stock level into the inventory_data table for the selected store location
            cursor.execute("""
            INSERT INTO inventory_data (`Product ID`, `Stock Level`, `Date of Last Refill`, `Refill Quantity`)
            VALUES (%s, %s, CURDATE(), %s)
            """, (cursor.lastrowid, 0, 0))  # Use last inserted Product ID


            conn.commit()

            flash(f"Product '{product_name}' added successfully ", 'success')
        except pymysql.MySQLError as e:
            flash(f"Database error: {e}", 'danger')
        finally:
            cursor.close()
            conn.close()

        return redirect('/home')

    return render_template('add_product.html')

@app.route('/delete_product', methods=['GET', 'POST'])
def delete_product():
    if request.method == 'POST':
        product_id = request.form['product_id']

        conn = connect_db()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                DELETE FROM product_data WHERE `Product ID` = %s
            """, (product_id,))
            conn.commit()
            flash(f"Product with ID {product_id} deleted successfully!", 'success')
        except pymysql.MySQLError as e:
            flash(f"Error: {e}", 'danger')
        finally:
            cursor.close()
            conn.close()

        return redirect('/home')

    return render_template('delete_product.html')
@app.route('/add_supplier', methods=['GET', 'POST'])
def add_supplier():
    if request.method == 'POST':
        supplier_name = request.form['supplier_name']
        contact_details = request.form['contact_details']
        lead_time = request.form['lead_time']

        conn = connect_db()
        cursor = conn.cursor()

        try:
            # Fetch the last Supplier ID
            cursor.execute("SELECT `Supplier ID` FROM supplier_data ORDER BY `Supplier ID` DESC LIMIT 1")
            max_id = cursor.fetchone()

            if max_id and max_id['Supplier ID']:
                # Extract the numeric part of the Supplier ID and increment it
                last_id = max_id['Supplier ID']
                numeric_part = int(last_id[1:])  # Assuming the format is 'S01'
                new_numeric_part = numeric_part + 1
                new_supplier_id = f"S{new_numeric_part:02}"  # Generates IDs like S01, S02, etc.
            else:
                new_supplier_id = "S01"  # Start from S01 if no IDs exist

            # Insert the new supplier into the database
            cursor.execute("""
                INSERT INTO supplier_data(`Supplier ID`, `Supplier Name`, `Contact Details`, `Lead Time`)
                VALUES (%s, %s, %s, %s)
            """, (new_supplier_id, supplier_name, contact_details, lead_time))

            conn.commit()

            flash(f"Supplier '{supplier_name}' added successfully with Supplier ID: {new_supplier_id}", 'success')
        except pymysql.MySQLError as e:
            flash(f"Database error: {e}", 'danger')
        finally:
            cursor.close()
            conn.close()

        return redirect('/home')

    return render_template('add_supplier.html')
@app.route('/delete_supplier', methods=['GET', 'POST'])
def delete_supplier():
    if request.method == 'POST':
        supplier_id = request.form['supplier_id']

        conn = connect_db()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                DELETE FROM supplier_data WHERE `Supplier ID` = %s
            """, (supplier_id,))
            conn.commit()
            flash(f"Supplier with ID {supplier_id} deleted successfully!", 'success')
        except pymysql.MySQLError as e:
            flash(f"Error: {e}", 'danger')
        finally:
            cursor.close()
            conn.close()

        return redirect('/home')    
    return render_template('delete_supplier.html')


# Manage Sales Route
@app.route('/manage_sales', methods=['GET', 'POST'])
def manage_sales():
    if request.method == 'POST':
        # Extract form data
        customer_id = request.form['customer_id']
        product_id = request.form['product_id']
        quantity_sold = int(request.form['quantity_sold'])
        price = float(request.form['price'])
        store_location = request.form['store_location']
        date_of_sale = date.today().strftime("%Y-%m-%d")

        conn = connect_db()
        cursor = conn.cursor()

        try:
            # Check if customer exists
            cursor.execute("SELECT * FROM customer_data WHERE `Customer ID` = %s", (customer_id,))
            customer = cursor.fetchone()

            if not customer:
                flash("Customer not found!", "warning")
                return redirect('/manage_sales')

            # Disable foreign key checks
            cursor.execute("SET FOREIGN_KEY_CHECKS=0;")

            # Corrected Insert Query
            insert_sales_query = """
                INSERT INTO sales_data ( `Product ID`, `Date of Sale`, `Quantity Sold`, `Store Location`, `Price`)
                VALUES ( %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_sales_query, (product_id, date_of_sale, quantity_sold, store_location, price))
            
            # Re-enable foreign key checks
            cursor.execute("SET FOREIGN_KEY_CHECKS=1;")
            

            # Update inventory stock
            update_inventory_query = """
                UPDATE inventory_data
                SET `Stock Level` = `Stock Level` - %s
                WHERE `Product ID` = %s
            """
            cursor.execute(update_inventory_query, (quantity_sold, product_id))

            conn.commit()
            flash("Sales data recorded successfully!", "success")
            return redirect('/manage_sales')

        except pymysql.MySQLError as e:
            conn.rollback()
            flash(f"Database error: {e}", "danger")
            return redirect('/manage_sales')

        finally:
            cursor.close()
            conn.close()

    return render_template('manage_sales.html')
 

@app.route('/sales-performance')
def sales_performance_view():
    return sales_performance()

@app.route('/customer-insights')
def customer_insights_view():
    return customer_insights()

@app.route('/inventory-management')
def inventory_management_view():
    return inventory_management()

@app.route('/supplier-performance')
def supplier_performance_view():
    return supplier_performance()
if __name__ == "__main__":
    app.run(debug=True)

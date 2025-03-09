import pandas as pd 
import seaborn as sns
import matplotlib
import matplotlib.pyplot as plt
import io
import base64
import pymysql
matplotlib.use('Agg') 
# Connect to the MySQL database
def connect_db():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='Vijaya@23',
        database='dataset'
    )

# Convert plot to base64-encoded image
def plot_to_base64():
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)
    encoded_img = base64.b64encode(buffer.read()).decode('utf-8')
    buffer.close()
    plt.close()
    return f"data:image/png;base64,{encoded_img}"

# Merge sales data with customer data for customer-specific analysis
def customer_plots(selected_customers=None):
    if selected_customers is None or len(selected_customers) == 0:
        selected_customers = ['All']  # Default to all customers if none are selected

    conn = connect_db()

    # Load data from the database
    sales_df = pd.read_sql("SELECT * FROM sales_data", conn)
    customer_df = pd.read_sql("SELECT * FROM customer_data", conn)
    product_df = pd.read_sql("SELECT * FROM product_data", conn)
        
    conn.close()
    sales_df.fillna({'Quantity Sold': 0, 'Store Location': 'Unknown'}, inplace=True)
    product_df.fillna({'Supplier Name': 'Unknown'}, inplace=True)
    # Merge the sales and customer data
    merged_data = pd.merge(sales_df, customer_df, on='Sales ID', how='left')

    # Ensure 'Date' column is in datetime format
    merged_data['Date of Sale'] = pd.to_datetime(merged_data['Date of Sale'], errors='coerce')

    # Handle any missing or invalid dates (if any)
    merged_data = merged_data.dropna(subset=['Date of Sale'])

    # If 'All' is selected, use all data
    if 'All' not in selected_customers:
        # Filter by selected customers
        filtered_data = merged_data[merged_data['Customer Name'].isin(selected_customers)]
    else:
        filtered_data = merged_data

    # Check if the filtered data is empty
    if filtered_data.empty:
        print("No data available for the selected customers.")
        return {}

    plots = {}

    # Graph 1: Total Quantity Sold per Customer
    plt.figure(figsize=(12, 6))
    sales_per_customer = filtered_data.groupby('Customer Name')['Quantity Sold'].sum().sort_values(ascending=False)
    sales_per_customer.plot(kind='bar', color='skyblue', width=0.7)
    plt.title('Total Quantity Sold per Customer', fontsize=16)
    plt.xlabel('Customer Name', fontsize=12)
    plt.ylabel('Total Quantity Sold', fontsize=12)
    plt.xticks(rotation=45, ha='right', fontsize=10)
    plots['Q_S_P_R'] = plot_to_base64()

    # Graph 2: Sales Trend Over Time by Customer
    plt.figure(figsize=(12, 6))
    sales_trend_customer = filtered_data.groupby(['Date of Sale', 'Customer Name'])['Quantity Sold'].sum().unstack().fillna(0)
    sales_trend_customer.plot(kind='line', linewidth=2)
    plt.title('Sales Trend Over Time by Customer', fontsize=16)
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Quantity Sold', fontsize=12)
    plt.xticks(rotation=45, ha='right', fontsize=10)
    plt.legend(title='Customer Name', bbox_to_anchor=(1.05, 1), loc='upper left')
    plots['Sales_Trend'] = plot_to_base64()

    # Graph 3: Distribution of Product Categories Purchased by Each Customer
    plt.figure(figsize=(14, 7))
    product_category_customer = pd.merge(filtered_data, product_df, on='Product ID', how='left')
    product_category_counts = product_category_customer.groupby(['Customer Name', 'Category'])['Quantity Sold'].sum().unstack().fillna(0)
    product_category_counts.plot(kind='bar', stacked=True, figsize=(14, 7), width=0.8)
    plt.title('Distribution of Product Categories Purchased by Each Customer', fontsize=16)
    plt.xlabel('Customer Name', fontsize=12)
    plt.ylabel('Total Quantity Sold', fontsize=12)
    plt.xticks(rotation=90, ha='center', fontsize=8)
    plt.legend(title='Product Category', bbox_to_anchor=(1.05, 1), loc='upper left')
    plots['Distribution_of_product_category'] = plot_to_base64()

    # Graph 4: Pie Chart of Total Sales per Customer (Top 10)
    plt.figure(figsize=(8, 8))
    customer_sales_pie = sales_per_customer.sort_values(ascending=False)
    customer_sales_pie.plot.pie(autopct='%1.1f%%', startangle=140, cmap='tab20', fontsize=10)
    plt.title('Pie Chart of Total Sales per Customer ', fontsize=16)
    plots['piechart'] = plot_to_base64()




    # Graph 7: Top 5 Customers by Frequency of Purchases (Bar Chart)
    plt.figure(figsize=(12, 6))
    customer_purchase_freq = filtered_data['Customer Name'].value_counts()
    customer_purchase_freq.plot(kind='bar', color='lightgreen', width=0.7)
    plt.title(' Customers by Frequency of Purchases', fontsize=16)
    plt.xlabel('Customer Name', fontsize=12)
    plt.ylabel('Number of Purchases', fontsize=12)
    plt.xticks(rotation=45, ha='right', fontsize=10)
    plots['frequency_of_purchase'] = plot_to_base64()

    return plots

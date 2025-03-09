import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib
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

# Generate plots using Seaborn
def common_plots():
    conn = connect_db()

    # Load data from the database
    sales_df = pd.read_sql("SELECT * FROM sales_data", conn)
    product_df = pd.read_sql("SELECT * FROM product_data", conn)
    inventory_df = pd.read_sql("SELECT * FROM inventory_data", conn)
    customer_df = pd.read_sql("SELECT * FROM customer_data", conn)
    
    conn.close()

    # Data cleaning
    sales_df.fillna({'Quantity Sold': 0, 'Store Location': 'Unknown'}, inplace=True)
    inventory_df.fillna({'Stock Level': 0, 'Refill Quantity': 0}, inplace=True)
    product_df.fillna({'Supplier Name': 'Unknown'}, inplace=True)

    merged_data = pd.merge(sales_df, customer_df, on='Sales ID', how='left')
    merged_data = pd.merge(merged_data, product_df, on='Product ID', how='left')
    merged_data['Profit'] = merged_data['Actual Price'] - merged_data['Price']

    plots = {}

    # 1. Top 10 Customers by Sales
    plt.figure(figsize=(12, 6))
    top_customers = merged_data.groupby('Customer Name')['Price'].sum().nlargest(10)
    sns.barplot(x=top_customers.index, y=top_customers.values, palette='Blues_d')
    plt.title('Top 10 Customers by Sales')
    plt.xlabel('Customer Name')
    plt.ylabel('Total Sales')
    plt.xticks(rotation=45, ha='right')
    plots['customer_sales_10'] = plot_to_base64()

    # 2. Least 10 Customers by Sales
    plt.figure(figsize=(12, 6))
    least_customers = merged_data.groupby('Customer Name')['Price'].sum().nsmallest(10)
    sns.barplot(x=least_customers.index, y=least_customers.values, palette='Reds')
    plt.title('Least 10 Customers by Sales')
    plt.xlabel('Customer Name')
    plt.ylabel('Total Sales')
    plt.xticks(rotation=45, ha='right')
    plots['customer_sales_11'] = plot_to_base64()

    # 3. Profit and Loss Analysis
    plt.figure(figsize=(12, 6))
    profit_loss = merged_data.groupby('Product Name')['Profit'].sum().sort_values()
    sns.barplot(x=profit_loss.index, y=profit_loss.values,
                palette=['red' if x < 0 else 'green' for x in profit_loss])
    plt.title('Profit and Loss by Product')
    plt.xlabel('Product Name')
    plt.ylabel('Profit')
    plt.xticks(rotation=90)
    plots['customer_sales_12'] = plot_to_base64()

    # 4. Product-wise Sales Distribution
    plt.figure(figsize=(8, 8))
    product_sales = merged_data.groupby('Category')['Price'].sum()
    product_sales.plot(kind='pie', autopct='%1.1f%%', startangle=140, cmap='Set3')
    plt.title('Product-wise Sales Distribution')
    plt.ylabel('')
    plots['customer_sales_13'] = plot_to_base64()

    # 5. Supplier Contribution Analysis
    plt.figure(figsize=(10, 6))
    supplier_contribution = product_df.groupby('Supplier Name')['Product Name'].count()
    sns.barplot(x=supplier_contribution.index, y=supplier_contribution.values, palette='Oranges')
    plt.title('Supplier Contribution Analysis')
    plt.xlabel('Supplier Name')
    plt.ylabel('Products Supplied')
    plt.xticks(rotation=45, ha='right')
    plots['customer_sales_15'] = plot_to_base64()

    # 6. Customer Purchase Frequency
    plt.figure(figsize=(12, 6))
    customer_frequency = merged_data['Customer Name'].value_counts().head(10)
    sns.barplot(x=customer_frequency.index, y=customer_frequency.values, palette='Greens')
    plt.title('Top 10 Customers by Purchase Frequency')
    plt.xlabel('Customer Name')
    plt.ylabel('Number of Purchases')
    plt.xticks(rotation=45, ha='right')
    plots['customer_sales_16'] = plot_to_base64()

    # 7. Cumulative Sales Contribution
    plt.figure(figsize=(10, 6))
    cumulative_sales = top_customers.cumsum() / top_customers.sum()
    sns.lineplot(x=top_customers.index, y=cumulative_sales, marker='o', color='brown')
    plt.title('Cumulative Sales Contribution')
    plt.xlabel('Customer Name')
    plt.ylabel('Cumulative Percentage')
    plt.xticks(rotation=45)
    plots['customer_sales_17'] = plot_to_base64()

    # 8. Loss-Making Products
    plt.figure(figsize=(12, 6))
    loss_making_products = profit_loss[profit_loss < 0]
    sns.barplot(x=loss_making_products.index, y=loss_making_products.values, color='red')
    plt.title('Loss-Making Products')
    plt.xlabel('Product Name')
    plt.ylabel('Loss')
    plt.xticks(rotation=90)
    plots['customer_sales_18'] = plot_to_base64()

    return plots

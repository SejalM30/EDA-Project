import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import io
import base64
import pymysql
import matplotlib
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

# Generate plots and return base64-encoded images
def get_plots(selected_product="All"):
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

    # Merge dataframes
    merged_sales_product = pd.merge(sales_df, product_df, on='Product ID', how='left')
    merged_inventory = pd.merge(product_df, inventory_df, on='Product ID', how='left')
    merged_data = pd.merge(sales_df, customer_df, on='Sales ID', how='left')
    merged_data = pd.merge(merged_data, product_df, on='Product ID', how='left')

    # Check for missing or inconsistent values in required columns
    required_columns = ['Product Name', 'Age', 'Gender', 'Price']
    for col in required_columns:
      if col not in merged_data.columns:
        raise KeyError(f"Column '{col}' is missing in the merged dataset.")

    merged_data = merged_data.dropna(subset=required_columns)  # Remove rows with missing data in required columns
    # Filter data by selected product
    if selected_product != "All":
        filtered_sales = merged_sales_product[merged_sales_product["Product Name"] == selected_product]
        filtered_inventory = merged_inventory[merged_inventory["Product Name"] == selected_product]
        filtered_data = merged_data[merged_data["Product Name"] == selected_product]
    else:
        filtered_sales = merged_sales_product
        filtered_inventory = merged_inventory
        filtered_data=merged_data

    plots = {}

    # Plot 1: Distribution of Quantity Sold
    plt.figure(figsize=(10, 6))
    sns.histplot(filtered_sales['Quantity Sold'], bins=20, kde=True, color='blue')
    plt.title("Distribution of Quantity Sold")
    plt.xlabel("Quantity Sold")
    plt.ylabel("Frequency")
    plots['quantity_sold_distribution'] = plot_to_base64()

    # Plot 2: Total Sales by Store Location
    store_sales = filtered_sales.groupby('Store Location')['Quantity Sold'].sum().reset_index()
    plt.figure(figsize=(8, 8))
    plt.pie(store_sales['Quantity Sold'], labels=store_sales['Store Location'], autopct='%1.1f%%', startangle=140)
    plt.title("Total Sales by Store Location")
    plots['sales_by_store'] = plot_to_base64()

    # Plot 3: Product Category Analysis
    category_sales = filtered_sales.groupby('Category')['Quantity Sold'].sum().reset_index()
    plt.figure(figsize=(10, 6))
    sns.barplot(x='Category', y='Quantity Sold', data=category_sales, palette='coolwarm')
    plt.title("Total Sales by Product Category")
    plt.xticks(rotation=45)
    plots['category_analysis'] = plot_to_base64()

    # Plot 4: Inventory Refill Analysis
    plt.figure(figsize=(12, 6))
    sns.barplot(x='Product Name', y='Refill Quantity', data=filtered_inventory, color='green')
    plt.title("Inventory Refill Analysis")
    plt.xticks(rotation=45, ha='right')
    plots['inventory_refill'] = plot_to_base64()

    # Plot 5: Sales Trend Over Time
    if not filtered_sales.empty:
        plt.figure(figsize=(12, 6))
        sns.lineplot(x='Date of Sale', y='Quantity Sold', data=filtered_sales)
        plt.title("Sales Trend Over Time")
        plt.xticks(rotation=45)
        plots['sales_trend'] = plot_to_base64()

    # Plot 6: Top 10 Products by Quantity Sold
    top_products = filtered_sales.groupby('Product Name')['Quantity Sold'].sum().nlargest(35).reset_index()
    plt.figure(figsize=(12, 6))
    sns.barplot(x='Product Name', y='Quantity Sold', data=top_products, color='purple')
    plt.title("Top 10 Products by Quantity Sold")
    plt.xticks(rotation=45, ha='right')
    plots['top_products'] = plot_to_base64()


    # Plot 7: Age Distribution of Customers
    plt.figure(figsize=(12, 6))
    sns.histplot(filtered_data['Age'], bins=15, kde=True, color='blue', alpha=0.7)
    plt.title(f'Customer Age Distribution for {selected_product}', fontsize=16)
    plt.xlabel('Age', fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plots['age'] = plot_to_base64()

    # Plot 8: Gender Contribution in Sales
    plt.figure(figsize=(8, 6))
    gender_sales = filtered_data.groupby('Gender')['Price'].sum().reset_index()
    sns.barplot(x='Gender', y='Price', data=gender_sales, palette=[ 'pink','skyblue'])
    plt.title(f'Gender Contribution in Sales for {selected_product}', fontsize=16)
    plt.xlabel('Gender', fontsize=12)
    plt.ylabel('Total Sales', fontsize=12)
    plots['gender'] = plot_to_base64()



# Convert 'Date of Sale' to datetime format
    merged_data['Date of Sale'] = pd.to_datetime(merged_data['Date of Sale'], format='%d-%m-%Y')



    # Calculate daily refill frequency and total sales
    daily_data = filtered_data.groupby('Date of Sale').agg(
        Refill_Frequency=('Sales ID', 'count'),  # Count of sales transactions
        Total_Sales=('Price', 'sum')            # Total sales amount
    ).reset_index()

    # Plotting the graph
    plt.figure(figsize=(14, 7))

    # Plot refill frequency
    plt.bar(daily_data['Date of Sale'], daily_data['Refill_Frequency'], color='blue', alpha=0.6, label='Refill Frequency')

    # Plot total sales on the secondary y-axis
    plt.twinx()  # Create secondary y-axis
    plt.plot(daily_data['Date of Sale'], daily_data['Total_Sales'], color='green', marker='o', label='Total Sales', linewidth=2)

    # Titles and labels
    plt.title(f'Refill Frequency vs Sales Over Time for Product: {selected_product}', fontsize=16)
    plt.xlabel('Date of Sale', fontsize=12)
    plt.ylabel('Refill Frequency (Bars)', fontsize=12, color='blue')
    plt.gca().yaxis.label.set_color('blue')

    # Add secondary y-axis label
    plt.ylabel('Total Sales (Line)', fontsize=12, color='green')
    plt.gca().tick_params(axis='y', colors='green')

    plt.legend(loc='upper left')
    plots['refillfre_sales'] = plot_to_base64()


    heatmap_data = filtered_data.groupby('Price').agg(
        Sales_Volume=('Sales ID', 'count'),
        Total_Revenue=('Price', 'sum')
    ).reset_index()
    heatmap_pivot = heatmap_data.pivot_table(
        index='Price', 
        values=['Sales_Volume', 'Total_Revenue']
    )
    plt.figure(figsize=(12, 8))
    sns.heatmap(heatmap_pivot, annot=True, fmt='.1f', cmap='YlGnBu', cbar_kws={'label': 'Intensity'})
    plt.title(f'Optimal Pricing Heatmap for {selected_product}', fontsize=16)
    plt.xlabel('Metric (Sales Volume and Revenue)', fontsize=12)
    plt.ylabel('Price', fontsize=12)
    plots['heatmap'] = plot_to_base64()



    
   



    

    return plots

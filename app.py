import streamlit as st
import pandas as pd
import requests
from datetime import datetime

def query_db(sql, params=[]):
    url = st.secrets["TURSO_DB_URL"]
    token = st.secrets["TURSO_AUTH_TOKEN"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    data = {"statements": [sql] if not params else [{"sql": sql, "params": params}]}
    try:
        response = requests.post(url + "/v1/execute", json=data, headers=headers)
        return response.json()
    except:
        return None

def init_db():
    query_db("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, price REAL, stock INTEGER)")
    query_db("CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER, quantity INTEGER, total REAL, date TEXT)")

def add_product(name, price, stock):
    query_db("INSERT INTO products (name, price, stock) VALUES (?, ?, ?)", [name, price, stock])

def delete_product(pid):
    query_db("DELETE FROM products WHERE id = ?", [pid])
    query_db("DELETE FROM sales WHERE product_id = ?", [pid])

def record_sale(pid, qty, total):
    query_db("UPDATE products SET stock = stock - ? WHERE id = ?", [qty, pid])
    query_db("INSERT INTO sales (product_id, quantity, total, date) VALUES (?, ?, ?, ?)", [pid, qty, total, datetime.now().strftime("%Y-%m-%d %H:%M")])

def get_products():
    result = query_db("SELECT * FROM products")
    if result and "results" in result:
        rows = result["results"][0].get("rows", [])
        return pd.DataFrame(rows, columns=["id", "name", "price", "stock"])
    return pd.DataFrame()

def get_sales():
    result = query_db("SELECT * FROM sales ORDER BY date DESC")
    if result and "results" in result:
        rows = result["results"][0].get("rows", [])
        return pd.DataFrame(rows, columns=["id", "product_id", "quantity", "total", "date"])
    return pd.DataFrame()

st.set_page_config(page_title="Merchant System", layout="wide")
init_db()

st.title("Sales Management System")
menu = ["Dashboard", "Products", "Sales", "Reports", "Add Product"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Dashboard":
    st.header("Dashboard")
    products_df = get_products()
    sales_df = get_sales()
    col1, col2 = st.columns(2)
    col1.metric("Products", len(products_df))
    col2.metric("Sales", len(sales_df))

elif choice == "Products":
    st.header("Products")
    df = get_products()
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("No products yet")

elif choice == "Sales":
    st.header("Record Sale")
    df = get_products()
    if not df.empty:
        product = st.selectbox("Product", df["name"].tolist())
        pdata = df[df["name"] == product].iloc[0]
        pid = int(pdata["id"])
        price = float(pdata["price"])
        stock = int(pdata["stock"])
        st.info(f"Price: {price} | Stock: {stock}")
        qty = st.number_input("Quantity", min_value=1, max_value=stock, value=1)
        total = price * qty
        st.success(f"Total: {total}")
        if st.button("Confirm Sale"):
            record_sale(pid, qty, total)
            st.success("Done!")
            st.rerun()

elif choice == "Reports":
    st.header("Reports")
    df = get_sales()
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        st.metric("Total Revenue", df["total"].sum())

elif choice == "Add Product":
    st.header("Add Product")
    name = st.text_input("Name")
    price = st.number_input("Price", min_value=0.0)
    stock = st.number_input("Stock", min_value=1)
    if st.button("Add"):        if name:
            add_product(name, price, stock)
            st.success("Added!")
            st.rerun()

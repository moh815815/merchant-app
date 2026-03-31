
import streamlit as st
import pandas as pd
from libsql_client import create_client
from datetime import datetime

def get_client():
    url = st.secrets["TURSO_DB_URL"]
    token = st.secrets["TURSO_AUTH_TOKEN"]
    return create_client(url=url, auth_token=token)

def init_db():
    try:
        client = get_client()
        client.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, price REAL, stock INTEGER)")
        client.execute("CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY, product_id INTEGER, quantity INTEGER, date TEXT)")
        return True
    except:
        return False

def add_product(name, price, stock):
    client = get_client()
    client.execute("INSERT INTO products (name, price, stock) VALUES (?, ?, ?)", [name, price, stock])

def get_products():
    client = get_client()
    result = client.execute("SELECT * FROM products")
    return pd.DataFrame(result.rows, columns=[desc[0] for desc in result.columns])

st.set_page_config(page_title="Merchant System", layout="wide")
st.title("Sales Management System")

if init_db():
    st.success("Connected to database!")
    
    name = st.text_input("Product Name")
    price = st.number_input("Price", min_value=0.0)
    stock = st.number_input("Stock", min_value=1)
    
    if st.button("Add Product"):
        add_product(name, price, stock)
        st.success("Added!")
    
    st.write("### Products")
    st.dataframe(get_products())
else:
    st.error("Database connection failed - check Secrets")

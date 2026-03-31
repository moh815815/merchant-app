
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

def add_product(name, price, stock):
    query_db("INSERT INTO products (name, price, stock) VALUES (?, ?, ?)", [name, price, stock])

def get_products():
    result = query_db("SELECT * FROM products")
    if result and "results" in result:
        rows = result["results"][0].get("rows", [])
        return pd.DataFrame(rows, columns=["id", "name", "price", "stock"])
    return pd.DataFrame()

st.set_page_config(page_title="Merchant System", layout="wide")
init_db()

st.title("Sales Management System")

# Initialize session state
if 'add_clicked' not in st.session_state:
    st.session_state.add_clicked = False

# Sidebar for adding products
with st.sidebar:
    st.header("Add New Product")
    name = st.text_input("Product Name", key="name_input")
    price = st.number_input("Price", min_value=0.0, key="price_input")
    stock = st.number_input("Stock", min_value=1, key="stock_input")
    
    if st.button("Add Product"):
        if name:
            add_product(name, price, stock)
            st.success("Added!")
            # Clear inputs
            st.session_state.name_input = ""
            st.session_state.price_input = 0.0
            st.session_state.stock_input = 1
        else:
            st.error("Enter product name!")

st.success("Connected to database!")

# Display products
st.header("Products")
df = get_products()
if not df.empty:
    st.dataframe(df, use_container_width=True)
    st.success(f"Total: {len(df)} products")
else:
    st.info("No products yet - add one from the sidebar!")

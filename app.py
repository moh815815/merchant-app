
import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# الاتصال بـ Turso عبر HTTP
def query_db(sql, params=[]):
    url = st.secrets["TURSO_DB_URL"]
    token = st.secrets["TURSO_AUTH_TOKEN"]
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "statements": [sql] if not params else [{"sql": sql, "params": params}]
    }
    
    try:
        response = requests.post(url + "/v1/execute", json=data, headers=headers)
        return response.json()
    except:
        return None

def init_db():
    query_db("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, price REAL, stock INTEGER)")
    query_db("CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER, quantity INTEGER, date TEXT)")
    return True

def add_product(name, price, stock):
    query_db("INSERT INTO products (name, price, stock) VALUES (?, ?, ?)", [name, price, stock])

def get_products():
    result = query_db("SELECT * FROM products")
    if result and "results" in result:
        rows = result["results"][0].get("rows", [])
        return pd.DataFrame(rows, columns=["id", "name", "price", "stock"])
    return pd.DataFrame()

st.set_page_config(page_title="Merchant System", layout="wide")
st.title("Sales Management System")

if init_db():
    st.success("Connected!")
    
    name = st.text_input("Product Name")
    price = st.number_input("Price", min_value=0.0)
    stock = st.number_input("Stock", min_value=1)
    
    if st.button("Add Product"):
        add_product(name, price, stock)
        st.success("Added!")
        st.rerun()
    
    st.write("### Products")
    st.dataframe(get_products())

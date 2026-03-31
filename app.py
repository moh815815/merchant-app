import streamlit as st
import pandas as pd
import requests

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
st.success("Connected!")

# إضافة منتج من غير form
st.header("Add New Product")
col1, col2, col3 = st.columns(3)
with col1:
    name = st.text_input("Product Name")
with col2:
    price = st.number_input("Price", min_value=0.0)
with col3:
    stock = st.number_input("Stock", min_value=1)

if st.button("Add Product", type="primary"):
    if name:
        add_product(name, price, stock)
        st.success("Product added successfully!")
        st.balloons()
    else:
        st.error("Please enter product name!")

st.markdown("---")
st.header("Products")
df = get_products()
if not df.empty:
    st.dataframe(df, use_container_width=True)
    st.success(f"Total products: {len(df)}")
else:
    st.info("No products yet")

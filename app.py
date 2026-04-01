import streamlit as st
import pandas as pd
import requests
import base64
from PIL import Image
import io

def query_db(sql, params=[]):
    url = st.secrets["TURSO_DB_URL"]
    token = st.secrets["TURSO_AUTH_TOKEN"]
    headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
    data = {"statements": [sql] if not params else [{"sql": sql, "params": params}]}
    try:
        response = requests.post(url + "/v1/execute", json=data, headers=headers)
        return response.json()
    except:
        return None

def init_db():
    query_db("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, price REAL, stock INTEGER, image_base64 TEXT)")

def process_image(file):
    try:
        img = Image.open(file)
        if img.mode in ('RGBA', 'P', 'LA'):
            img = img.convert('RGB')
        img.thumbnail((800, 800))
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=75, optimize=True)
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        return img_base64
    except:
        return None

def add_product(name, price, stock, img_data=None):
    query_db("INSERT INTO products (name, price, stock, image_base64) VALUES (?, ?, ?, ?)", [name, price, stock, img_data])

def get_products():
    result = query_db("SELECT * FROM products")
    if result and "results" in result:
        rows = result["results"][0].get("rows", [])
        df = pd.DataFrame(rows, columns=["id", "name", "price", "stock", "image_base64"])
        return df
    return pd.DataFrame()

st.set_page_config(page_title="Merchant System", layout="wide")
init_db()

st.title("Sales Management System")
st.success("Connected!")

st.header("Add New Product")
name = st.text_input("Product Name")
col1, col2 = st.columns(2)

with col1:
    price = st.number_input("Price", min_value=0.0)
    stock = st.number_input("Stock", min_value=1)

with col2:
    uploaded_file = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png", "webp"])
    if uploaded_file:
        st.image(uploaded_file, width=200)

if st.button("Add Product", type="primary"):
    if name:
        img_base64 = None
        if uploaded_file:
            with st.spinner("Processing..."):
                img_base64 = process_image(uploaded_file)
                if img_base64:
                    st.success("Image OK!")
        add_product(name, price, stock, img_base64)
        st.success("Added!")
        st.rerun()
    else:
        st.error("Enter name!")

st.header("Products")
df = get_products()
if not df.empty:
    for index, row in df.iterrows():
        col1, col2 = st.columns([1, 3])
        with col1:
            if row['image_base64']:
                try:
                    img_bytes = base64.b64decode(row['image_base64'])
                    st.image(img_bytes, width=150)
                except:
                    st.write("No Image")
            else:
                st.write("No Image")
        with col2:
            st.subheader(row['name'])
            st.write("Price: " + str(row['price']) + " | Stock: " + str(row['stock']))
        st.markdown("---")
else:
    st.info("No products yet")

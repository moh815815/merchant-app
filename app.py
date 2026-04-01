import streamlit as st
import pandas as pd
import requests
import cloudinary
import cloudinary.uploader

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
    query_db("""CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        name TEXT, 
        price REAL, 
        stock INTEGER,
        image_url TEXT
    )""")

def upload_image(file):
    try:
        cloudinary.config(
            cloud_name=st.secrets["CLOUDINARY_CLOUD_NAME"],
            api_key=st.secrets["CLOUDINARY_API_KEY"],
            api_secret=st.secrets["CLOUDINARY_API_SECRET"]
        )
        result = cloudinary.uploader.upload(file)
        return result['secure_url']
    except Exception as e:
        st.error(f"Upload failed: {e}")
        return None

def add_product(name, price, stock, image_url=""):
    query_db("INSERT INTO products (name, price, stock, image_url) VALUES (?, ?, ?, ?)", 
             [name, price, stock, image_url])

def delete_product(pid):
    query_db("DELETE FROM products WHERE id = ?", [pid])

def get_products():
    result = query_db("SELECT * FROM products")
    if result and "results" in result:
        rows = result["results"][0].get("rows", [])        return pd.DataFrame(rows, columns=["id", "name", "price", "stock", "image_url"])
    return pd.DataFrame()

st.set_page_config(page_title="Merchant System", layout="wide")
init_db()

st.title("🛒 Sales Management System")
st.success("Connected!")
st.markdown("---")

st.header("➕ Add New Product")

name = st.text_input("Product Name")
col1, col2 = st.columns(2)

with col1:
    price = st.number_input("Price", min_value=0.0)
    stock = st.number_input("Stock", min_value=1)

with col2:
    uploaded_file = st.file_uploader("📸 Upload Image", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        st.image(uploaded_file, width=200)

if st.button("Add Product", type="primary"):
    if name:
        image_url = ""
        if uploaded_file:
            with st.spinner("Uploading image..."):
                image_url = upload_image(uploaded_file)
                if image_url:
                    st.success("✅ Image uploaded!")
        
        add_product(name, price, stock, image_url)
        st.success("✅ Product added!")
        st.balloons()
        st.rerun()
    else:
        st.error("Enter product name!")

st.markdown("---")
st.header("📦 Products")
df = get_products()

if not df.empty:
    for _, row in df.iterrows():
        col1, col2, col3 = st.columns([1, 3, 1])
        with col1:
            if row['image_url']:
                st.image(row['image_url'], width=150)            else:
                st.write("No Image")
        with col2:
            st.subheader(row['name'])
            st.write(f"💰 {row['price']} EGP | 📦 {row['stock']}")
        with col3:
            if st.button("🗑️", key=row['id']):
                delete_product(row['id'])
                st.rerun()
        st.markdown("---")
else:
    st.info("No products yet")

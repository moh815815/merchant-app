
import streamlit as st
import pandas as pd
import requests
import base64

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

def upload_to_imgur(image_file):
    try:
        img_data = image_file.read()
        b64 = base64.b64encode(img_data).decode()
        
        headers = {"Authorization": "Client-ID 8c0c1a0c8c0c1a0"}
        data = {"image": b64}
        
        response = requests.post("https://api.imgur.com/3/image", data=data, headers=headers)
        result = response.json()
        
        if result.get("success"):
            return result["data"]["link"]
        return None
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

def add_product(name, price, stock, image_url=""):
    query_db("INSERT INTO products (name, price, stock, image_url) VALUES (?, ?, ?, ?)", 
             [name, price, stock, image_url])

def delete_product(pid):
    query_db("DELETE FROM products WHERE id = ?", [pid])

def get_products():    result = query_db("SELECT * FROM products")
    if result and "results" in result:
        rows = result["results"][0].get("rows", [])
        return pd.DataFrame(rows, columns=["id", "name", "price", "stock", "image_url"])
    return pd.DataFrame()

st.set_page_config(page_title="Merchant System", layout="wide")
init_db()

st.title("🛒 Sales Management System")
st.success("Connected!")

st.markdown("---")

# إضافة منتج
st.header("➕ Add New Product")

name = st.text_input("Product Name")
col1, col2, col3 = st.columns(3)
with col1:
    price = st.number_input("Price", min_value=0.0)
with col2:
    stock = st.number_input("Stock", min_value=1)
with col3:
    uploaded_file = st.file_uploader("📸 Upload Image", type=["jpg", "jpeg", "png"])

if uploaded_file:
    st.image(uploaded_file, width=200, caption="Preview")

if st.button("Add Product", type="primary"):
    if name:
        image_url = ""
        if uploaded_file:
            with st.spinner("Uploading image..."):
                image_url = upload_to_imgur(uploaded_file)
                if image_url:
                    st.success("Image uploaded!")
                else:
                    st.warning("Image upload failed, continuing without image")
        
        add_product(name, price, stock, image_url)
        st.success("✅ Product added successfully!")
        st.balloons()
        st.rerun()
    else:
        st.error("Please enter product name!")

st.markdown("---")

# عرض المنتجاتst.header("📦 Products")
df = get_products()

if not df.empty:
    st.success(f"Total: {len(df)} products")
    
    for index, row in df.iterrows():
        with st.container():
            col1, col2, col3 = st.columns([1, 3, 1])
            
            with col1:
                if row['image_url']:
                    st.image(row['image_url'], width=150)
                else:
                    st.write("🖼️ No Image")
            
            with col2:
                st.subheader(row['name'])
                st.write(f"💰 Price: {row['price']} EGP")
                st.write(f"📦 Stock: {row['stock']} units")
            
            with col3:
                st.write("")
                st.write("")
                if st.button("🗑️ Delete", key=f"del_{row['id']}"):
                    delete_product(row['id'])
                    st.success("Deleted!")
                    st.rerun()
            
            st.markdown("---")
else:
    st.info("No products yet - add your first product above!")

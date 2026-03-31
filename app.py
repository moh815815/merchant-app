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

def init_db():
    query_db("""CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        name TEXT, 
        price REAL, 
        stock INTEGER,
        image TEXT
    )""")

def add_product(name, price, stock, image_data=None):
    query_db("INSERT INTO products (name, price, stock, image) VALUES (?, ?, ?, ?)", 
             [name, price, stock, image_data])

def get_products():
    result = query_db("SELECT * FROM products")
    if result and "results" in result:
        rows = result["results"][0].get("rows", [])
        return pd.DataFrame(rows, columns=["id", "name", "price", "stock", "image"])
    return pd.DataFrame()

def encode_image(uploaded_file):
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        return base64.b64encode(bytes_data).decode()
    return None

st.set_page_config(page_title="Merchant System", layout="wide")
init_db()

st.title("🛒 Sales Management System")
st.success("Connected!")

st.markdown("---")
# إضافة منتج مع صورة
st.header("➕ Add New Product")

col1, col2 = st.columns([1, 1])

with col1:
    name = st.text_input("Product Name")
    price = st.number_input("Price", min_value=0.0)
    stock = st.number_input("Stock", min_value=1)

with col2:
    st.write("### Product Image")
    uploaded_file = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        st.image(uploaded_file, width=200, caption="Preview")

if st.button("Add Product", type="primary"):
    if name:
        image_data = encode_image(uploaded_file)
        add_product(name, price, stock, image_data)
        st.success("✅ Product added successfully!")
        st.balloons()
    else:
        st.error("Please enter product name!")

st.markdown("---")

# عرض المنتجات مع الصور
st.header("📦 Products")
df = get_products()

if not df.empty:
    st.success(f"Total: {len(df)} products")
    
    # عرض المنتجات في بطاقات
    for index, row in df.iterrows():
        with st.container():
            col1, col2, col3 = st.columns([1, 3, 1])
            
            with col1:
                if row['image']:
                    img_data = base64.b64decode(row['image'])
                    st.image(img_data, width=150)
                else:
                    st.write("No Image")
            
            with col2:
                st.subheader(row['name'])
                st.write(f"💰 Price: {row['price']} EGP")
                st.write(f"📦 Stock: {row['stock']} units")            
            with col3:
                st.write("")
                st.write("")
                if st.button("🗑️ Delete", key=f"del_{row['id']}"):
                    query_db("DELETE FROM products WHERE id = ?", [row['id']])
                    st.success("Deleted!")
                    st.rerun()
            
            st.markdown("---")
else:
    st.info("No products yet - add your first product above!")

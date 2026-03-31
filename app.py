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
        client.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, price REAL, stock INTEGER)")
        client.execute("CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER, quantity INTEGER, date TEXT)")
        return True
    except Exception as e:
        st.error("خطأ في قاعدة البيانات")
        return False

def add_product(name, price, stock):
    client = get_client()
    client.execute("INSERT INTO products (name, price, stock) VALUES (?, ?, ?)", [name, price, stock])

def record_sale(product_id, quantity):
    client = get_client()
    result = client.execute("SELECT stock FROM products WHERE id = ?", [product_id])
    current_stock = result.rows[0][0]
    
    if current_stock >= quantity:
        new_stock = current_stock - quantity
        client.execute("UPDATE products SET stock = ? WHERE id = ?", [new_stock, product_id])
        client.execute("INSERT INTO sales (product_id, quantity, date) VALUES (?, ?, ?)", [product_id, quantity, datetime.now().strftime("%Y-%m-%d %H:%M")])
        return True
    return False

def get_products():
    client = get_client()
    result = client.execute("SELECT * FROM products")
    return pd.DataFrame(result.rows, columns=[desc[0] for desc in result.columns])

def get_sales():
    client = get_client()
    result = client.execute("SELECT * FROM sales")
    return pd.DataFrame(result.rows, columns=[desc[0] for desc in result.columns])

st.set_page_config(page_title="نظام التاجر", layout="wide")
st.title("نظام إدارة المبيعات")

if init_db():
    menu = ["لوحة التحكم", "اضافة منتج", "تسجيل بيع", "البيانات"]
    choice = st.sidebar.selectbox("القائمة", menu)
    
    if choice == "اضافة منتج":
        name = st.text_input("اسم المنتج")
        price = st.number_input("السعر", min_value=0.0)
        stock = st.number_input("الكمية", min_value=1)
        if st.button("اضافة"):
            add_product(name, price, stock)
            st.success("تمت الاضافة")
    
    elif choice == "تسجيل بيع":
        df = get_products()
        if not df.empty:
            product = st.selectbox("اختر المنتج", df["name"].tolist())
            product_id = int(df[df["name"] == product]["id"].values[0])
            qty = st.number_input("الكمية", min_value=1)
            if st.button("تأكيد البيع"):
                if record_sale(product_id, qty):
                    st.success("تم البيع")
                else:
                    st.error("المخزون غير كاف")
        else:
            st.warning("اضف منتجات اولا")
    
    elif choice == "لوحة التحكم":
        sales = get_sales()
        st.metric("اجمالي المبيعات", len(sales))
        st.dataframe(sales)
    
    elif choice == "البيانات":
        st.write("المنتجات")
        st.dataframe(get_products())
        st.write("المبيعات")
        st.dataframe(get_sales())

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

st.set_page_config(page_title="نظام المبيعات", layout="wide")
init_db()

st.title("نظام إدارة المبيعات")
menu = ["الرئيسية", "المنتجات", "بيع", "تقارير", "اضافة منتج"]
choice = st.sidebar.selectbox("القائمة", menu)

if choice == "الرئيسية":
    st.header("لوحة التحكم")
    products_df = get_products()
    sales_df = get_sales()
    col1, col2 = st.columns(2)
    col1.metric("المنتجات", len(products_df))
    col2.metric("المبيعات", len(sales_df))

elif choice == "المنتجات":
    st.header("المنتجات")
    df = get_products()
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("لا توجد منتجات")

elif choice == "بيع":
    st.header("تسجيل بيع")
    df = get_products()
    if not df.empty:
        product = st.selectbox("المنتج", df["name"].tolist())
        pdata = df[df["name"] == product].iloc[0]
        pid = int(pdata["id"])
        price = float(pdata["price"])
        stock = int(pdata["stock"])
        st.info(f"السعر: {price} | المخزون: {stock}")
        qty = st.number_input("الكمية", min_value=1, max_value=stock, value=1)
        total = price * qty
        st.success(f"الإجمالي: {total}")
        if st.button("تأكيد"):
            record_sale(pid, qty, total)
            st.success("تم!")
            st.rerun()

elif choice == "تقارير":
    st.header("التقارير")
    df = get_sales()
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        st.metric("إجمالي الإيرادات", df["total"].sum())

elif choice == "اضافة منتج":
    st.header("إضافة منتج")
    name = st.text_input("الاسم")
    price = st.number_input("السعر", min_value=0.0)
    stock = st.number_input("الكمية", min_value=1)
    if st.button("إضافة"):        if name:
            add_product(name, price, stock)
            st.success("تم!")
            st.rerun()

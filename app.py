
import streamlit as st
import pandas as pd
import requests
from datetime import datetime

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
    except Exception as e:
        return None

def init_db():
    query_db("""CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        name TEXT, 
        price REAL, 
        stock INTEGER
    )""")
    query_db("""CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        product_id INTEGER, 
        quantity INTEGER, 
        total REAL,
        date TEXT
    )""")

def add_product(name, price, stock):
    query_db("INSERT INTO products (name, price, stock) VALUES (?, ?, ?)", [name, price, stock])

def delete_product(product_id):
    query_db("DELETE FROM products WHERE id = ?", [product_id])
    query_db("DELETE FROM sales WHERE product_id = ?", [product_id])

def record_sale(product_id, quantity, total):
    query_db("UPDATE products SET stock = stock - ? WHERE id = ?", [quantity, product_id])
    query_db("INSERT INTO sales (product_id, quantity, total, date) VALUES (?, ?, ?, ?)", 
             [product_id, quantity, total, datetime.now().strftime("%Y-%m-%d %H:%M")])
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

# الواجهة الرئيسية
st.set_page_config(page_title="نظام إدارة المبيعات", layout="wide", initial_sidebar_state="expanded")

# التهيئة
init_db()

# العنوان
st.title("🛒 نظام إدارة المبيعات المتكامل")
st.markdown("---")

# القائمة الجانبية
menu = ["📊 لوحة التحكم", "📦 المنتجات", "💰 تسجيل بيع", "📈 التقارير", "➕ إضافة منتج"]
choice = st.sidebar.selectbox("القائمة الرئيسية", menu)

# لوحة التحكم
if choice == "📊 لوحة التحكم":
    st.header("📊 لوحة التحكم الرئيسية")
    
    products_df = get_products()
    sales_df = get_sales()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("إجمالي المنتجات", len(products_df))
    with col2:
        st.metric("إجمالي المبيعات", len(sales_df))
    with col3:
        total_revenue = sales_df["total"].sum() if not sales_df.empty else 0
        st.metric("إجمالي الإيرادات", f"{total_revenue:.2f} جنيه")
    with col4:
        total_stock = products_df["stock"].sum() if not products_df.empty else 0
        st.metric("إجمالي المخزون", total_stock)
    
    st.markdown("---")    st.subheader("📈 آخر 5 مبيعات")
    if not sales_df.empty:
        st.dataframe(sales_df.head(5), use_container_width=True)
    else:
        st.info("لا توجد مبيعات بعد")

# المنتجات
elif choice == "📦 المنتجات":
    st.header("📦 إدارة المنتجات")
    
    products_df = get_products()
    
    if not products_df.empty:
        st.dataframe(products_df, use_container_width=True)
        
        st.markdown("---")
        st.subheader("🗑️ حذف منتج")
        
        product_to_delete = st.selectbox(
            "اختر المنتج للحذف",
            products_df["name"].tolist(),
            key="delete_product"
        )
        
        if st.button("حذف المنتج"):
            product_id = int(products_df[products_df["name"] == product_to_delete]["id"].values[0])
            delete_product(product_id)
            st.success("✅ تم حذف المنتج بنجاح!")
            st.rerun()
    else:
        st.warning("لا توجد منتجات - أضف منتجات أولاً")

# تسجيل بيع
elif choice == "💰 تسجيل بيع":
    st.header("💰 تسجيل عملية بيع جديدة")
    
    products_df = get_products()
    
    if not products_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            product = st.selectbox(
                "اختر المنتج",
                products_df["name"].tolist()
            )
        
        product_data = products_df[products_df["name"] == product].iloc[0]
        product_id = int(product_data["id"])
        price = float(product_data["price"])        stock = int(product_data["stock"])
        
        with col2:
            st.info(f"السعر: {price} جنيه")
            st.info(f"المخزون المتاح: {stock}")
        
        quantity = st.number_input("الكمية", min_value=1, max_value=stock, value=1)
        total = price * quantity
        
        st.success(f"💵 الإجمالي: {total:.2f} جنيه")
        
        if st.button("✅ تأكيد البيع", type="primary"):
            record_sale(product_id, quantity, total)
            st.success("✅ تم تسجيل البيع بنجاح!")
            st.rerun()
    else:
        st.warning("لا توجد منتجات - أضف منتجات أولاً")

# التقارير
elif choice == "📈 التقارير":
    st.header("📈 تقارير المبيعات")
    
    sales_df = get_sales()
    products_df = get_products()
    
    if not sales_df.empty:
        # الإحصائيات
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("إجمالي المبيعات", len(sales_df))
        with col2:
            total_revenue = sales_df["total"].sum()
            st.metric("إجمالي الإيرادات", f"{total_revenue:.2f} جنيه")
        with col3:
            avg_sale = sales_df["total"].mean()
            st.metric("متوسط البيع", f"{avg_sale:.2f} جنيه")
        
        st.markdown("---")
        
        # جدول المبيعات
        st.subheader("📋 جميع المبيعات")
        st.dataframe(sales_df, use_container_width=True)
        
        # مبيعات كل منتج
        st.markdown("---")
        st.subheader("📊 مبيعات كل منتج")
        
        if not products_df.empty:
            product_sales = []            for _, row in products_df.iterrows():
                product_id = row["id"]
                product_name = row["name"]
                sales_count = len(sales_df[sales_df["product_id"] == product_id])
                total_qty = sales_df[sales_df["product_id"] == product_id]["quantity"].sum() if sales_count > 0 else 0
                total_rev = sales_df[sales_df["product_id"] == product_id]["total"].sum() if sales_count > 0 else 0
                
                product_sales.append({
                    "المنتج": product_name,
                    "عدد مرات البيع": sales_count,
                    "الكمية المباعة": total_qty,
                    "الإيرادات": f"{total_rev:.2f}"
                })
            
            sales_report_df = pd.DataFrame(product_sales)
            st.dataframe(sales_report_df, use_container_width=True)
    else:
        st.info("لا توجد مبيعات بعد")

# إضافة منتج
elif choice == "➕ إضافة منتج":
    st.header("➕ إضافة منتج جديد")
    
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input("اسم المنتج *")
        price = st.number_input("السعر (جنيه)", min_value=0.0, step=0.01)
    
    with col2:
        stock = st.number_input("الكمية في المخزون", min_value=1, step=1)
    
    if st.button("إضافة المنتج", type="primary"):
        if name:
            add_product(name, price, stock)
            st.success("✅ تم إضافة المنتج بنجاح!")
            st.rerun()
        else:
            st.error("❌ يرجى إدخال اسم المنتج")

# التذييل
st.markdown("---")
st.markdown("<div style='text-align: center; color: gray;'>نظام إدارة المبيعات المتكامل © 2026</div>", unsafe_allow_html=True)

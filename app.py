import streamlit as st
import pandas as pd
import requests
import base64
from PIL import Image
import io

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
        image_base64 TEXT
    )""")

def process_image(file):
    """تحويل أي صورة لـ JPEG صغير"""
    try:
        # فتح الصورة بأي صيغة
        img = Image.open(file)
        
        # تحويل لـ RGB (عشان نجنب مشاكل RGBA)
        if img.mode in ('RGBA', 'P', 'LA'):
            img = img.convert('RGB')
        
        # تصغير الحجم
        img.thumbnail((800, 800))
        
        # حفظ كـ JPEG بجودة متوسطة
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=75, optimize=True)
        
        # تحويل لـ base64
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return img_base64
    except Exception as e:
        st.error(f"خطأ في الصورة: {e}")        return None

def add_product(name, price, stock, img_data=None):
    query_db("INSERT INTO products (name, price, stock, image_base64) VALUES (?, ?, ?, ?)", 
             [name, price, stock, img_data])

def get_products():
    result = query_db("SELECT * FROM products")
    if result and "results" in result:
        rows = result["results"][0].get("rows", [])
        return pd.DataFrame(rows, columns=["id", "name", "price", "stock", "image_base64"])
    return pd.DataFrame()

st.set_page_config(page_title="Merchant System", layout="wide")
init_db()

st.title("🛒 نظام إدارة المنتجات")
st.success("✅ متصل!")

st.header("➕ إضافة منتج جديد")

name = st.text_input("اسم المنتج")
col1, col2 = st.columns(2)

with col1:
    price = st.number_input("السعر", min_value=0.0)
    stock = st.number_input("الكمية", min_value=1)

with col2:
    # قبول أي صيغة صورة
    uploaded_file = st.file_uploader(
        "📸 رفع صورة", 
        type=["jpg", "jpeg", "png", "webp", "gif", "bmp", "heic", "heif", "tiff"],
        help="يقبل أي صيغة: JPG, PNG, WEBP, GIF, HEIC..."
    )
    
    if uploaded_file:
        try:
            st.image(uploaded_file, width=200, caption="معاينة")
        except:
            st.write("📷 صورة محملة")

if st.button("إضافة منتج", type="primary"):
    if name:
        img_base64 = None
        if uploaded_file:
            with st.spinner("⏳ جاري معالجة الصورة..."):
                img_base64 = process_image(uploaded_file)
                if img_base64:
                    st.success("✅ تم معالجة الصورة!")                else:
                    st.warning("⚠️ لم يتم معالجة الصورة")
        
        add_product(name, price, stock, img_base64)
        st.success("✅ تم إضافة المنتج بنجاح!")
        st.balloons()
        st.rerun()
    else:
        st.error("❌ اكتب اسم المنتج!")

st.header("📦 المنتجات")
df = get_products()

if not df.empty:
    st.success(f"إجمالي المنتجات: {len(df)}")
    for _, row in df.iterrows():
        with st.container():
            col1, col2 = st.columns([1, 3])
            with col1:
                if row['image_base64']:
                    try:
                        img_bytes = base64.b64decode(row['image_base64'])
                        st.image(img_bytes, width=150)
                    except:
                        st.write("🖼️ بدون صورة")
                else:
                    st.write("🖼️ بدون صورة")
            with col2:
                st.subheader(row['name'])
                st.write(f"💰 السعر: {row['price']} جنيه")
                st.write(f"📦 المخزون: {row['stock']}")
            st.markdown("---")
else:
    st.info("لا توجد منتجات بعد - أضف منتجك الأول!")

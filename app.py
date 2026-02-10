import streamlit as st
import pandas as pd
import snowflake.connector

# --------------------------------------------------
# Page config
# --------------------------------------------------
st.set_page_config(page_title="Enterprise Sales Dashboard", layout="wide")
st.title("📊 Enterprise Sales Dashboard")

# --------------------------------------------------
# Snowflake connection (Streamlit Cloud / Local)
# --------------------------------------------------
@st.cache_resource
def get_connection():
    return snowflake.connector.connect(
        user=st.secrets["snowflake"]["user"],
        password=st.secrets["snowflake"]["password"],
        account=st.secrets["snowflake"]["account"],
        warehouse=st.secrets["snowflake"]["warehouse"],
        database=st.secrets["snowflake"]["database"],
        schema=st.secrets["snowflake"]["schema"],
        role=st.secrets["snowflake"]["role"]
    )

conn = get_connection()

# ==================================================
# GLOBAL YEAR DROPDOWN
# ==================================================
years_df = pd.read_sql("""
    SELECT DISTINCT YEAR(Order_Date) AS YEAR
    FROM GOLD.FACT_ORDERS
    ORDER BY YEAR
""", conn)

years = years_df["YEAR"].tolist()
selected_year = st.selectbox("📅 Select Year", years)

# ==================================================
# KPI ROW (EXECUTIVE SUMMARY)
# ==================================================
kpi_df = pd.read_sql(f"""
    SELECT
        SUM(Revenue) AS TOTAL_REVENUE,
        AVG(Revenue) AS AVG_REVENUE,
        COUNT(Order_ID) AS TOTAL_ORDERS
    FROM GOLD.FACT_ORDERS
    WHERE YEAR(Order_Date) = {selected_year}
""", conn)

k1, k2, k3 = st.columns(3)

k1.metric("💰 Total Revenue", f"{kpi_df.iloc[0]['TOTAL_REVENUE']:,.2f}")
k2.metric("📊 Average Revenue", f"{kpi_df.iloc[0]['AVG_REVENUE']:,.2f}")
k3.metric("🧾 Total Orders", int(kpi_df.iloc[0]['TOTAL_ORDERS']))

st.divider()

# ==================================================
# Revenue by Region
# ==================================================
df_region = pd.read_sql(f"""
    SELECT Region, SUM(Revenue) AS TOTAL_REVENUE
    FROM GOLD.FACT_ORDERS
    WHERE YEAR(Order_Date) = {selected_year}
    GROUP BY Region
    ORDER BY TOTAL_REVENUE DESC
""", conn)

st.markdown("## 🔵 Revenue by Region")
st.bar_chart(df_region.set_index("REGION"))

st.divider()

# ==================================================
# Revenue by Category
# ==================================================
df_category = pd.read_sql(f"""
    SELECT Category, SUM(Revenue) AS TOTAL_REVENUE
    FROM GOLD.FACT_ORDERS
    WHERE YEAR(Order_Date) = {selected_year}
    GROUP BY Category
    ORDER BY TOTAL_REVENUE DESC
""", conn)

st.markdown("## 🟢 Revenue by Category")
st.bar_chart(df_category.set_index("CATEGORY"))

st.divider()

# ==================================================
# Monthly Sales Trend
# ==================================================
df_monthly = pd.read_sql(f"""
    SELECT
        TO_CHAR(Order_Date, 'Mon') AS MONTH,
        MONTH(Order_Date) AS MONTH_NO,
        SUM(Revenue) AS MONTHLY_REVENUE
    FROM GOLD.FACT_ORDERS
    WHERE YEAR(Order_Date) = {selected_year}
    GROUP BY MONTH, MONTH_NO
    ORDER BY MONTH_NO
""", conn)

month_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

df_monthly["MONTH"] = pd.Categorical(
    df_monthly["MONTH"], categories=month_order, ordered=True
)

df_monthly = df_monthly.sort_values("MONTH").set_index("MONTH")

st.markdown("## 🟣 Monthly Sales Trend")
st.line_chart(df_monthly["MONTHLY_REVENUE"])

st.divider()

# ==================================================
# Year-over-Year Revenue Trend
# ==================================================
df_yoy = pd.read_sql("""
    SELECT
        YEAR(Order_Date) AS YEAR,
        SUM(Revenue) AS TOTAL_REVENUE
    FROM GOLD.FACT_ORDERS
    GROUP BY YEAR
    ORDER BY YEAR
""", conn)

df_yoy = df_yoy.set_index("YEAR")

st.markdown("## 📈 Year-over-Year Revenue Trend")
st.line_chart(df_yoy["TOTAL_REVENUE"])

st.divider()

# ==================================================
# Customer Revenue Analysis
# ==================================================
df_top5 = pd.read_sql(f"""
    SELECT Customer_ID, SUM(Revenue) AS TOTAL_REVENUE
    FROM GOLD.FACT_ORDERS
    WHERE YEAR(Order_Date) = {selected_year}
    GROUP BY Customer_ID
    ORDER BY TOTAL_REVENUE DESC
    LIMIT 5
""", conn)

df_bottom5 = pd.read_sql(f"""
    SELECT Customer_ID, SUM(Revenue) AS TOTAL_REVENUE
    FROM GOLD.FACT_ORDERS
    WHERE YEAR(Order_Date) = {selected_year}
    GROUP BY Customer_ID
    ORDER BY TOTAL_REVENUE ASC
    LIMIT 5
""", conn)

st.markdown("## 🧑‍🤝‍🧑 Customer Revenue Analysis")

c1, c2 = st.columns(2)

with c1:
    st.markdown("### 🟢 Top 5 Customers")
    st.bar_chart(df_top5.set_index("CUSTOMER_ID"))

with c2:
    st.markdown("### 🔴 Bottom 5 Customers")
    st.bar_chart(df_bottom5.set_index("CUSTOMER_ID"))

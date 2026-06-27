import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import plotly.express as px

st.markdown("""
<style>
h1, h2, h3 {
    color: #00ffcc;
}

div[data-testid="metric-container"] {
    background-color: #1c1f26;
    border-radius: 12px;
    padding: 15px;
    box-shadow: 0px 0px 10px #000;
}

.stButton>button {
    background-color: #00ffcc;
    color: black;
    border-radius: 8px;
    padding: 8px 15px;
    font-weight: bold;
}

.stSidebar {
    background-color: #11151c;
}
</style>
""", unsafe_allow_html=True)

st.set_page_config(
    page_title="Smart Expense Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# DATABASE SETUP
# =========================

conn = sqlite3.connect("expenses.db", check_same_thread=False)
c = conn.cursor()

def create_table():
    c.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            category TEXT,
            type TEXT,
            amount REAL,
            note TEXT
        )
    """)
    conn.commit()

create_table()

# =========================
# DATABASE FUNCTIONS
# =========================

def add_transaction(date, category, t_type, amount, note):
    c.execute("""
        INSERT INTO expenses (date, category, type, amount, note)
        VALUES (?, ?, ?, ?, ?)
    """, (date, category, t_type, amount, note))
    conn.commit()

def get_all_transactions():
    c.execute("SELECT * FROM expenses ORDER BY date DESC")
    data = c.fetchall()
    return data

def delete_transaction(t_id):
    c.execute("DELETE FROM expenses WHERE id=?", (t_id,))
    conn.commit()

def get_balance():
    c.execute("SELECT SUM(amount) FROM expenses WHERE type='Income'")
    income = c.fetchone()[0] or 0

    c.execute("SELECT SUM(amount) FROM expenses WHERE type='Expense'")
    expense = c.fetchone()[0] or 0

    return income, expense, income - expense

# =========================
# STREAMLIT UI SETUP
# =========================

st.set_page_config(page_title="Expense Tracker", layout="wide")

st.title("💰 Smart Expense Tracker")
st.write("Track your income and expenses easily with charts & database storage.")

menu = ["Dashboard", "Add Transaction", "View Transactions", "Analytics"]
choice = st.sidebar.selectbox("Menu", menu)

# =========================
# DASHBOARD (START)
# =========================

if choice == "Dashboard":
    income, expense, balance = get_balance()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Income", f"₹ {income}")
    col2.metric("Total Expense", f"₹ {expense}")
    col3.metric("Balance", f"₹ {balance}")

    st.subheader("Recent Transactions")
    data = get_all_transactions()

    df = pd.DataFrame(data, columns=[
        "ID", "Date", "Category", "Type", "Amount", "Note"
    ])

    st.dataframe(df.head(10))
    
    st.markdown("### 🔥 Quick Insights")

    if income > expense:
        st.success("You are saving money 💰")
    else:
        st.error("You are spending more than income ⚠️")

    savings_rate = (balance / income * 100) if income > 0 else 0
    st.info(f"Savings Rate: {savings_rate:.2f}%")
    
# =========================
# ADD TRANSACTION PAGE
# =========================

if choice == "Add Transaction":
    st.subheader("➕ Add New Transaction")

    col1, col2 = st.columns(2)

    with col1:
        t_type = st.selectbox("Type", ["Income", "Expense"])
        category = st.selectbox("Category", [
            "Salary", "Food", "Travel", "Shopping",
            "Bills", "Entertainment", "Medical", "Other"
        ])

    with col2:
        amount = st.number_input("Amount (₹)", min_value=0.0, format="%.2f")
        date = st.date_input("Date", datetime.today())

    note = st.text_input("Note (Optional)")

    if st.button("Add Transaction"):
        if amount > 0:
            add_transaction(
                date.strftime("%Y-%m-%d"),
                category,
                t_type,
                amount,
                note
            )
            st.success("Transaction Added Successfully ✅")
        else:
            st.error("Please enter a valid amount")

# =========================
# VIEW TRANSACTIONS PAGE
# =========================

if choice == "View Transactions":
    st.subheader("📋 All Transactions")
    
    filter_type = st.selectbox("Filter", ["All", "Income", "Expense"])

    if filter_type != "All":
        df = df[df["Type"] == filter_type]

    data = get_all_transactions()

    if len(data) == 0:
        st.info("No transactions found")
    else:
        df = pd.DataFrame(data, columns=[
            "ID", "Date", "Category", "Type", "Amount", "Note"
        ])

        st.dataframe(df, use_container_width=True)

        st.subheader("🗑️ Delete Transaction")

        delete_id = st.number_input("Enter Transaction ID to delete", min_value=1, step=1)

        if st.button("Delete"):
            delete_transaction(delete_id)
            st.warning("Transaction Deleted Successfully ⚠️")

# =========================
# ANALYTICS PAGE
# =========================

if choice == "Analytics":
    st.subheader("📊 Expense Analytics")

    data = get_all_transactions()

    if len(data) == 0:
        st.info("No data available for analytics")
    else:
        df = pd.DataFrame(data, columns=[
            "ID", "Date", "Category", "Type", "Amount", "Note"
        ])

        # =========================
        # INCOME VS EXPENSE CHART
        # =========================

        income_df = df[df["Type"] == "Income"]
        expense_df = df[df["Type"] == "Expense"]

        total_income = income_df["Amount"].sum()
        total_expense = expense_df["Amount"].sum()

        fig1 = px.bar(
            x=["Income", "Expense"],
            y=[total_income, total_expense],
            color=["Income", "Expense"],
            title="Income vs Expense"
        )
        st.plotly_chart(fig1, use_container_width=True)

        # =========================
        # CATEGORY WISE EXPENSE
        # =========================

        st.subheader("🥧 Category-wise Expense")

        category_df = expense_df.groupby("Category")["Amount"].sum().reset_index()

        fig2 = px.pie(
            category_df,
            names="Category",
            values="Amount",
            title="Expense by Category"
        )
        st.plotly_chart(fig2, use_container_width=True)

        # =========================
        # DAILY TREND
        # =========================

        st.subheader("📈 Daily Spending Trend")

        df["Date"] = pd.to_datetime(df["Date"])

        daily_df = df.groupby("Date")["Amount"].sum().reset_index()

        fig3 = px.line(
            daily_df,
            x="Date",
            y="Amount",
            markers=True,
            title="Daily Transaction Trend"
        )
        st.plotly_chart(fig3, use_container_width=True)

# =========================
# FOOTER
# =========================

st.markdown("---")
st.markdown("💡 Built with Python + Streamlit + SQLite")
import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import plotly.express as px

# =========================
# SESSION STATE
# =========================
if "user" not in st.session_state:
    st.session_state.user = None

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Smart Expense Tracker",
    page_icon="💰",
    layout="wide"
)

# =========================
# DATABASE
# =========================
conn = sqlite3.connect("expenses.db", check_same_thread=False)
c = conn.cursor()

def create_tables():
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            date TEXT,
            category TEXT,
            type TEXT,
            amount REAL,
            note TEXT
        )
    """)
    conn.commit()

create_tables()

# =========================
# AUTH FUNCTIONS
# =========================
def signup_user(username, password):
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?,?)",
                  (username, password))
        conn.commit()
        return True
    except:
        return False

def login_user(username, password):
    c.execute("SELECT * FROM users WHERE username=? AND password=?",
              (username, password))
    return c.fetchone()

# =========================
# EXPENSE FUNCTIONS
# =========================
def add_transaction(user, date, category, t_type, amount, note):
    c.execute("""
        INSERT INTO expenses (username, date, category, type, amount, note)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user, date, category, t_type, amount, note))
    conn.commit()

def get_all_transactions(user):
    c.execute("""
        SELECT * FROM expenses
        WHERE username=?
        ORDER BY date DESC
    """, (user,))
    return c.fetchall()

def delete_transaction(t_id):
    c.execute("DELETE FROM expenses WHERE id=?", (t_id,))
    conn.commit()

def get_balance(user):
    c.execute("""
        SELECT SUM(amount) FROM expenses
        WHERE username=? AND type='Income'
    """, (user,))
    income = c.fetchone()[0] or 0

    c.execute("""
        SELECT SUM(amount) FROM expenses
        WHERE username=? AND type='Expense'
    """, (user,))
    expense = c.fetchone()[0] or 0

    return income, expense, income - expense

# =========================
# LOGIN SYSTEM
# =========================
if st.session_state.user is None:

    st.title("🔐 Smart Expense Tracker Login")

    mode = st.radio("Choose", ["Login", "Signup"])

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if mode == "Signup":
        if st.button("Create Account"):
            if signup_user(username, password):
                st.success("Account created! Please login")
            else:
                st.error("Username already exists")

    else:
        if st.button("Login"):
            user = login_user(username, password)
            if user:
                st.session_state.user = username
                st.success("Login successful 🚀")
                st.rerun()
            else:
                st.error("Invalid credentials")

# =========================
# MAIN APP (AFTER LOGIN)
# =========================
else:

    user = st.session_state.user

    st.sidebar.write(f"👤 {user}")

    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

    choice = st.sidebar.selectbox(
        "Menu",
        ["Dashboard", "Add Transaction", "View Transactions", "Analytics"],
        key="menu"
    )

    # =========================
    # DASHBOARD
    # =========================
    if choice == "Dashboard":

        income, expense, balance = get_balance(user)
        data = get_all_transactions(user)

        col1, col2, col3 = st.columns(3)
        col1.metric("Income", f"₹ {income}")
        col2.metric("Expense", f"₹ {expense}")
        col3.metric("Balance", f"₹ {balance}")

        st.subheader("Recent Transactions")

        df = pd.DataFrame(data, columns=[
            "ID", "Username", "Date", "Category", "Type", "Amount", "Note"
        ])

        st.dataframe(df.head(10), use_container_width=True)

        if income > expense:
            st.success("You are saving money 💰")
        else:
            st.error("You are spending more than income ⚠️")

        savings_rate = (balance / income * 100) if income > 0 else 0
        st.info(f"Savings Rate: {savings_rate:.2f}%")

    # =========================
    # ADD TRANSACTION
    # =========================
    elif choice == "Add Transaction":

        st.subheader("➕ Add Transaction")

        col1, col2 = st.columns(2)

        with col1:
            t_type = st.selectbox("Type", ["Income", "Expense"])
            category = st.selectbox("Category", [
                "Salary", "Food", "Travel", "Shopping",
                "Bills", "Entertainment", "Medical", "Other"
            ])

        with col2:
            amount = st.number_input("Amount", min_value=0.0)
            date = st.date_input("Date", datetime.today())

        note = st.text_input("Note")

        if st.button("Save"):
            if amount > 0:
                add_transaction(
                    user,
                    date.strftime("%Y-%m-%d"),
                    category,
                    t_type,
                    amount,
                    note
                )
                st.success("Saved successfully ✅")

    # =========================
    # VIEW TRANSACTIONS
    # =========================
    elif choice == "View Transactions":

        st.subheader("📋 Transactions")

        data = get_all_transactions(user)

        df = pd.DataFrame(data, columns=[
            "ID", "Username", "Date", "Category", "Type", "Amount", "Note"
        ])

        filter_type = st.selectbox("Filter", ["All", "Income", "Expense"])

        if filter_type != "All":
            df = df[df["Type"] == filter_type]

        st.dataframe(df, use_container_width=True)

        delete_id = st.number_input("Delete ID", min_value=1)

        if st.button("Delete"):
            delete_transaction(delete_id)
            st.warning("Deleted")

    # =========================
    # ANALYTICS
    # =========================
    elif choice == "Analytics":

        st.subheader("📊 Analytics")

        data = get_all_transactions(user)

        if len(data) == 0:
            st.info("No data")
        else:
            df = pd.DataFrame(data, columns=[
                "ID", "Username", "Date", "Category", "Type", "Amount", "Note"
            ])

            income_df = df[df["Type"] == "Income"]
            expense_df = df[df["Type"] == "Expense"]

            fig1 = px.bar(
                x=["Income", "Expense"],
                y=[income_df["Amount"].sum(), expense_df["Amount"].sum()],
                title="Income vs Expense"
            )
            st.plotly_chart(fig1, use_container_width=True)

            cat_df = expense_df.groupby("Category")["Amount"].sum().reset_index()

            fig2 = px.pie(cat_df, names="Category", values="Amount")
            st.plotly_chart(fig2, use_container_width=True)

            df["Date"] = pd.to_datetime(df["Date"])
            daily = df.groupby("Date")["Amount"].sum().reset_index()

            fig3 = px.line(daily, x="Date", y="Amount", markers=True)
            st.plotly_chart(fig3, use_container_width=True)
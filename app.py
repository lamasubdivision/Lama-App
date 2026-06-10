import streamlit as st
import sqlite3
import pandas as pd
import os
from fpdf import FPDF
from datetime import datetime

# --- Setup Paths ---
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
db_path = os.path.join(desktop_path, "land_sales.db")

# --- PDF Generation (The 24 Clauses) ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'VENDOR FINANCE AGREEMENT', 0, 1, 'C')

def create_contract_pdf(client_data):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 10, f"Client: {client_data['name']} | Plot: {client_data['plot_number']}", ln=True)
    pdf.cell(0, 10, f"Total Price: {client_data['contract_total']:,.0f} VUV", ln=True)
    pdf.ln(10)
    # This is a placeholder for the 24 clauses from your images
    clauses = "1. The vendor will sell... [Insert all 24 clauses here] ... 24. Laws of VANUATU."
    pdf.multi_cell(0, 5, clauses)
    file_path = os.path.join(desktop_path, f"Contract_{client_data['name']}.pdf")
    pdf.output(file_path)
    return file_path

# --- Database Setup ---
def get_db_connection():
    conn = sqlite3.connect(db_path)
    conn.execute('''CREATE TABLE IF NOT EXISTS plots 
                    (id INTEGER PRIMARY KEY, plot_number TEXT UNIQUE, land_size TEXT, 
                     title_number TEXT, location TEXT, status TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS clients 
                    (id INTEGER PRIMARY KEY, client_number TEXT, name TEXT, reg_date TEXT, 
                     plot_id INTEGER, contract_total REAL, 
                     FOREIGN KEY(plot_id) REFERENCES plots(id))''')
    return conn

# --- Interface ---
st.title("🏡 Lama Mount Subdivision Manager")
conn = get_db_connection()
menu = st.sidebar.radio("Menu", ["Dashboard", "Plot Inventory", "Clients"])

if menu == "Plot Inventory":
    with st.form("add_plot"):
        p_num = st.text_input("Plot Number")
        size = st.text_input("Land Size")
        title = st.text_input("Title Number")
        loc = st.text_input("Location/Stage")
        status = st.selectbox("Status", ["Available", "Sold", "Under Finance", "Reserved"])
        if st.form_submit_button("Add Plot"):
            conn.execute("INSERT INTO plots (plot_number, land_size, title_number, location, status) VALUES (?,?,?,?,?)", 
                         (p_num, size, title, loc, status))
            conn.commit()
            st.rerun()
    st.table(pd.read_sql("SELECT * FROM plots", conn))

elif menu == "Clients":
    with st.form("add_client"):
        c_num = st.text_input("Client Number")
        name = st.text_input("Full Name")
        reg_date = st.date_input("Registration Date")
        # Get only available plots
        available_plots = pd.read_sql("SELECT id, plot_number FROM plots WHERE status='Available'", conn)
        plot_select = st.selectbox("Assign Plot", available_plots['plot_number'] if not available_plots.empty else [])
        total = st.number_input("Total Contract Amount")
        if st.form_submit_button("Register & Contract"):
            if not available_plots.empty:
                p_id = available_plots[available_plots['plot_number'] == plot_select]['id'].iloc[0]
                conn.execute("INSERT INTO clients (client_number, name, reg_date, plot_id, contract_total) VALUES (?,?,?,?,?)", 
                             (c_num, name, str(reg_date), int(p_id), total))
                conn.execute("UPDATE plots SET status='Under Finance' WHERE id=?", (int(p_id),))
                conn.commit()
                st.success("Registered and Plot Status Updated!")
                st.rerun()

elif menu == "Dashboard":
    st.subheader("Active Contracts")
    query = "SELECT c.name, p.plot_number, c.contract_total FROM clients c JOIN plots p ON c.plot_id = p.id"
    data = pd.read_sql(query, conn)
    st.dataframe(data)

import streamlit as st
import sqlitecloud
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# --- PDF Generation ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'VENDOR FINANCE AGREEMENT', 0, 1, 'C')

def generate_pdf_bytes(client_data):
    """Generates PDF in memory for download."""
    pdf = PDF()
    pdf.add_page()
    my_secret_key = st.secrets["DB_CONNECTION_STRING"]
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 10, f"Client: {client_data['name']} | Plot: {client_data['plot_number']}", ln=True)
    pdf.cell(0, 10, f"Total Price: {client_data['contract_total']:,.0f} VUV", ln=True)
    pdf.ln(10)
    clauses = "1. The vendor will sell... [Insert all 24 clauses here] ... 24. Laws of VANUATU."
    pdf.multi_cell(0, 5, clauses)
    return pdf.output(dest='S').encode('latin-1')

# --- Database Setup & Initialization ---
def get_db_connection():
    return sqlitecloud.cts["DB_CONNECTION_STRING"])

def init_db(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS plots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plot_number TEXT,
            land_size TEXT,
            title_number TEXT,
            location TEXT,
            status TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_number TEXT,
            name TEXT,
            reg_date TEXT,
            plot_id INTEGER,
            contract_total REAL,
            FOREIGN KEY(plot_id) REFERENCES plots(id)
        )
    """)
    conn.commit()

# --- Interface ---
st.title("🏡 Lama Mount Subdivision Manager")

# Initialize connection and tables
conn = get_db_connection()
init_db(conn)

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
                
                pdf_data = generate_pdf_bytes({"name": name, "plot_number": plot_select, "contract_total": total})
                st.download_button("Download Contract PDF", pdf_data, f"Contract_{name}.pdf", "application/pdf")
                st.success("Registered and Plot Status Updated!")
                st.rerun()
    st.table(pd.read_sql("SELECT * FROM clients", conn))

elif menu == "Dashboard":
    st.subheader("Active Contracts")
    data = pd.read_sql("SELECT c.name, p.plot_number, c.contract_total FROM clients c JOIN plots p ON c.plot_id = p.id", conn)
    st.dataframe(data)

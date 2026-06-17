import streamlit as st
import pandas as pd
import sqlite3

# --- 1. Database & Config ---
# Replace this line with your actual database connection string
conn = sqlite3.connect('lama_subdivision.db', check_same_thread=False)

# --- 2. Initialize Session State ---
# This prevents the app from losing the "contract ready" status on refresh
if 'show_download' not in st.session_state:
    st.session_state.show_download = None

# --- 3. App UI & Menu ---
st.title("🏡 Lama Mount Subdivision Manager")
menu = st.sidebar.selectbox("Menu", ["Dashboard", "Register Client", "Plot Inventory"])

# --- 4. Logic for Registering Client ---
if menu == "Register Client":
    st.subheader("Register New Client")
    available_plots = pd.read_sql("SELECT * FROM plots WHERE status='Available'", conn)
    
    # FORM BLOCK: Only handles inputs and data submission
    with st.form("registration_form"):
        c_num = st.text_input("Client Number")
        name = st.text_input("Full Name")
        reg_date = st.date_input("Registration Date")
        plot_select = st.selectbox("Assign Plot", available_plots['plot_number'] if not available_plots.empty else [])
        total = st.number_input("Total Contract Amount")
        
        submit_btn = st.form_submit_button("Register & Contract")
        
        if submit_btn:
            if not available_plots.empty:
                # Perform DB update
                p_id = available_plots[available_plots['plot_number'] == plot_select]['id'].iloc[0]
                conn.execute("INSERT INTO clients (client_number, name, reg_date, plot_id, contract_total) VALUES (?,?,?,?,?)",
                             (c_num, name, str(reg_date), int(p_id), total))
                conn.execute("UPDATE plots SET status='Under Finance' WHERE id=?", (int(p_id),))
                conn.commit()
                
                # Store data in session to be accessed AFTER the form closes
                st.session_state.show_download = {"name": name, "plot_number": plot_select, "contract_total": total}
                st.rerun()
            else:
                st.error("No plots available.")

    # DOWNLOAD BLOCK: Outside the form, only shows if registration just happened
    if st.session_state.show_download:
        data = st.session_state.show_download
        # Ensure this function matches the one you have in your file
        pdf_data = generate_pdf_bytes(data) 
        
        st.success("Registered and Plot Status Updated!")
        st.download_button(
            label="Download Contract PDF", 
            data=pdf_data, 
            file_name=f"Contract_{data['name']}.pdf", 
            mime="application/pdf"
        )
        
        # Allows user to reset the view
        if st.button("Clear Notification"):
            st.session_state.show_download = None
            st.rerun()

# --- 5. Other Menus ---
elif menu == "Dashboard":
    st.subheader("Active Contracts")
    data = pd.read_sql("SELECT c.name, p.plot_number, c.contract_total FROM clients c JOIN plots p ON c.plot_id = p.id", conn)
    st.dataframe(data)

elif menu == "Plot Inventory":
    st.table(pd.read_sql("SELECT * FROM plots", conn))

import sqlitecloud

# Paste your connection string inside the quotes below
connection_string = 'sqlitecloud://ctnp0rlbvz.g4.sqlite.cloud:8860/auth.sqlitecloud?apikey=haKBajaFb8UCn2RIVnvWAXdqa8yZ7gyyIVx5nr3ofuE'

def add_lot(lot_number, client_name):
    try:
        # Connect to the cloud database
        conn = sqlitecloud.connect(connection_string)
        
        # Create the table if it doesn't exist
        conn.execute("CREATE TABLE IF NOT EXISTS lot_transactions (lot_number TEXT, client_name TEXT)")
        
        # Add the record
        query = "INSERT INTO lot_transactions (lot_number, client_name) VALUES (?, ?)"
        conn.execute(query, (lot_number, client_name))
        
        print(f"Successfully added {lot_number} for {client_name}")
        conn.close()
    except Exception as e:
        print(f"An error occurred: {e}")

# This part runs the function when you execute the script
if __name__ == "__main__":
    add_lot("LOT-001", "Example Client")
    print("Script finished!")
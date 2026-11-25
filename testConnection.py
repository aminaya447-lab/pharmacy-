from database import get_connection

try:
    conn = get_connection()
    print("Connected to SQL Server successfully!")

    cursor = conn.cursor()
    cursor.execute("SELECT DB_NAME()")

    print("Database:", cursor.fetchone()[0])

    cursor.close()
    conn.close()

except Exception as e:
    print("Connection failed!")
    print(e)
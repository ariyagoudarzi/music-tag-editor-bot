import sqlite3
conn = sqlite3.connect('user_database.db')
cursor = conn.cursor()


def get_user(chat_id):
    cursor.execute("SELECT * FROM users WHERE chat_id=?", (chat_id,))
    return cursor.fetchone()


def get_all_users():
    cursor.execute("SELECT * FROM users")
    return cursor.fetchall()


all_users = get_all_users()
print("\nAll users:")
for user in all_users:
    print("\n- Chat ID:", user[0])
    print("\n- Username:", user[1])
    print("\n- First Name:", user[2])
    print("\n- Last Name:", user[3])
    print("--------------------")
conn.close()

from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(
    __name__,
    template_folder='frontend/templates',
    static_folder='frontend/static'
)

# Home page
@app.route('/')
def home():
    return render_template('index.html')

# Other pages
@app.route('/create_account')
def create_account_page():
    return render_template('create_account.html')

@app.route('/deposit')
def deposit_page():
    return render_template('deposit.html')

@app.route('/withdraw')
def withdraw_page():
    return render_template('withdraw.html')

@app.route('/transfer')
def transfer_page():
    return render_template('transfer.html')

@app.route('/transactions')
def transactions_page():
    return render_template('transactions.html')

# Example POST route
@app.route('/create_account', methods=['POST'])
def create_account():
    name = request.form['name']
    balance = request.form['balance']

    conn = sqlite3.connect('database/banking.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO accounts (name, balance) VALUES (?, ?)", (name, balance))
    conn.commit()
    conn.close()

    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True)
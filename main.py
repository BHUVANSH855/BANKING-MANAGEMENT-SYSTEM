# main.py - CLI interface
import argparse
from db import initialize_db
import models
from utils import verify_pin

def input_pin(prompt='Enter PIN: '):
    import getpass
    return getpass.getpass(prompt)

def create_account_flow():
    name = input('Full name: ').strip()
    email = input('Email (optional): ').strip() or None
    phone = input('Phone (optional): ').strip() or None
    while True:
        pin = input_pin('Set numeric PIN (4-6 digits): ')
        pin2 = input_pin('Confirm PIN: ')
        if pin != pin2:
            print('PINs do not match, try again.')
            continue
        if not pin.isdigit() or not (4 <= len(pin) <= 6):
            print('PIN must be 4-6 digits numeric.')
            continue
        break
    init_dep_input = input('Initial deposit (0 if none): ').strip()
    init_dep = float(init_dep_input) if init_dep_input else 0.0
    acc_id = models.create_account(name, email, phone, pin, init_dep)
    print(f'Account created successfully. Account ID: {acc_id}')

def authenticate(account_id):
    acc = models.get_account(account_id)
    if not acc:
        print('Account not found')
        return False
    pin = input_pin('Enter PIN: ')
    if verify_pin(pin, acc['pin_hash']):
        return True
    print('Invalid PIN')
    return False

def view_account_flow():
    try:
        aid = int(input('Account ID: '))
    except ValueError:
        print('Invalid ID')
        return
    acc = models.get_account(aid)
    if not acc:
        print('Account not found')
        return
    print('--- Account details ---')
    print('ID:', acc['account_id'])
    print('Name:', acc['name'])
    print('Email:', acc['email'])
    print('Phone:', acc['phone'])
    print('Balance:', acc['balance'])
    print('Created at:', acc['created_at'])

def deposit_flow():
    try:
        aid = int(input('Account ID: '))
        amt = float(input('Amount to deposit: '))
    except ValueError:
        print('Invalid input')
        return
    try:
        new_bal = models.deposit(aid, amt)
        print('Deposit successful. New balance:', new_bal)
    except Exception as e:
        print('Error:', e)

def withdraw_flow():
    try:
        aid = int(input('Account ID: '))
    except ValueError:
        print('Invalid ID')
        return
    if not authenticate(aid):
        return
    try:
        amt = float(input('Amount to withdraw: '))
    except ValueError:
        print('Invalid amount')
        return
    try:
        new_bal = models.withdraw(aid, amt)
        print('Withdrawal successful. New balance:', new_bal)
    except Exception as e:
        print('Error:', e)

def transfer_flow():
    try:
        from_id = int(input('From Account ID: '))
    except ValueError:
        print('Invalid ID')
        return
    if not authenticate(from_id):
        return
    try:
        to_id = int(input('To Account ID: '))
        amt = float(input('Amount to transfer: '))
    except ValueError:
        print('Invalid input')
        return
    try:
        new_from, new_to = models.transfer(from_id, to_id, amt)
        print('Transfer successful.')
        print('From new balance:', new_from)
        print('To new balance:', new_to)
    except Exception as e:
        print('Error:', e)

def tx_history_flow():
    try:
        aid = int(input('Account ID: '))
    except ValueError:
        print('Invalid ID')
        return
    txs = models.get_transactions(aid, limit=50)
    if not txs:
        print('No transactions found.')
        return
    for t in txs:
        print(f"[{t['created_at']}] {t['type']} {t['amount']} => bal {t['balance_after']} ({t['note']})")

def delete_account_flow():
    try:
        aid = int(input('Account ID to delete: '))
    except ValueError:
        print('Invalid ID')
        return
    if not authenticate(aid):
        return
    confirm = input('Type YES to confirm deletion: ')
    if confirm == 'YES':
        models.delete_account(aid)
        print('Account deleted.')
    else:
        print('Aborted.')

def main_menu():
    while True:
        print('\n=== Banking Management System ===')
        print('1. Create account')
        print('2. View account')
        print('3. Deposit')
        print('4. Withdraw')
        print('5. Transfer')
        print('6. Transaction history')
        print('7. Delete account')
        print('0. Exit')
        choice = input('Choice: ').strip()
        if choice == '1':
            create_account_flow()
        elif choice == '2':
            view_account_flow()
        elif choice == '3':
            deposit_flow()
        elif choice == '4':
            withdraw_flow()
        elif choice == '5':
            transfer_flow()
        elif choice == '6':
            tx_history_flow()
        elif choice == '7':
            delete_account_flow()
        elif choice == '0':
            print('Bye')
            break
        else:
            print('Invalid choice')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--init', action='store_true', help='Initialize database (or use init_db.sql)')
    args = parser.parse_args()
    if args.init:
        # if you want to use the SQL file included, pass its path:
        try:
            initialize_db('init_db.sql')
        except Exception:
            initialize_db()
        print('Database initialized.')
    models.ensure_admin_account()
    main_menu()
  

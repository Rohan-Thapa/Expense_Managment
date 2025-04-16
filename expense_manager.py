import json
from datetime import datetime, timedelta
import pandas as pd
import os
from tabulate import tabulate
from pyfiglet import Figlet
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

DATA_FILE = "transactions.json"

def get_current_week_start():
    today = datetime.today().date()
    days_since_sunday = (today.weekday() + 1) % 7
    return today - timedelta(days=days_since_sunday)

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                if 'transactions' not in data or 'current_budget' not in data:
                    raise ValueError("Invalid data structure.")
            return data
        except (json.JSONDecodeError, ValueError) as e:
            print(Fore.RED + f"Error loading data: {e}. Initializing new data." + Style.RESET_ALL)
    return {'transactions': [], 'current_budget': None}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def add_transaction(data):
    days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    print("\nSelect day of the week:")
    for i, day in enumerate(days):
        print(f"{i}. {day}")
    day_choice = input("Enter day number (0-6): ")
    try:
        day_num = int(day_choice)
        if not 0 <= day_num < 7:
            raise ValueError
    except ValueError:
        print(Fore.RED + "Invalid day. Please enter a number between 0 and 6." + Style.RESET_ALL)
        return

    week_start = datetime.strptime(data['current_budget']['week_start'], "%Y-%m-%d").date()
    transaction_date = week_start + timedelta(days=day_num)
    if transaction_date > week_start + timedelta(days=6):
        print(Fore.RED + "Error: Date is outside the current budget week." + Style.RESET_ALL)
        return

    title = input("Enter transaction title: ").strip()
    if not title:
        print(Fore.RED + "Title cannot be empty." + Style.RESET_ALL)
        return

    while True:
        amount = input("Enter amount: ")
        try:
            amount = float(amount)
            if amount <= 0:
                print(Fore.RED + "Amount must be positive." + Style.RESET_ALL)
                continue
            break
        except ValueError:
            print(Fore.RED + "Invalid amount. Please enter a positive number." + Style.RESET_ALL)

    categories = ["food", "shopping", "entertainment", "bills", "other"]
    print("Select category:")
    for i, cat in enumerate(categories):
        print(f"{i}. {cat}")
    while True:
        cat_choice = input("Enter category number: ")
        try:
            cat_num = int(cat_choice)
            category = categories[cat_num]
            break
        except (ValueError, IndexError):
            print(Fore.RED + "Invalid category selection. Please choose a valid number." + Style.RESET_ALL)

    while True:
        type_choice = input("Enter type (income/expense) [i/e]: ").lower()
        if type_choice == 'i':
            t_type = 'income'
            break
        elif type_choice == 'e':
            t_type = 'expense'
            break
        else:
            print(Fore.RED + "Invalid type. Use 'i' for income or 'e' for expense." + Style.RESET_ALL)

    transaction = {
        'title': title,
        'amount': amount,
        'category': category,
        'type': t_type,
        'date': transaction_date.isoformat()
    }
    data['transactions'].append(transaction)
    save_data(data)
    print(Fore.GREEN + "\nTransaction added successfully." + Style.RESET_ALL)

def view_total_expenses(data):
    week_start = datetime.strptime(data['current_budget']['week_start'], "%Y-%m-%d").date()
    week_end = week_start + timedelta(days=6)

    df = pd.DataFrame(data['transactions'])
    if df.empty:
        print("\nNo transactions this week.")
        return

    df['date'] = pd.to_datetime(df['date']).dt.date
    mask = (df['date'] >= week_start) & (df['date'] <= week_end)
    current_week_transactions = df[mask]

    if current_week_transactions.empty:
        print("\nNo transactions this week.")
        return

    expenses = current_week_transactions[current_week_transactions['type'] == 'expense']['amount'].sum()
    income = current_week_transactions[current_week_transactions['type'] == 'income']['amount'].sum()
    budget = data['current_budget']['amount']
    remaining = budget - expenses

    print(f"\nWeekly Budget: रु.{budget:.2f}")
    print(f"Total Expenses: रु.{expenses:.2f}")
    print(f"Total Income: रु.{income:.2f}")
    print(f"Remaining Budget: रु.{remaining:.2f}")

def view_weekly_category_expenses(data):
    week_start = datetime.strptime(data['current_budget']['week_start'], "%Y-%m-%d").date()
    week_end = week_start + timedelta(days=6)
    df = pd.DataFrame(data['transactions'])
    if df.empty:
        print("\nNo transactions this week.")
        return

    df['date'] = pd.to_datetime(df['date']).dt.date
    mask = (df['date'] >= week_start) & (df['date'] <= week_end) & (df['type'] == 'expense')
    current_week_expenses = df[mask]

    if current_week_expenses.empty:
        print("\nNo expense transactions this week.")
        return

    category_totals = current_week_expenses.groupby('category')['amount'].sum().reset_index()
    table = tabulate(category_totals, headers=["Category", "Expense Amount"], tablefmt="grid", floatfmt=".2f")
    print("\nWeekly Expenses by Category:")
    print(table)

def view_daily_summary(data):
    week_start = datetime.strptime(data['current_budget']['week_start'], "%Y-%m-%d").date()
    df = pd.DataFrame(data['transactions'])
    if df.empty:
        print("\nNo transactions this week.")
        return

    df['date'] = pd.to_datetime(df['date']).dt.date
    mask = (df['date'] >= week_start) & (df['date'] <= week_start + timedelta(days=6))
    current_week = df[mask]

    days = [week_start + timedelta(days=i) for i in range(7)]
    rows = []
    for day in days:
        day_str = day.strftime("%A %Y-%m-%d")
        day_transactions = current_week[current_week['date'] == day]
        income_total = day_transactions[day_transactions['type'] == 'income']['amount'].sum() if not day_transactions.empty else 0
        expense_total = day_transactions[day_transactions['type'] == 'expense']['amount'].sum() if not day_transactions.empty else 0
        rows.append([day_str, income_total, expense_total])

    table = tabulate(rows, headers=["Date", "Income", "Expenses"], tablefmt="grid", floatfmt=".2f")
    print("\nDaily Summary (Income vs. Expenses):")
    print(table)

def view_daily_category_breakdown(data):
    week_start = datetime.strptime(data['current_budget']['week_start'], "%Y-%m-%d").date()
    df = pd.DataFrame(data['transactions'])
    if df.empty:
        print("\nNo transactions this week.")
        return

    df['date'] = pd.to_datetime(df['date']).dt.date
    mask = (df['date'] >= week_start) & (df['date'] <= week_start + timedelta(days=6))
    current_week = df[mask]

    days = [week_start + timedelta(days=i) for i in range(7)]
    print("\nDaily Category Breakdown:")
    for day in days:
        day_str = day.strftime("%A %Y-%m-%d")
        day_transactions = current_week[current_week['date'] == day]
        if day_transactions.empty:
            print(f"{day_str} - No transactions")
            continue
        breakdown = day_transactions.groupby(['category', 'type'])['amount'].sum().reset_index()
        table = tabulate(breakdown, headers=["Category", "Type", "Amount"], tablefmt="grid", floatfmt=".2f")
        print(f"\nTransactions for {day_str}:")
        print(table)

def main():
    # Display Welcome Banner using Pyfiglet
    figlet = Figlet(font="slant")
    print(figlet.renderText("Expense Manager"))
    print(Fore.BLUE + "\t\t\t - Rohan Thapa"+ Style.RESET_ALL)

    data = load_data()
    current_week_start = get_current_week_start()

    if data['current_budget'] is None:
        print("\nWelcome! Please set your budget for this week.")
        while True:
            budget_input = input("Enter weekly budget: रु.")
            try:
                budget = float(budget_input)
                if budget <= 0:
                    print(Fore.RED + "Budget must be positive." + Style.RESET_ALL)
                    continue
                data['current_budget'] = {
                    'week_start': current_week_start.isoformat(),
                    'amount': budget
                }
                save_data(data)
                break
            except ValueError:
                print(Fore.RED + "Invalid input. Please enter a number." + Style.RESET_ALL)
    else:
        budget_week_start = datetime.strptime(data['current_budget']['week_start'], "%Y-%m-%d").date()
        if budget_week_start != current_week_start:
            print(f"\nNew week detected (Current week starts on {current_week_start}).")
            print("Please set a new budget for this week.")
            while True:
                budget_input = input("Enter weekly budget: रु.")
                try:
                    budget = float(budget_input)
                    if budget <= 0:
                        print(Fore.RED + "Budget must be positive." + Style.RESET_ALL)
                        continue
                    data['current_budget'] = {
                        'week_start': current_week_start.isoformat(),
                        'amount': budget
                    }
                    save_data(data)
                    break
                except ValueError:
                    print(Fore.RED + "Invalid input. Please enter a number." + Style.RESET_ALL)

    while True:
        print("\n--- Expense Manager ---")
        print("1. Add Transaction")
        print("2. View Total Expenses")
        print("3. View Weekly Expenses by Category")
        print("4. View Daily Summary (Income vs. Expenses)")
        print("5. View Daily Category Breakdown")
        print("6. Exit")
        choice = input("\nEnter your choice (1-6): ").strip()

        if choice == '1':
            add_transaction(data)
        elif choice == '2':
            view_total_expenses(data)
        elif choice == '3':
            view_weekly_category_expenses(data)
        elif choice == '4':
            view_daily_summary(data)
        elif choice == '5':
            view_daily_category_breakdown(data)
        elif choice == '6':
            print("\nExiting the program. Goodbye!")
            break
        else:
            print(Fore.RED + "\nInvalid choice. Please enter a number between 1 and 6." + Style.RESET_ALL)

if __name__ == "__main__":
    main()

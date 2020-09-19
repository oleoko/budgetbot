from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.types import Message, ReplyKeyboardRemove
from fsm import Inc_exp, Ammount, Editcater, Semsum, Update, Edbudget, Month_stat
from keyboards import menu_kb, back_to_menu, back_to_menu_keyboard, start_menu_kb, inex_category, add_remove_keyboard, \
    edit_budget_category, previous_month_keyboard, previous_and_next_month_keyboard, upd_keyboard
import psycopg2
from config import DB_USER, DB_PORT, DB_PASS, DB_NAME, DB_HOST, TOKEN
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import requests
import time
from urllib.parse import urljoin
from aiogram.utils.executor import start_webhook
import os


WEBHOOK_URL = urljoin(WEBHOOK_HOST, WEBHOOK_URL_PATH)



remove_commands = [f'remove{x}' for x in range(1000)]
delete_commands = [f'delete{x}' for x in range(1000)]
upd_comment = [f'upd_comment{x}' for x in range(1000)]

regexp = r'^(?:(?:31(\/|-|\.)(?:0?[13578]|1[02]))\1|(?:(?:29|30)(\/|-|\.)(?:0?[13-9]|1[0-2])\2))(?:(?:1[6-9]|[2-9]\d)?\d{2})$|^(?:29(\/|-|\.)0?2\3(?:(?:(?:1[6-9]|[2-9]\d)?(?:0[48]|[2468][048]|[13579][26])|(?:(?:16|[2468][048]|[3579][26])00))))$|^(?:0?[1-9]|1\d|2[0-8])(\/|-|\.)(?:(?:0?[1-9])|(?:1[0-2]))\4(?:(?:1[6-9]|[2-9]\d)?\d{2})$'

calendar = {1:'January',2:'February',3:'March',4:'April',5:'May',6:'June',7:'July',8:'August',9:'September',10:'October',11:'November',12:'December'}

# Initialize bot and dispatcher
storage = MemoryStorage()
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=storage)


def db_connect():
    global conn, cur
    conn = psycopg2.connect(database=DB_NAME, user=DB_USER, password=DB_PASS,
                            host=DB_HOST, port=DB_PORT)
    conn.autocommit = True
    cur = conn.cursor()

def curent_ammount(message):
    # Get amount
    query_get_ammount = """SELECT ID,SUM,DATE FROM AMMOUNT WHERE ID=(%s);"""
    user = message.from_user.id
    cur.execute(query_get_ammount,[user])
    rows = cur.fetchall()
    for data in rows:
        user_ammount_data = data # Get user ammount data
    last_added_ammount = user_ammount_data[1] # Ammount sum
    date_ammount_added = user_ammount_data[2] # Date ammount was added

    # sum all expenceses after last ammount update
    query_select_expenceses = """SELECT SUM FROM BUDGET WHERE DATE>%s AND IN_EX=%s AND ID=%s;"""
    parameters_exp_query = [date_ammount_added,'expencese',message.from_user.id]
    cur.execute(query_select_expenceses,parameters_exp_query)
    rows = cur.fetchall()
    expenceses = 0
    for i in rows:
        expenceses -= round(float(i[0]),2)

    # sum all incomes after last ammount update
    query_select_incomes = """SELECT SUM FROM BUDGET WHERE DATE>%s AND IN_EX=%s AND ID=%s;"""
    parameters_exp_query = [date_ammount_added,'income',message.from_user.id]
    cur.execute(query_select_incomes,parameters_exp_query)
    rows = cur.fetchall()
    incomes = 0
    for i in rows:
        incomes += round(float(i[0]),2)

    # Counting current ammount
    curent_ammount = round(float(last_added_ammount),2)+expenceses+incomes
    if curent_ammount%1 == 0:
        curent_ammount = int(curent_ammount)
    else:
        curent_ammount = round(float(curent_ammount),2)
    return curent_ammount


def statistic(message, month, year):
    db_connect()
    user = message.from_user.id
    # Get all user categories for month
    text_ex = ''
    text_in = ''
    categ_sum = []
    categories_ex = []
    categories_in = []
    ex = []
    inc = []
    query_get_categories = """SELECT CATEGORY FROM BUDGET WHERE ID=%s AND IN_EX=%s AND EXTRACT(MONTH FROM DATE)=%s AND EXTRACT(YEAR FROM DATE)=%s;"""
    param_ex = [user,'expencese',month,year]
    param_in = [user, 'income',month,year]
    cur.execute(query_get_categories,param_ex)
    rows = cur.fetchall()
    if rows == []:
        text_ex = 'No expencese for this month\n'
    for category in rows:
        ex.append(category[0])
    cur.execute(query_get_categories, param_in)
    rows = cur.fetchall()
    if rows == []:
        text_in = "No income for this month"
    for category in rows:
        inc.append(category[0])
    [categories_ex.append(x) for x in ex if x not in categories_ex] # Delete dublicates
    [categories_in.append(x) for x in inc if x not in categories_in] # Delete dublicates


    # Get expencese categories sum
    query_get_sum_for_categ = """SELECT SUM FROM BUDGET WHERE ID=%s AND IN_EX=%s AND EXTRACT(MONTH FROM DATE)=%s AND EXTRACT(YEAR FROM DATE)=%s AND CATEGORY=%s;"""
    total_in = 0
    total_ex = 0
    for category in categories_ex:
        sum = 0
        categ=category
        param_sum_ex = [user, 'expencese', month, year, categ]
        cur.execute(query_get_sum_for_categ,param_sum_ex)
        rows = cur.fetchall()
        for value in rows:
            sum += float(value[0])
            total_ex += float(value[0])
        if sum%1 == 0:
            sum=int(sum)
        else:
            sum = round(sum,2)
        if total_ex%1 == 0:
            total_ex=int(total_ex)
        else:
            total_ex = round(total_ex,2)
        categ_sum.append([sum,categ])

    # Sort expencese categories by sum in reverse
    sorted_by_sum = sorted(categ_sum, key=lambda tup: tup[0],reverse=True)
    for sum_cat in sorted_by_sum:
        text_ex += f'{sum_cat[1]}: {sum_cat[0]}\n'

    # Reuse lists for income categories
    sorted_by_sum = []
    categ_sum = []

    # Get income categories sum
    for category in categories_in:
        sum = 0
        categ=category
        param_sum_in = [user, 'income', month, year, categ]
        cur.execute(query_get_sum_for_categ,param_sum_in)
        rows = cur.fetchall()
        for value in rows:
            sum += float(value[0])
            total_in += float(value[0])
        if sum%1 == 0:
            sum=int(sum)
        else:
            sum = round(sum,2)
        if total_in%1 == 0:
            total_in=int(total_in)
        else:
            total_in = round(total_in,2)
        categ_sum.append([sum,categ])

    # Sort income categories by sum in reverse
    sorted_by_sum = sorted(categ_sum, key=lambda tup: tup[0], reverse=True)
    for sum_cat in sorted_by_sum:
        text_in += f'{sum_cat[1]}: {sum_cat[0]}\n'
    result = f'Statistic for {calendar[month]} {year}:\n\nMonthly expenceses:\nTotal: {total_ex}\n{text_ex}\nMonthly incomes:\nTotal: {total_in}\n{text_in}'
    conn.close()
    return result

def delete_categories(message):
    global income_categories,expencese_categories, all_categories, dictionary
    income_categories = []
    expencese_categories = []
    all_categories = []
    dictionary = {}
    query_select_categories = """SELECT category FROM CATEGORIES WHERE ID = (%s) and IN_EX = (%s);"""
    parameters_in = [message.from_user.id,'income']
    parameters_ex = [message.from_user.id,'expencese']
    db_connect()
    cur.execute(query_select_categories,parameters_in)
    rows = cur.fetchall()
    for category in rows:
        income_categories.append(category[0])
        all_categories.append(category[0])
    cur.execute(query_select_categories, parameters_ex)
    rows = cur.fetchall()
    for category in rows:
        all_categories.append(category[0])
        expencese_categories.append(category[0])
    second_counter = 1
    for category in all_categories:
        dictionary[second_counter] = category
        second_counter +=1
    if len(all_categories) == 0:
        text = "You don't have any categories. Create one"
    else:
        text = 'Income categories:'
        counter = 1
        for category in income_categories:
            text += f'\n{counter}. {category}'
            text += f'\n/remove{counter}'
            counter += 1
        text += '\n\nExpencese categories:'
        for category in expencese_categories:
            text += f'\n{counter}. {category}'
            text += f'\n/remove{counter}'
            counter += 1
    conn.close()
    return text

def get_categories_list(message):
    global income_categories,expencese_categories, all_categories, dictionary
    income_categories = []
    expencese_categories = []
    all_categories = []
    dictionary = {}
    query_select_categories = """SELECT category FROM CATEGORIES WHERE ID = (%s) and IN_EX = (%s);"""
    parameters_in = [message.from_user.id,'income']
    parameters_ex = [message.from_user.id,'expencese']
    db_connect()
    cur.execute(query_select_categories,parameters_in)
    rows = cur.fetchall()
    for category in rows:
        income_categories.append(category[0])
        all_categories.append(category[0])
    cur.execute(query_select_categories, parameters_ex)
    rows = cur.fetchall()
    for category in rows:
        all_categories.append(category[0])
        expencese_categories.append(category[0])
    second_counter = 1
    for category in all_categories:
        dictionary[second_counter] = category
        second_counter +=1
    if len(all_categories) == 0:
        text = "You don't have any categories. Create one"
    else:
        text = 'Income categories:'
        counter = 1
        for category in income_categories:
            text += f'\n{counter}. {category}'
            counter += 1
        text += '\n\nExpencese categories:'
        for category in expencese_categories:
            text += f'\n{counter}. {category}'
            counter += 1
    conn.close()
    return text

def day_history(message,day,month,year):
    global data_to_delete
    data_to_delete= {}
    query_get_from_budget = """SELECT (SUM,CATEGORY,IN_EX,DATE) FROM budget WHERE ID=%s AND EXTRACT(DAY FROM DATE)=%s AND EXTRACT(MONTH FROM DATE)=%s AND EXTRACT(YEAR FROM DATE)=%s;"""
    query_parameters = [message.from_user.id,day,month,year]
    db_connect()
    cur.execute(query_get_from_budget,query_parameters)
    rows = cur.fetchall()
    if rows == []:
        tex = f'{day}.{month}.{year}\nThere are no data on this day'
    else:
        date = f'{day},{month},{year}'
        tex = f'{day}.{month}.{year}\n'
        counter = 1
        for data in rows:
            data = data[0][1:-1]
            data = data.split(',')
            categ = data[1]
            if data[1][0] == '"' and data[1][-1] == '"':
                categ = data[1][1:-1]
            if data[1][0:3] == '"""' and data[1][-3:] == '"""':
                categ = data[1][2:-2]
            tex += f'{categ} - {data[0]}\n{data[2]}\n/delete{counter}    /upd_comment{counter}\n\n'
            data_to_delete[counter] = [data[0],categ,data[2],date,data[3]]
            counter +=1
    conn.close()
    return tex

@dp.message_handler(text = '⬅️Back to menu',state='*')
async def enter_ammount_sum(message: Message, state: FSMContext):
    await message.answer('Main menu', reply_markup=menu_kb)
    await state.reset_state(with_data=True)  # Reset data in storage

                                        # Start
@dp.message_handler(commands=['start'],state='*')
async def send_welcome(message: Message, state: FSMContext):
    await state.reset_state(with_data=True)  # Reset data in storage
    await message.answer('Hello!\nI am your budget bot\n\nClick on button "Enter current balance" and enter your amount\nYou can also update your amount later using command /update'
                         '\n\nClick "expencese" or "income" button, enter sum and choose category to save your transaction. You can enter sum directly, without clicking on buttons,'
                         ' it will direct you to expencese categories. You can add comment to your transaction entering it after sum in format: "sum comment" \n\nUse commands:\n/edit_categories to add or remove your categories\n/edit_budget to delete your transactions', reply_markup=start_menu_kb)
    db_connect()
    user = [message.from_user.id]
    query_check_if_user_in_db = """SELECT ID FROM indicator WHERE ID = (%s);"""
    cur.execute(query_check_if_user_in_db, user)
    users = []
    rows = cur.fetchall()
    for id in rows:
        users.append(id[0])
    if message.from_user.id in users:  # Check if user already have categories. If not - add basic categories
        pass
    else:
        basic_expence_categories = ['Groсeries', 'Transport', 'Restaraunte', 'House', 'Car', 'Kids', 'Clothes', 'Study', 'Sport'] #🍯🚎🍽🏡🚘👶🏾👕💻🏓💰
        basic_income_categories = ['❤️️']
        query_add_basic_categories = """INSERT INTO categories (ID,CATEGORY,IN_EX) VALUES(%s,%s,%s);"""
        for category in basic_expence_categories:
            data = [message.from_user.id, category, 'expencese']
            cur.execute(query_add_basic_categories, data)
        for category in basic_income_categories:
            data = [message.from_user.id, category, 'income']
            cur.execute(query_add_basic_categories, data)
        query_add_to_users = """INSERT INTO indicator (ID) VALUES (%s);"""
        cur.execute(query_add_to_users, user)
    query_check_if_ammount = """SELECT ID FROM AMMOUNT WHERE ID = (%s);"""
    cur.execute(query_check_if_ammount, user)
    rows = cur.fetchall()
    users = []
    for id in rows:
        users.append(id[0])
    if message.from_user.id in users:  # Check if user already have ammount. If not - add basic categories
        pass
    else:
        query_add_null_ammount = """INSERT INTO AMMOUNT (ID,SUM,DATE) VALUES(%s,%s,%s);"""
        ammount_null_data = [message.from_user.id, 0, message.date]
        cur.execute(query_add_null_ammount, ammount_null_data)
    conn.close()


@dp.message_handler(commands='exchange_rate', state='*')
async def ed_budg(message:Message, state: FSMContext):
    await state.reset_state(with_data=True)  # Reset data in storage
    try:

        page = 'https://bank.gov.ua/'
        user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
        headers = {'User-Agent': user_agent, }
        request = requests.get(page)
        time.sleep(0.01)
        soup = BeautifulSoup(request.text, "html.parser")
        rates = []

        mydivs = soup.findAll("div", {"class": "value-full"})
        for i in mydivs:
            stri = str(i.contents[1])
            rate = round(float(stri.split("<")[1].split('>')[1].split(' ')[0].replace(',', '.')), 4)
            rates.append(rate)
        await message.answer(f'Exchange rate:\n1 EUR = {rates[0]}\n1 USD = {rates[1]}', reply_markup=menu_kb)
    except IndexError:
        await message.answer("For some reason we can't get exchange rate now\nPlease contact with https://t.me/oleoko", reply_markup=menu_kb)


@dp.message_handler(commands='edit_budget', state='*')
async def ed_budg(message:Message, state: FSMContext):
    await state.reset_state(with_data=True)  # Reset data in storage
    await message.answer('Edit today or any another day?', reply_markup=edit_budget_category)
    await Edbudget.Edbudget1.set()

@dp.message_handler(commands=['edit_categories'], state='*')
async def edit_buttons(message: Message, state: FSMContext):
    await state.reset_state(with_data=True)  # Reset data in storage
    await message.answer('Edit categories',reply_markup=add_remove_keyboard)
    await Editcater.Edit1.set()


@dp.message_handler(commands=['update'], state='*')
async def send_welcome(message: Message, state: FSMContext):
    await state.reset_state(with_data=True)  # Reset data in storage
    await Update.Updater.set()
    await message.answer('Enter new balance', reply_markup=back_to_menu_keyboard)

@dp.message_handler(state=Update.Updater)
async def send_welcome(message: Message, state=FSMContext):
    try:
        ammount = round(float(message.text), 2)
        query_add_ammount = """UPDATE AMMOUNT SET SUM=(%s),DATE=(%s) WHERE ID = (%s)"""
        ammount_data = [ammount, message.date, message.from_user.id]
        db_connect()
        cur.execute(query_add_ammount, ammount_data)
        conn.close()
        await state.reset_state(with_data=True)  # Reset state
        await message.answer(f'Your ammont updated.\nCurrent amount:\n{message.text}', reply_markup=menu_kb)
    except ValueError:
        await message.answer('Incorrect value. Try again', reply_markup=back_to_menu)

                                                # Enter amount
@dp.message_handler(text='Enter current balance', state=None)
async def enter_ammount(message: Message):
    await message.answer('Enter balance sum', reply_markup=back_to_menu_keyboard)
    await Ammount.Ammount_cur.set()


@dp.message_handler(state=Ammount.Ammount_cur)
async def enter_ammount_sum(message: Message, state: FSMContext):
    try:
        ammount = round(float(message.text),2)
        query_add_ammount = """UPDATE AMMOUNT SET SUM=(%s),DATE=(%s) WHERE ID = (%s)"""
        ammount_data = [ammount,message.date,message.from_user.id]
        db_connect()
        cur.execute(query_add_ammount,ammount_data)
        conn.close()
        await state.reset_state(with_data=True)  # Reset state            await message.answer(f'Your ammont updated.\nCurrent ammount:\n{message.text}',reply_markup=menu_kb)
    except ValueError:
        await message.answer('Incorrect value. Try again',reply_markup=back_to_menu)

                                        # Income/Expenceses section
@dp.message_handler(text='Income', state=None)
async def income(message: Message, state: FSMContext):
    await message.answer('Enter sum', reply_markup=back_to_menu_keyboard)
    await Inc_exp.Inex1.set()
    await state.update_data(exin='income')  # Saving expencese as parameter to filter categories by it


@dp.message_handler(text='Expencese', state=None)
async def income(message: Message, state: FSMContext):
    await message.answer('Enter sum', reply_markup=back_to_menu_keyboard)
    await Inc_exp.Inex1.set()  # Set fsm into first state
    await state.update_data(exin='expencese')  # Saving expencese as parameter to filter categories by it


@dp.message_handler(state=Inc_exp.Inex1)
async def enter_sum(message: Message, state: FSMContext):
    try:
        spl = message.text.split(' ')
        sum_value = round(float(spl[0]),2)
        if sum_value % 1 == 0:
            sum_value = int(sum_value)
        if sum_value > 10**15:
            await message.answer('What kind of inflation is it?\nHope you enter wrong value')
            return None
        comment = ' '.join(spl[1:])
        await state.update_data(com=comment)  # Saving comment
        db_connect()
        choose_cat_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(back_to_menu)  # Create keyboard for categories
        data = await state.get_data()  # Get data about which choosen income or expencese
        expence_par = data.get('exin')
        query_get_user_categories = """SELECT category FROM CATEGORIES WHERE ID = (%s) and IN_EX = (%s);"""
        id = [message.from_user.id, expence_par]
        cur.execute(query_get_user_categories, id)
        categories_list = []
        rows = list(cur)
        for category in rows:  # Generating user categories
            categories_list.append(category[0])  # Saving categories to filter message when one is choosen
        pairs = len(categories_list)//2
        ostatok = len(categories_list)%2
        for i in range(pairs):
            i = (i+1)*2
            choose_cat_kb = choose_cat_kb.row(KeyboardButton(f'{categories_list[i-2]}'),KeyboardButton(f'{categories_list[i-1]}'))
        if ostatok == 1:
            choose_cat_kb.add(KeyboardButton(f'{categories_list[-1]}'))
        choose_cat_kb = choose_cat_kb.add(KeyboardButton('➕Add category'))  # Add '+add category' button
        await message.answer('Choose category', reply_markup=choose_cat_kb)
        await state.update_data(categories=categories_list)  # Save user categories
        await state.update_data(sum=sum_value)  # Save sum
        await state.update_data(show_sum = sum_value)
        await Inc_exp.next()
        conn.close()
    except ValueError:
        await message.answer('Incorrect value. Try again', reply_markup=back_to_menu_keyboard)


@dp.message_handler(state=Inc_exp.Inex2)
async def choose_cat(message: Message, state=FSMContext):
    if message.text == '➕Add category':
        await message.answer('Enter category name',reply_markup=ReplyKeyboardRemove())
        await Inc_exp.Inex3.set()
    else:
        choosen_cat = message.text
        query_add_sum_in_category = """INSERT INTO budget (ID,SUM,CATEGORY,DATE,IN_EX) VALUES(%s,%s,%s,%s,%s)"""
        query_add_sum_in_category_with_com = """INSERT INTO budget (ID,SUM,CATEGORY,DATE,IN_EX,COMMENT) VALUES(%s,%s,%s,%s,%s,%s)"""
        data = await state.get_data()  # Get data from storage
        added_sum = data.get('show_sum')  # Get sum
        com = data.get('com')
        in_ex = data.get('exin')
        data_to_insert = [message.from_user.id, added_sum, choosen_cat, message.date, in_ex]
        data_to_insert_with_com = [message.from_user.id, added_sum, choosen_cat, message.date, in_ex, com]
        valid_categories = data.get('categories')  # Get list of valid categories
        db_connect()
        if choosen_cat in valid_categories:  # Check if message == valid category
            if com == []:
                cur.execute(query_add_sum_in_category, data_to_insert)
                await state.reset_state(with_data=True)  # Reset state and data in storage
            else:
                cur.execute(query_add_sum_in_category_with_com,data_to_insert_with_com)
                await state.reset_state(with_data=True)  # Reset state and data in storage
            cura = curent_ammount(message)
            await message.answer(f'{added_sum} added to category {choosen_cat}\nBalance: {cura}', reply_markup=menu_kb)
            query_add_ammount = """UPDATE AMMOUNT SET SUM=(%s),DATE=(%s) WHERE ID = (%s)"""
            ammount_data = [cura, message.date, message.from_user.id]
            cur.execute(query_add_ammount, ammount_data)
        else:
            await message.answer('Not added. Please chose valid category from buttons below')
        conn.close()


@dp.message_handler(state=Inc_exp.Inex3)
async def choose_cat(message: Message, state=FSMContext):
    print(len(message.text))
    if len(message.text)>299:
        await message.answer('Value too long', reply_markup=back_to_menu_keyboard)
    else:
        data = await state.get_data()  # Get data from storage
        added_sum = data.get('show_sum')  # Get sum
        in_ex = data.get('exin')
        com = data.get('com')
        choosen_cat = message.text
        db_connect()
        query_check_if_category_already_exist = """SELECT CATEGORY FROM CATEGORIES WHERE ID=%s AND IN_EX=%s"""
        param_check = [message.from_user.id, in_ex]
        cur.execute(query_check_if_category_already_exist,param_check)
        rows = cur.fetchall()
        for category in rows:
            if message.text == category[0]:
                await message.answer('Сategory already exist\nChoose another name',reply_markup=back_to_menu_keyboard)
                return None
        query_add_sum_in_category = """INSERT INTO budget (ID,SUM,CATEGORY,DATE,IN_EX) VALUES(%s,%s,%s,%s,%s)"""
        query_add_sum_in_category_with_comment = """INSERT INTO budget (ID,SUM,CATEGORY,DATE,IN_EX,COMMENT) VALUES(%s,%s,%s,%s,%s,%s)"""
        query_add_new_cat = """INSERT INTO categories (ID,CATEGORY,IN_EX) VALUES(%s,%s,%s);"""
        values = [message.from_user.id,message.text,in_ex]
        cur.execute(query_add_new_cat, values)
        data_to_insert = [message.from_user.id, added_sum, choosen_cat, message.date, in_ex]
        data_to_insert_with_com = [message.from_user.id, added_sum, choosen_cat, message.date, in_ex, com]
        if com == []:
            cur.execute(query_add_sum_in_category, data_to_insert)
        else:
            cur.execute(query_add_sum_in_category_with_comment,data_to_insert_with_com)
        cura = curent_ammount(message)
        await message.answer(f'{added_sum} added to category {choosen_cat}\nBalance: {cura}', reply_markup=menu_kb)
        query_add_ammount = """UPDATE AMMOUNT SET SUM=(%s),DATE=(%s) WHERE ID = (%s)"""
        ammount_data = [cura, message.date, message.from_user.id]
        cur.execute(query_add_ammount, ammount_data)
        await state.reset_state(with_data=True)  # Reset state and data in storage
        conn.close()

                                        # Statistics
@dp.message_handler(text='Statistics', state=None)
async def show_stat(message:Message, state:FSMContext):
    db_connect()
    cura = curent_ammount(message)
    stat = statistic(message,message.date.month,message.date.year)
    await message.answer(f'Balance: {cura}\n{stat}', reply_markup=previous_month_keyboard)
    await state.update_data(curent_month = message.date.month)
    await state.update_data(curent_year = message.date.year)
    await state.update_data(month = message.date.month)
    await state.update_data(year = message.date.year)
    await Month_stat.Month_stat1.set()

@dp.message_handler(text='Details', state=Month_stat.Month_stat1)
async def previous_month(message: Message, state: FSMContext):
    data = await state.get_data()
    month = int(data.get('month'))
    year = int(data.get('year'))
    text = ''
    mes = ''
    dates_list = []
    db_connect()
    query = "SELECT CATEGORY, SUM, COMMENT, IN_EX, DATE FROM BUDGET WHERE ID=%s AND EXTRACT(MONTH FROM DATE)=%s AND EXTRACT(YEAR FROM DATE)=%s"
    param = [message.from_user.id, month, year]
    cur.execute(query,param)
    rows = cur.fetchall()
    conn.close()

    if rows == []:
        await message.answer('No data for this month')
    else:
        rows = sorted(rows, key=lambda tup: tup[4], reverse=False)
        for transaction in rows:
            # Format sum, minutes, hours, month, day
            if float(transaction[1]) % 1 == 0:
                sum = int(transaction[1])
            else:
                sum = round(float(transaction[1]),2)

            if transaction[4].month<10:
                month = '0'+str(transaction[4].month)
            else:
                month = transaction[4].month

            if transaction[4].day < 10:
                day = '0' + str(transaction[4].day)
            else:
                day = transaction[4].day

            # Generating message text
            if transaction[4].day not in dates_list:
                if dates_list != []:
                    text += '\n\n'
                dates_list.append(transaction[4].day)
                text +=f'{day}.{month}.{transaction[4].year}'
            if transaction[3] == 'income':
                text += f'\n🔹{transaction[0]} {sum}'
            else:
                text += f'\n🔸{transaction[0]} {sum}'
            if transaction[2] != None and transaction[2] != '':
                text += f'\n{transaction[2]}'

            # Check if message longer 4000 var
            if len(mes) + len(text) > 4000:
                await message.answer(mes)
                mes = ''
                mes += text
            else:
                mes += text

            text = ''

    # If mes not None send it
    if mes != '':
        await message.answer(mes)


@dp.message_handler(text='Previous month', state=Month_stat.Month_stat1)
async def previous_month(message: Message, state: FSMContext):
    # Get data about next month
    data = await state.get_data()
    next_month = int(data.get('month'))
    get_year = await state.get_data()
    next_year = int(data.get('year'))
    if next_month == 1:
        month = 12
        year = next_year-1
    else:
        month = next_month-1
        year = next_year

    # Replace date with new date month earlier
    await state.update_data(month = month)
    await state.update_data(year = year)

    # Get monthly statistic
    stat = statistic(message,month,year)
    await message.answer(stat,reply_markup=previous_and_next_month_keyboard)

@dp.message_handler(text='Next month', state=Month_stat.Month_stat1)
async def previous_month(message: Message, state: FSMContext):
    # Get data about previous month
    data = await state.get_data()
    pre_month = int(data.get('month'))
    get_year = await state.get_data()
    pre_year = int(data.get('year'))
    if pre_month == 12:
        month = 1
        year = pre_year+1
    else:
        month = pre_month+1
        year = pre_year

    # Replace date with new date month earlier
    await state.update_data(month = month)
    await state.update_data(year = year)

    # Get monthly statistic
    stat = statistic(message, month, year)
    if month == message.date.month and year == message.date.year:
        keyboard = previous_month_keyboard
    else:
        keyboard = previous_and_next_month_keyboard

    await message.answer(stat,reply_markup=keyboard)

                           # Semsum
@dp.message_handler(regexp='\A\d', state = None)
async def show_stat(message:Message, state: FSMContext):
    try:
        spl = message.text.split(' ')
        number = round(float(spl[0]),2)
        if number > 10**15:
            await message.answer('What kind of inflation is it? \nHope you enter wrong value')
            return None
        comment = ' '.join(spl[1:])
        await state.update_data(com=comment)  # Saving comment
        await Semsum.Kateg1.set()  # Set fsm into first state
        await state.update_data(sum=number)  # Saving expencese as parameter to filter categories by it
        choose_cat_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(back_to_menu)  # Create keyboard for categories
        query_get_user_categories = """SELECT category FROM CATEGORIES WHERE ID = (%s) and IN_EX = (%s);"""
        expence_par = 'expencese'
        id = [message.from_user.id, expence_par]
        db_connect()
        cur.execute(query_get_user_categories, id)
        categories_list = []
        rows = list(cur)
        conn.close()
        for category in rows:  # Generating user categories
        #    choose_cat_kb = choose_cat_kb.add(KeyboardButton(f'{category[0]}'))  # Add buttons to ReplyKeyboardMarkup
            categories_list.append(category[0])  # Saving categories to filter message when one is choosen
        pairs = len(categories_list)//2
        ostatok = len(categories_list)%2
        for i in range(pairs):
            i = (i+1)*2
            choose_cat_kb = choose_cat_kb.row(KeyboardButton(f'{categories_list[i-2]}'),KeyboardButton(f'{categories_list[i-1]}'))
        if ostatok == 1:
            choose_cat_kb.add(KeyboardButton(f'{categories_list[-1]}'))
        choose_cat_kb = choose_cat_kb.add(KeyboardButton('➕Add category'))  # Add 'add category' button
        await state.update_data(categories=categories_list)  # Save user categories
        await message.answer('Choose category', reply_markup=choose_cat_kb)
    except ValueError:
        await message.answer('Invalid sum value')


@dp.message_handler(state=Semsum.Kateg1)
async def ch_cat(message: Message, state: FSMContext):
    if message.text == '➕Add category':
        await message.answer('Enter category name',reply_markup=ReplyKeyboardRemove())
        await Semsum.Kateg2.set()
    else:
        choosen_cat = message.text
        query_add_sum_in_category = """INSERT INTO budget (ID,SUM,CATEGORY,DATE,IN_EX) VALUES(%s,%s,%s,%s,%s)"""
        query_add_sum_in_category_with_comment = """INSERT INTO budget (ID,SUM,CATEGORY,DATE,IN_EX,COMMENT) VALUES(%s,%s,%s,%s,%s,%s)"""
        data = await state.get_data()  # Get data from storage
        added_sum = data.get('sum')  # Get sum
        if added_sum % 1 == 0:
            added_sum = int(added_sum)
        com = data.get('com')
        in_ex = 'expencese'
        data_to_insert = [message.from_user.id, added_sum, choosen_cat, message.date, in_ex]
        data_to_insert_with_com = [message.from_user.id, added_sum, choosen_cat, message.date, in_ex, com]
        valid_categories = data.get('categories')  # Get list of valid categories
        db_connect()
        if choosen_cat in valid_categories:  # Check if message == valid category
            if com == []:
                cur.execute(query_add_sum_in_category, data_to_insert)
                await state.reset_state(with_data=True)  # Reset state and data in storage
            else:
                cur.execute(query_add_sum_in_category_with_comment,data_to_insert_with_com)
                await state.reset_state(with_data=True)  # Reset state and data in storage
            cura = curent_ammount(message)
            await message.answer(f'{added_sum} added to category {choosen_cat}\nBalance: {cura}', reply_markup=menu_kb)
            query_add_ammount = """UPDATE AMMOUNT SET SUM=(%s),DATE=(%s) WHERE ID = (%s)"""
            ammount_data = [cura, message.date, message.from_user.id]
            cur.execute(query_add_ammount, ammount_data)
        else:
            await message.answer('Not added. Please chose valid category from buttons below')
        conn.close()


@dp.message_handler(state=Semsum.Kateg2)
async def choose_cat(message: Message, state=FSMContext):
    if len(message.text)>299:
        await message.answer('Value too long', reply_markup=back_to_menu_keyboard)
    else:
        data = await state.get_data()  # Get data from storage
        added_sum = data.get('sum')  # Get sum
        com = data.get('com')
        if added_sum % 1 == 0:
            added_sum = int(added_sum)
        in_ex = 'expencese'
        choosen_cat = message.text
        db_connect()
        query_check_if_category_already_exist = """SELECT CATEGORY FROM CATEGORIES WHERE ID=%s AND IN_EX=%s"""
        param_check = [message.from_user.id, in_ex]
        cur.execute(query_check_if_category_already_exist,param_check)
        rows = cur.fetchall()
        for category in rows:
            if message.text == category[0]:
                await message.answer('Сategory already exist\nChoose another name',reply_markup=back_to_menu_keyboard)
                return None
        query_add_sum_in_category = """INSERT INTO budget (ID,SUM,CATEGORY,DATE,IN_EX) VALUES(%s,%s,%s,%s,%s)"""
        query_add_new_cat = """INSERT INTO categories (ID,CATEGORY,IN_EX) VALUES(%s,%s,%s);"""
        values = [message.from_user.id, message.text, in_ex]
        cur.execute(query_add_new_cat, values)
        data_to_insert = [message.from_user.id, added_sum, choosen_cat, message.date, in_ex]
        query_add_sum_in_category_with_comment = """INSERT INTO budget (ID,SUM,CATEGORY,DATE,IN_EX,COMMENT) VALUES(%s,%s,%s,%s,%s,%s)"""
        data_to_insert_with_comment = [message.from_user.id, added_sum, choosen_cat, message.date, in_ex, com]
        if com == []:
            cur.execute(query_add_sum_in_category, data_to_insert)
        else:
            cur.execute(query_add_sum_in_category_with_comment,data_to_insert_with_comment)
        cura = curent_ammount(message)
        await message.answer(f'{added_sum} added to category {choosen_cat}\nBalance: {cura}', reply_markup=menu_kb)
        query_add_ammount = """UPDATE AMMOUNT SET SUM=(%s),DATE=(%s) WHERE ID = (%s)"""
        ammount_data = [cura, message.date, message.from_user.id]
        cur.execute(query_add_ammount, ammount_data)
        await state.reset_state(with_data=True)  # Reset state and data in storage
        conn.close()





                                           # Edit categories
@dp.message_handler(text=['➕Add category'], state=Editcater.Edit1)
async def add_cat1(message:Message, state:FSMContext):
    await message.answer("Choose category's class",reply_markup=inex_category)
    await Editcater.Edit2.set()


@dp.message_handler(text=['Income','Expencese'],state=Editcater.Edit2)
async def add_cat2(message:Message, state:FSMContext):
    in_ex = message.text.lower()
    await state.update_data(in_ex=in_ex)
    await message.answer('Enter category name',reply_markup=back_to_menu_keyboard)
    await Editcater.Edit3.set()


@dp.message_handler(state=Editcater.Edit3)
async def add_cat3(message:Message, state:FSMContext):
    if len(message.text)>299:
        await message.answer('Value too long', reply_markup=back_to_menu_keyboard)
    else:
        data = await state.get_data()
        in_ex = data.get('in_ex')
        query_add_cater = """INSERT INTO categories (ID,CATEGORY,IN_EX) VALUES(%s,%s,%s);"""
        parameters = [message.from_user.id,str(message.text),in_ex]
        db_connect()
        query_check_if_category_already_exist = """SELECT CATEGORY FROM CATEGORIES WHERE ID=%s AND IN_EX=%s"""
        param_check = [message.from_user.id, in_ex]
        cur.execute(query_check_if_category_already_exist,param_check)
        rows = cur.fetchall()
        for category in rows:
            if message.text == category[0]:
                await message.answer('Сategory already exist\nChoose another name',reply_markup=back_to_menu_keyboard)
                return None
        cur.execute(query_add_cater,parameters)
        text = get_categories_list(message)
        await message.answer(f'{in_ex.title()} category {message.text} added\nAll categories:\n{text}',reply_markup=add_remove_keyboard)
        await state.reset_state(with_data=True)
        await Editcater.Edit4.set()
        conn.close()


@dp.message_handler(text=['➕Add category'], state=Editcater.Edit4)
async def add_cat4(message:Message, state: FSMContext):
    await message.answer("Choose category's class",reply_markup=inex_category)
    await Editcater.Edit2.set()



@dp.message_handler(text='❌Remove category', state=[Editcater.Edit4,Editcater.Edit1])
async def rem_cat1(message:Message, state: FSMContext):
    text = delete_categories(message)
    await message.answer(text)


@dp.message_handler(commands=remove_commands, state=[Editcater.Edit4, Editcater.Edit1])
async def rem_cat1(message:Message, state: FSMContext):
    indicator = int(message.text[7:])
    text = delete_categories(message)
    try:
        category_to_delete = dictionary[indicator]
        if indicator > len(income_categories):
            inex = 'expencese'
        else:
            inex = 'income'
        query_to_delete_category = """DELETE FROM CATEGORIES WHERE ID=%s AND CATEGORY=%s AND IN_EX=%s"""
        parameters = [message.from_user.id, category_to_delete, inex]
        db_connect()
        cur.execute(query_to_delete_category, parameters)
        await message.answer(f'{category_to_delete} category deleted')
        text = delete_categories(message)
        await message.answer(text)
    except KeyError:
        await message.answer('There is no category with this index')

                                     # Edit budget
@dp.message_handler(text='Today', state=[Edbudget.Edbudget1,Edbudget.Edbudget2])
async def choose_day(message:Message, state: FSMContext):
    await state.update_data(date=message.date)
    await state.update_data(day_month_year=[message.date.day, message.date.month, message.date.year])
    tex = day_history(message,message.date.day,message.date.month,message.date.year)
    await message.answer(tex)
    await Edbudget.Edbudget2.set()


@dp.message_handler(text=['Another day'], state= [Edbudget.Edbudget1,Edbudget.Edbudget2,Edbudget.Edbudget3,Edbudget.Edbudget4])
async def choose_day(message:Message, state: FSMContext):
    await message.answer('Enter day in format dd.mm.yyyy',reply_markup=back_to_menu_keyboard)
    await Edbudget.Edbudget3.set()

@dp.message_handler(regexp=regexp, state=[Edbudget.Edbudget3,Edbudget.Edbudget4])
async def choose_daysd(message:Message, state: FSMContext):
    try:
        date = message.text.split('.')
        dayz, monthz, yearz = int(date[0]), int(date[1]), int(date[2])
        await state.update_data(day_month_year=[dayz, monthz, yearz])
        tex = day_history(message, dayz, monthz, yearz)
        await message.answer(tex)
        await Edbudget.Edbudget4.set()
    except ValueError:
        await message.answer('Invalid value. Enter day in format dd.mm.yyyy')


@dp.message_handler(commands=delete_commands, state=Edbudget.Edbudget2)
async def choose_day(message:Message, state: FSMContext):
    indicator = int(message.text[7:])
    data = await state.get_data()
    date = data.get('date')
    day_history(message,date.day,date.month,date.year)
    try:
        sum = float(data_to_delete[indicator][0])
        if sum%1 == 0:
            sum = int(sum)
        cat,inex,data = data_to_delete[indicator][1],data_to_delete[indicator][2],data_to_delete[indicator][4]
        query_edit_budget = """DELETE FROM BUDGET WHERE ID=%s AND SUM=%s AND CATEGORY=%s AND IN_EX=%s AND DATE=%s"""
        parameters = [message.from_user.id, sum, cat, inex, data]
        db_connect()
        cura = curent_ammount(message)
        cur.execute(query_edit_budget, parameters)
        if inex == 'income':
            suma = cura - sum
        else:
            suma = cura + sum
        query_add_ammount = """UPDATE AMMOUNT SET SUM=(%s),DATE=(%s) WHERE ID = (%s)"""
        ammount_data = [suma, message.date, message.from_user.id]
        cur.execute(query_add_ammount, ammount_data)
        conn.close()
        text = day_history(message, date.day, date.month, date.year)
        await message.answer(f'{sum} from {cat} deleted')
        await message.answer(text)

    except KeyError:
        await message.answer('Invalid command index')



@dp.message_handler(commands=delete_commands, state=Edbudget.Edbudget4)
async def choose_day(message: Message, state: FSMContext):
    sum, cat, inex, data = 0,0,0,0
    indicator = int(message.text[7:])
    data = await state.get_data()
    date = data.get('day_month_year')
    day_history(message, date[0], date[1], date[2])
    try:
        sum,cat,inex,data = float(data_to_delete[indicator][0]),data_to_delete[indicator][1],data_to_delete[indicator][2],data_to_delete[indicator][4]
        if sum % 1 == 0:
            sum = int(sum)
        print(cat)
        query_edit_budget = """DELETE FROM BUDGET WHERE ID=%s AND SUM=%s AND CATEGORY=%s AND IN_EX=%s AND DATE=%s"""
        parameters = [message.from_user.id, sum, cat, inex, data]
        db_connect()
        cur.execute(query_edit_budget, parameters)
        conn.close()
        text = day_history(message, date[0], date[1], date[2])
        await message.answer(f'{sum} from {cat} deleted')
        await message.answer(text)
    except (KeyError, UnboundLocalError) as e:
        await message.answer('Invalid command index')

@dp.message_handler(commands=upd_comment, state=[Edbudget.Edbudget4,Edbudget.Edbudget2])
async def type_comment(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        indicator = int(message.text[12:])
        date = data.get('day_month_year')
        day_history(message, date[0], date[1], date[2])
        sum, cat, inex, data = float(data_to_delete[indicator][0]), data_to_delete[indicator][1], \
                               data_to_delete[indicator][2], data_to_delete[indicator][4]
        await message.answer('Type comment',reply_markup=upd_keyboard)
        await state.update_data(commentind=message.text[12:])
        await Edbudget.Edbudget5.set()
    except KeyError:
        await message.answer('Invalid command index')

@dp.message_handler(text='Delete comment', state=Edbudget.Edbudget5)
async def type_comment(message: Message, state: FSMContext):
    data = await state.get_data()
    date = data.get('day_month_year')
    indicator = int(data.get('commentind'))
    sum, cat, inex, data = 0, 0, 0, 0
    print(date, indicator)
    day_history(message, date[0], date[1], date[2])
    sum, cat, inex, data = float(data_to_delete[indicator][0]), data_to_delete[indicator][1], \
                           data_to_delete[indicator][2], data_to_delete[indicator][4]

    query_update_comment = """UPDATE BUDGET SET COMMENT=%s WHERE ID=%s AND SUM=%s AND CATEGORY=%s AND IN_EX=%s AND DATE=%s"""
    parameters = ['', message.from_user.id, sum, cat, inex, data]
    db_connect()
    cur.execute(query_update_comment, parameters)
    conn.close()
    await message.answer(f'Comment deleted\nYou are in edit budget menu', reply_markup=edit_budget_category)
    await state.reset_state(with_data=True)  # Reset data in storage
    await Edbudget.Edbudget1.set()

@dp.message_handler(state=Edbudget.Edbudget5)
async def type_comment(message: Message, state: FSMContext):
    if len(message.text)>299:
        await message.answer('Value too long', reply_markup=back_to_menu_keyboard)
    else:
        data = await state.get_data()
        date = data.get('day_month_year')
        indicator = int(data.get('commentind'))
        sum, cat, inex, data = 0, 0, 0, 0
        print(date,indicator)
        day_history(message, date[0], date[1], date[2])
        try:
            sum, cat, inex, data = float(data_to_delete[indicator][0]), data_to_delete[indicator][1], \
                                   data_to_delete[indicator][2], data_to_delete[indicator][4]

            query_update_comment = """UPDATE BUDGET SET COMMENT=%s WHERE ID=%s AND SUM=%s AND CATEGORY=%s AND IN_EX=%s AND DATE=%s"""
            parameters = [message.text,message.from_user.id, sum, cat, inex, data]
            db_connect()
            cur.execute(query_update_comment, parameters)
            conn.close()
            text = day_history(message, date[0], date[1], date[2])
            await message.answer(f'Comment added\nYou are in edit budget menu',reply_markup=edit_budget_category)
            await state.reset_state(with_data=True)  # Reset data in storage
            await Edbudget.Edbudget1.set()
        except (KeyError, UnboundLocalError) as e:
            await message.answer('Invalid command index')


async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)


async def on_shutdown(dp):
    pass


if __name__ == '__main__':
    start_webhook(dispatcher=dp, webhook_path=WEBHOOK_URL_PATH,
                  on_startup=on_startup, on_shutdown=on_shutdown,
                  host='0.0.0.0', port=os.getenv('PORT'))


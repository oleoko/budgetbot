from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

income = KeyboardButton('Income')
expencese = KeyboardButton('Expencese')
statistics = KeyboardButton('Statistics')
back_to_menu = KeyboardButton('⬅️Back to menu')
enter_curent_ammount = KeyboardButton('Enter current balance')
upgrate_ammount = KeyboardButton('Upgrate ammount')
add_cat = KeyboardButton('➕Add category')
rem_cat = KeyboardButton('❌Remove category')
today = KeyboardButton('Today')
another_day = KeyboardButton('Another day')
previous_month = KeyboardButton('Previous month')
next_month = KeyboardButton('Next month')
details = KeyboardButton('Details')
upd_delete = KeyboardButton('Delete comment')


menu_kb = ReplyKeyboardMarkup(resize_keyboard = True).add(expencese).add(income).add(statistics)
back_to_menu_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(back_to_menu)
start_menu_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(enter_curent_ammount).add(expencese).add(income).add(statistics)
add_ammount = ReplyKeyboardMarkup(resize_keyboard=True).add(upgrate_ammount).add(back_to_menu)
inex_category = ReplyKeyboardMarkup(resize_keyboard=True).add(back_to_menu).add(income).add(expencese)
add_remove_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(back_to_menu).add(add_cat).add(rem_cat)
edit_budget_category = ReplyKeyboardMarkup(resize_keyboard=True).add(back_to_menu).add(today).add(another_day)
previous_month_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(back_to_menu).add(previous_month).add(details)
previous_and_next_month_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(back_to_menu).row(previous_month, next_month).add(details)
upd_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(back_to_menu).add(upd_delete)


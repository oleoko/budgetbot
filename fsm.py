from aiogram.dispatcher.filters.state import StatesGroup, State


class Inc_exp(StatesGroup):
    Inex1 = State()
    Inex2 = State()
    Inex3 = State()
    Inex4 = State()


class Ammount(StatesGroup):
    Ammount_cur = State()
    Ammount_upg = State()


class Editcater(StatesGroup):
    Edit1 = State()
    Edit2 = State()
    Edit3 = State()
    Edit4 = State()


class Semsum(StatesGroup):
    Kateg1 = State()
    Kateg2 = State()


class Update(StatesGroup):
    Updater = State()


class Edbudget(StatesGroup):
    Edbudget1 = State()
    Edbudget2 = State()
    Edbudget3 = State()
    Edbudget4 = State()
    Edbudget5 = State()


class Month_stat(StatesGroup):
    Month_stat1 = State()



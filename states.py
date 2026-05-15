from aiogram.fsm.state import State, StatesGroup

class RegistrationStates(StatesGroup):
    waiting_phone = State()

class PaymentStates(StatesGroup):
    waiting_for_check = State()

class AdminStates(StatesGroup):
    broadcast        = State()
    add_question     = State()
    add_q_subject    = State()
    add_q_bolim      = State()
    add_q_text       = State()
    add_q_a          = State()
    add_q_b          = State()
    add_q_c          = State()
    add_q_d          = State()
    add_q_correct    = State()
    add_q_image      = State()
    search_user      = State()
    set_solution_url = State()
    excel_import     = State()
    delete_bolim     = State()

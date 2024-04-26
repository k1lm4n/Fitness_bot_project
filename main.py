import logging
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ConversationHandler
import sqlite3
import bcrypt
import re
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from config import BOT_TOKEN

account = False
account_login = ''
status = 'пусто'

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)

sex_keyboard = [['Мужской', 'Женский']]
tren_keyboard = [['Бицепс и спина', 'Грудь и трицепс', 'Ноги и плечи']]
markup = ReplyKeyboardMarkup(sex_keyboard, one_time_keyboard=False)
markup_2 = ReplyKeyboardMarkup(tren_keyboard, one_time_keyboard=False)


def get_status(imt):
    if imt < 16:
        return 'Истощен. Вам срочно нужно набирать вес и обратится к специалисту'
    elif 16 <= imt <= 18.5:
        return 'Недостаточный вес. Вам стоит употреблять больше калорий'
    elif 18.5 < imt <= 24.9:
        return 'Нормальный вес. Вам нужно его удержать'
    elif 24.9 < imt <= 29.9:
        return 'Предожирение. Вам следует начать потреблять меньше калорий'
    elif 29.9 < imt <= 34.9:
        return 'Вероятно у Вас ожирение I степени. Следует обратиться к специалисту с этой проблемой'
    elif 34.9 < imt <= 39.9:
        return 'Вероятно у Вас ожирение II степени. Следует обратиться к специалисту с этой проблемой'
    elif imt > 40:
        return 'Вероятно у Вас ожирение III степени. Следует обратиться к специалисту с этой проблемой'


def poisk_po_bd(bd, row, table):
    con = sqlite3.connect(bd)
    cur = con.cursor()
    result = cur.execute(f"""SELECT {row} FROM {table}""").fetchall()
    con.close()
    return result


def poisk_poo_bd(bd, row, table, uslovie):
    con = sqlite3.connect(bd)
    cur = con.cursor()
    result = cur.execute(f"""SELECT {row} FROM {table}
                             WHERE {uslovie}""").fetchall()
    con.close()
    return result


def dobavit_v_bd(bd, table, row, znach):
    con = sqlite3.connect(bd)
    cur = con.cursor()
    cur.execute(f'''INSERT INTO {table}({row}) VALUES('{znach}')''')
    con.commit()
    con.close()


def obnov_v_bd(bd, table, uslovie, row, znach):
    con = sqlite3.connect(bd)
    cur = con.cursor()
    cur.execute(f'''UPDATE {table}
                    SET {row} = '{znach}'
                    WHERE {uslovie}''')
    con.commit()
    con.close()


def delete_from_bd(bd, table, uslovie):
    con = sqlite3.connect(bd)
    cur = con.cursor()
    cur.execute(f"""DELETE from {table}
                    WHERE {uslovie}""")
    con.commit()
    con.close()


async def start(update, context):
    user = update.effective_user
    await update.message.reply_html(
        rf"Привет {user.mention_html()}! Это бот, который станет твоим помощником для домашнего фитнеса."
        rf"Чтобы посмотреть команды нужно ввести /help",
    )


async def stop(update, context):
    await update.message.reply_text('Работа бота приостановлена')


async def help_command(update, context):
    if not account:
        await update.message.reply_text("Для начала вам необходимо зарегистрироваться/войти.\n"
                                        "Чтобы зарегистрироваться введите /reg \n"
                                        "Чтобы войти введите /login.")
    else:
        await update.message.reply_text('''Список команд:
        /prog - посмотреть прогресс
        /tren - подобрать тренировку
        /izves - изменить данные о весе
        /izros - изменить данные о росте
        /izage - изменить данные о возрасте''')


async def close_keyboard(update, context):
    await update.message.reply_text(
        "Ok",
        reply_markup=ReplyKeyboardRemove()
    )


async def wathc_progress(update, context):
    if account:
        global imt, tren
        tren = poisk_poo_bd('bd_users', 'trenirovok', 'list_of_users', f'login = "{account_login}"')[0][0]
        if not tren:
            tren = 0
        visota = float(poisk_poo_bd('bd_users', 'height', 'list_of_users', f'login = "{account_login}"')[0][0])
        massa = float(poisk_poo_bd('bd_users', 'weight', 'list_of_users', f'login = "{account_login}"')[0][0])
        print(visota, massa)
        imt = float(massa / ((visota / 100) ** 2))
        imt = round(imt, 2)
        await update.message.reply_text(f'''Ваш прогресс: 
Тренировок: {tren}
Вес: {massa}
Рост: {visota}
Индекс массы тела {imt} - {get_status(imt)}''')
    else:
        await update.message.reply_text('Сначала войдите в аккаунт!')


async def izmen_ves(update, context):
    await update.message.text('Введите ваш текущий вес')
    return 334


async def izmen_ves_one(update, context):
    new_ves = update.message.text
    if new_ves.isdigit() and 20 < int(new_ves) < 200:
        obnov_v_bd('bd_users', 'list_of_users', f'login = "{account_login}"', 'weight', int(new_ves))
        await update.message.reply_text('Данные успешно обновлены')
        return ConversationHandler.END
    else:
        await update.message.reply_text('Недопустимый ввод')
        return ConversationHandler.END


async def izmen_rost(update, context):
    await update.message.reply_text('Введите текущий рост')
    return 335


async def izmen_rost_one(update, context):
    new_rost = update.message.text
    if new_rost.isdigit() and 120 < int(new_rost) < 230:
        obnov_v_bd('bd_users', 'list_of_users', f'login = "{account_login}"', 'height', int(new_rost))
        await update.message.reply_text('Данные успешно обновлены')
        return ConversationHandler.END
    else:
        await update.message.reply_text('Недопустимый ввод')
        return ConversationHandler.END


async def izmen_age(update, context):
    await update.message.reply_text('Введите Ваш текущий возраст')
    return 333


async def izmen_age_one(update, context):
    new_age = update.message.text
    if new_age.isdigit() and 51 > int(new_age) > 13:
        obnov_v_bd('bd_users', 'list_of_users', f'login = "{account_login}"', 'age', int(new_age))
        await update.message.reply_text('Данные успешно обновлены')
        return ConversationHandler.END
    else:
        await update.message.reply_text('Недопустимый ввод')
        return ConversationHandler.END


async def first_reg_reply(update, context):
    await update.message.reply_text('Придумайте себе логин')
    return 1


async def second_reg_reply(update, context):
    login = update.message.text
    context.user_data['login'] = login
    lst = poisk_po_bd('bd_users', 'login', 'list_of_users')
    list_users = [el[0] for el in lst if lst]
    if login not in list_users or not list_users:
        dobavit_v_bd('bd_users', 'list_of_users', 'login', login)
        await update.message.reply_text('Отлично, теперь введите пароль. Он должен быть длиной от 8 до 16 знаков'
                                        'и сожержать только латинские буквы и цифры')
        return 2
    else:
        await update.message.reply_text('Такое имя уже занято, попробуйте другое')
        return 1


async def third_reg_reply(update, context):
    password = update.message.text
    if 7 < len(password) < 17 and not re.search(r'[^a-zA-Z0-9_]', password):
        hashAndSalt = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        print(hashAndSalt.decode('utf-8'))
        obnov_v_bd('bd_users', 'list_of_users', f'login = "{context.user_data['login']}"', 'password',
                   hashAndSalt.decode('utf-8'))
        await update.message.reply_text('Отлично. Теперь выберите свой пол', reply_markup=markup)
        return 3
    else:
        await update.message.reply_text('Недопустимый пароль, попробуйте другой. Введите еще раз')
        return 2


async def fourth_reg_reply(update, context):
    sex = update.message.text
    if sex.lower() == 'мужской' or sex.lower() == 'женский':
        obnov_v_bd('bd_users', 'list_of_users', f'login = "{context.user_data['login']}"', 'sex', sex.lower())
        await update.message.reply_text('Отлично. Теперь введите свой возраст', reply_markup=ReplyKeyboardRemove())
        return 4
    else:
        await update.message.reply_text('Некорректный ввод. Проверьте, что Вы написали. Введите еще раз')
        return 3


async def fifth_reg_reply(update, context):
    age = update.message.text
    if age.isdigit() and 14 <= int(age) <= 50:
        obnov_v_bd('bd_users', 'list_of_users', f'login = "{context.user_data['login']}"', 'age', int(age))
        await update.message.reply_text('Принято. Теперь введите свой рост')
        return 5
    elif int(age) < 14 or int(age) > 49:
        await update.message.reply_text('Программа не подразумевает тренировки для вашего возраста')
        delete_from_bd('bd_users', 'list_of_users', f'login = "{context.user_data['login']}"')
        return ConversationHandler.END
    else:
        await update.message.reply_text('Некорректный ввод. Проверьте, что Вы написали. Введите еще раз')
        return 4


async def sixth_reg_reply(update, context):
    height = update.message.text
    if height.isdigit() and 120 < int(height) < 230:
        obnov_v_bd('bd_users', 'list_of_users', f'login = "{context.user_data['login']}"', 'height', int(height))
        await update.message.reply_text('Зачтено. Введите свой вес')
        return 6
    elif not height.isdigit():
        await update.message.reply_text('Некорректный ввод. Проверьте, что Вы написали. Введите еще раз')
        return 5
    else:
        await update.message.reply_text('Я не верю, что у Вас такой рост. Напишите настоящий')
        return 5


async def seventh_reg_reply(update, context):
    weight = update.message.text
    if weight.isdigit() and 40 < int(weight) < 250:
        obnov_v_bd('bd_users', 'list_of_users', f'login = "{context.user_data['login']}"', 'weight', int(weight))
        obnov_v_bd('bd_users', 'list_of_users', f'login = "{account_login}"', 'trenirovok', 0)
        await update.message.reply_text('Отлично, Вы прошли регистрацию. Теперь Вы можете войти (команда /login)')
        context.user_data.clear()
        return ConversationHandler.END
    elif not weight.isdigit():
        await update.message.reply_text('Некорректный ввод. Проверьте, что Вы написали. Введите еще раз')
        return 6
    else:
        await update.message.reply_text('Я не верю что у Вас такой вес. Введите настоящий')
        return 6


async def first_login_reply(update, context):
    await update.message.reply_text('Для входа введите логин')
    return 11


async def second_login_reply(update, context):
    global account_login
    login = update.message.text
    context.user_data['login'] = login
    lst = poisk_po_bd('bd_users', 'login', 'list_of_users')
    list_users = [el[0] for el in lst if lst]
    if login not in list_users:
        await update.message.reply_text('Вы ввели несуществующий логин. Попробуйте еще раз')
        return 11
    else:
        account_login = login
        await update.message.reply_text('Теперь введите пароль')
        return 12


async def third_login_reply(update, context):
    password = update.message.text
    global massa
    print(poisk_poo_bd('bd_users', 'password', 'list_of_users', f'login = "{context.user_data['login']}"')[0][0])
    hashAndSalt = bytes(
        poisk_poo_bd('bd_users', 'password', 'list_of_users', f'login = "{context.user_data['login']}"')[0][0],
        encoding='utf-8')
    valid = bcrypt.checkpw(password.encode(), hashAndSalt)
    if valid:
        global account, account_login
        await update.message.reply_text('Успешно. Теперь вам доступны все команды, введите /help')
        account = True
        account_login = context.user_data['login']
        massa = poisk_poo_bd('bd_users', 'weight', 'list_of_users', f'login = "{context.user_data['login']}"')
        context.user_data.clear()
        return ConversationHandler.END
    elif password == 'back':
        await update.message.reply_text('Введите логин')
        return 11
    elif password == 'stoprg':
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            'Неверный пароль, попробуйте еще раз. Чтобы вернуться на логин, введите back. Чтобы остановить регистрацию'
            ' введите stoprg')
        return 12


async def trenirovka(update, context):
    if account:
        await update.message.reply_text('Выберите, на какие группы мышц хотите выполнить упражнения',
                                        reply_markup=markup_2)
        return 21
    else:
        await update.message.reply_text('Для начала войдите в аккаунт')


async def second_trenirovka(update, context):
    group_mishc = update.message.text
    age = int(poisk_poo_bd('bd_users', 'age', 'list_of_users', f'login = "{account_login}"')[0][0])
    if group_mishc.lower() == 'бицепс и спина':
        if 19 >= age >= 14:
            await update.message.reply_text(
                'Начнем. Первое упражнение. Подтягивания широким хватом 3 подхода на максимум (не больше 16 раз, '
                'если легко, то утяжелять вес).\n'
                'После выполнения введите ok. Чтобы остановить тренировку, введите /stop',
                reply_markup=ReplyKeyboardRemove())
            return 221
        elif age > 19:
            await update.message.reply_text(
                'Начнем. Первое упражнение. Тяга гантелей в наклоне 12-20 раз по 2-3 подхода. \nпосле выполнения введите ok. Чтобы остановить тренировку, введите /stop',
                reply_markup=ReplyKeyboardRemove())
            return 231
    elif group_mishc.lower() == 'грудь и трицепс':
        if 19 >= age >= 14:
            await update.message.reply_text(
                'Начнем. Первое упражнение. Отжимания на брусьях 5 подходов на максимум (не больше 16 раз, либо добавляй утяжеление).'
                ' \n после выполнения введите ok. Чтобы остановить тренировку, введите /stop',
                reply_markup=ReplyKeyboardRemove())
            return 241
        elif age > 19:
            await update.message.reply_text(
                'Начнем. Первое упражнение. Жим гантелей на горизонтальной скамье 12-20 раз по 2-3 подхода. \nпосле выполнения введите ok. Чтобы остановить тренировку, введите /stop',
                reply_markup=ReplyKeyboardRemove())
            return 251
    elif group_mishc.lower() == 'ноги и плечи':
        if 19 >= age >= 14:
            await update.message.reply_text('Начнем. Первое упражнение. Приседания 4 подхода на максимум '
                                            '(не больше 16 раз, если получается больше, добавляй утяжеление). \nпосле выполнения введите ok. Чтобы остановить тренировку, введите /stop',
                                            reply_markup=ReplyKeyboardRemove())
            return 261
        elif age > 19:
            await update.message.reply_text(
                'Начнем. Первое упражнение. Приседания с гантелями 12-20 раз по 2-3 подхода. \nпосле выполнения введите ok. Чтобы остановить тренировку, введите /stop',
                reply_markup=ReplyKeyboardRemove())
            return 271
    else:
        await update.message.reply_text('Некорректный ввод. Попробуйте еще раз')
        return 21


async def trenirovka_ruki_molodnyak_one(update, context):
    ok = update.message.text
    if ok == 'ok':
        await update.message.reply_text(
            'Отдохните пару минут. Следующее упражнение. Тяга гантелей в наклоне 4 подхода по 8-16 повторений.'
            '\nпосле выполнения введите ok. Чтобы остановить тренировку, введите /stop')
        return 222
    else:
        return 221


async def trenirovka_ruki_molodnyak_two(update, context):
    ok = update.message.text
    if ok == 'ok':
        await update.message.reply_text(
            'Отдохните пару минут. Следующее упражнение. Подтягивания узким обратным хватом 3 подхода на максимум (также не больше 16 раз).'
            '\nпосле выполнения введите ok. Чтобы остановить тренировку, введите /stop')
        return 223
    else:
        return 222


async def trenirovka_ruki_molodnyak_three(update, context):
    ok = update.message.text
    if ok == 'ok':
        await update.message.reply_text('Отдохните пару минут. Следующее упражнение. Лодочка 4 подхода по 16-20 раз.'
                                        '\nпосле выполнения введите ok. Чтобы остановить тренировку, введите /stop')
        return 224
    else:
        return 223


async def trenirovka_ruki_molodnyak_four(update, context):
    ok = update.message.text
    if ok == 'ok':
        await update.message.reply_text(
            'Отдохните пару минут. Следующее упражнение. Подъем гантелей на бицепс 4 подхода по 8-12 раз.'
            '\nпосле выполнения введите ok. Чтобы остановить тренировку, введите /stop')
        return 225
    else:
        return 224


async def trenirovka_ruki_molodnyak_five(update, context):
    global tren
    ok = update.message.text
    if ok == 'ok':
        if tren == 0:
            tren += 1
            await update.message.reply_text(
                'Поздравляю, Вы закончили свою первую тренировку. В слеюдщий раз стоит взять тренировку на другую группу мышц.'
                'Так же нужно дать день мышцам восстановиться')
            obnov_v_bd('bd_users', 'list_of_users', f'login = "{account_login}"', 'trenirovok', tren)
            return ConversationHandler.END
        else:
            tren += 1
            await update.message.reply_text(
                'Вы закончили тренировку. В слеюдщий раз стоит взять тренировку на другую группу мышц.'
                'Так же нужно дать день мышцам восстановиться')
            obnov_v_bd('bd_users', 'list_of_users', f'login = "{account_login}"', 'trenirovok', tren)
            return ConversationHandler.END
    else:
        return 225


async def trenirovka_ruki_one(update, context):
    ok = update.message.text
    if ok == 'ok':
        await update.message.reply_text(
            'Отдохните пару минут. Следующее упражнение. Тяга гантели в наклоне 12-20 повторений по 2-3 подхода. \nпосле выполнения введите ok. Чтобы остановить тренировку, введите /stop')
        return 232
    else:
        return 231


async def trenirovka_ruki_two(update, context):
    ok = update.message.text
    if ok == 'ok':
        await update.message.reply_text(
            'Отдохните пару минут. Следующее упражнение. '
            'Пуловер с гантелей лежа на скамье 12-20 повторений по 2-3 подхода.\nпосле выполнения введите ok. Чтобы остановить тренировку, введите /stop')
        return 233
    else:
        return 232


async def trenirovka_ruki_three(update, context):
    ok = update.message.text
    if ok == 'ok':
        await update.message.reply_text(
            'Отдохните пару минут. Следующее упражнение. '
            'Подъем гантелей на бицепс на наклонной скамье 12-20 повторений по 2-3 подхода.\nпосле выполнения введите ok. Чтобы остановить тренировку, введите /stop')
        return 234
    else:
        return 233


async def trenirovka_ruki_four(update, context):
    ok = update.message.text
    if ok == 'ok':
        await update.message.reply_text(
            'Отдохните пару минут. Следующее упражнение. '
            'Подъем гантелей на бицепс стоя 12-20 повторений по 2-3 подхода.\nпосле выполнения введите ok. Чтобы остановить тренировку, введите /stop')
        return 235
    else:
        return 234


async def trenirovka_ruki_five(update, context):
    ok = update.message.text
    if ok == 'ok':
        await update.message.reply_text(
            'Отдохните пару минут. Следующее упражнение. '
            'Подъем гантелей на бицепс хватом «молоток» 12-20 повторений по 2-3 подхода.\nпосле выполнения введите ok. Чтобы остановить тренировку, введите /stop')
        return 225
    else:
        return 235


async def trenirovka_grud_molodnyak_one(update, context):
    ok = update.message.text
    if ok == 'ok':
        await update.message.reply_text(
            'Отдохните пару минут. Следующее упражнение. Отжимания от пола 5 подходов на максимум (не больше 16 раз).\nпосле выполнения введите ok. Чтобы остановить тренировку, введите /stop')
        return 242
    else:
        return 241


async def trenirovka_grud_molodnyak_two(update, context):
    ok = update.message.text
    if ok == 'ok':
        await update.message.reply_text(
            'Отдохните пару минут. Следующее упражнение. Отжимания от пола узким хватом 5 подходов на максимум (не больше 16 раз).\nпосле выполнения введите ok. Чтобы остановить тренировку, введите /stop')
        return 225
    else:
        return 242


async def trenirovka_grud_one(update, context):
    ok = update.message.text
    if ok == 'ok':
        await update.message.reply_text(
            'Отдохните пару минут. Следующее упражнение. Жим гантелей на наклонной скамье 12-20 повторений 2-3 подхода.\nпосле выполнения введите ok. Чтобы остановить тренировку, введите /stop')
        return 252
    else:
        return 251


async def trenirovka_grud_two(update, context):
    ok = update.message.text
    if ok == 'ok':
        await update.message.reply_text(
            'Отдохните пару минут. Следующее упражнение. Сведение гантелей лежа 12-20 повторений 2-3 подхода.\nпосле выполнения введите ok. Чтобы остановить тренировку, введите /stop')
        return 253
    else:
        return 252


async def trenirovka_grud_three(update, context):
    ok = update.message.text
    if ok == 'ok':
        await update.message.reply_text(
            'Отдохните пару минут. Следующее упражнение. Французский жим лежа с гантелями 12-20 повторений 2-3 подхода.\nпосле выполнения введите ok. Чтобы остановить тренировку, введите /stop')
        return 254
    else:
        return 253


async def trenirovka_grud_four(update, context):
    ok = update.message.text
    if ok == 'ok':
        await update.message.reply_text(
            'Отдохните пару минут. Следующее упражнение. Отведение гантелей назад в наклоне 12-20 повторений 2-3 подхода.\nпосле выполнения введите ok. Чтобы остановить тренировку, введите /stop')
        return 255
    else:
        return 254


async def trenirovka_grud_five(update, context):
    ok = update.message.text
    if ok == 'ok':
        await update.message.reply_text(
            'Отдохните пару минут. Следующее упражнение. Разгибание гантели из-за головы 12-20 повторений 2-3 подхода.\nпосле выполнения введите ok. Чтобы остановить тренировку, введите /stop')
        return 225
    else:
        return 255


async def trenirovka_nogi_molodnyak_one(update, context):
    ok = update.message.text
    if ok == 'ok':
        await update.message.reply_text(
            'Отдохните пару минут. Следующее упражнение. Приседания 4 подхода на максимум (не больше 16 раз, если получается больше, добавляй утяжеление).\nпосле выполнения введите ok. Чтобы остановить тренировку, введите /stop')
        return 262
    else:
        return 261


async def trenirovka_nogi_molodnyak_two(update, context):
    ok = update.message.text
    if ok == 'ok':
        await update.message.reply_text(
            'Отдохните пару минут. Следующее упражнение. Выпады 4 подхода по 8-16 на каждую ногу.\nпосле выполнения введите ok. Чтобы остановить тренировку, введите /stop')
        return 263
    else:
        return 262


async def trenirovka_nogi_molodnyak_three(update, context):
    ok = update.message.text
    if ok == 'ok':
        await update.message.reply_text(
            'Отдохните пару минут. Следующее упражнение. Зашагивания на возвышенность 4 подхода по 8-16 на каждую ногу.\nпосле выполнения введите ok. Чтобы остановить тренировку, введите /stop')
        return 264
    else:
        return 263


async def trenirovka_nogi_molodnyak_four(update, context):
    ok = update.message.text
    if ok == 'ok':
        await update.message.reply_text(
            'Отдохните пару минут. Следующее упражнение. Жим гантелей стоя/сидя 4 подхода по 8-16 раз.\nпосле выполнения введите ok. Чтобы остановить тренировку, введите /stop')
        return 265
    else:
        return 264


async def trenirovka_nogi_molodnyak_five(update, context):
    ok = update.message.text
    if ok == 'ok':
        await update.message.reply_text(
            'Отдохните пару минут. Следующее упражнение. Махи в гантелями в стороны 4 подхода по 8-16 раз.\nпосле выполнения введите ok. Чтобы остановить тренировку, введите /stop')
        return 225
    else:
        return 265


async def trenirovka_nogi_one(update, context):
    ok = update.message.text
    if ok == 'ok':
        await update.message.reply_text(
            'Отдохните пару минут. Следующее упражнение. Приседания с гантелями 12-20 повторений 2-3 подхода.\nпосле выполнения введите ok. Чтобы остановить тренировку, введите /stop')
        return 272
    else:
        return 271


async def trenirovka_nogi_two(update, context):
    ok = update.message.text
    if ok == 'ok':
        await update.message.reply_text(
            'Отдохните пару минут. Следующее упражнение. Выпады с гантелями на месте 12-20 повторений 2-3 подхода.\nпосле выполнения введите ok. Чтобы остановить тренировку, введите /stop')
        return 273
    else:
        return 272


async def trenirovka_nogi_three(update, context):
    ok = update.message.text
    if ok == 'ok':
        await update.message.reply_text(
            'Отдохните пару минут. Следующее упражнение. Заход на скамью с гантелями 12-20 повторений 2-3 подхода.\nпосле выполнения введите ok. Чтобы остановить тренировку, введите /stop')
        return 274
    else:
        return 273


async def trenirovka_nogi_four(update, context):
    ok = update.message.text
    if ok == 'ok':
        await update.message.reply_text(
            'Отдохните пару минут. Следующее упражнение. Становая тяга с гантелями на прямых ногах 12-20 '
            'повторений 2-3 подхода.\nпосле выполнения введите ok. Чтобы остановить тренировку, введите /stop')
        return 275
    else:
        return 274


async def trenirovka_nogi_five(update, context):
    ok = update.message.text
    if ok == 'ok':
        await update.message.reply_text(
            'Отдохните пару минут. Следующее упражнение. Жим гантелей сидя 12-20 повторений 2-3 подхода.'
            '\nпосле выполнения введите ok. Чтобы остановить тренировку, введите /stop')
        return 276
    else:
        return 275


async def trenirovka_nogi_six(update, context):
    ok = update.message.text
    if ok == 'ok':
        await update.message.reply_text(
            'Отдохните пару минут. Следующее упражнение. Разведение рук с гантелями в стороны 12-20 повторений 2-3 '
            'подхода.\nпосле выполнения введите ok. Чтобы остановить тренировку, введите /stop')
        return 225
    else:
        return 276


def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("close", close_keyboard))
    application.add_handler(CommandHandler("prog", wathc_progress))
    age_handler = ConversationHandler(
        entry_points=[CommandHandler("izage", izmen_age)],
        states={
            333: [MessageHandler(filters.TEXT & ~filters.COMMAND, izmen_age_one)],
        },
        fallbacks=[]
    )
    ves_handler = ConversationHandler(
        entry_points=[CommandHandler("izves", izmen_ves)],
        states={
            334: [MessageHandler(filters.TEXT & ~filters.COMMAND, izmen_ves_one)],
        },
        fallbacks=[]
    )
    rost_handler = ConversationHandler(
        entry_points=[CommandHandler("izros", izmen_rost)],
        states={
            335: [MessageHandler(filters.TEXT & ~filters.COMMAND, izmen_rost_one)],
        },
        fallbacks=[]
    )
    reg_handler = ConversationHandler(
        entry_points=[CommandHandler("reg", first_reg_reply)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, second_reg_reply)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, third_reg_reply)],
            3: [MessageHandler(filters.TEXT & ~filters.COMMAND, fourth_reg_reply)],
            4: [MessageHandler(filters.TEXT & ~filters.COMMAND, fifth_reg_reply)],
            5: [MessageHandler(filters.TEXT & ~filters.COMMAND, sixth_reg_reply)],
            6: [MessageHandler(filters.TEXT & ~filters.COMMAND, seventh_reg_reply)]
        },
        fallbacks=[]
    )
    login_handler = ConversationHandler(
        entry_points=[CommandHandler("login", first_login_reply)],
        states={
            11: [MessageHandler(filters.TEXT & ~filters.COMMAND, second_login_reply)],
            12: [MessageHandler(filters.TEXT & ~filters.COMMAND, third_login_reply)]
        },
        fallbacks=[]
    )
    tren_handler = ConversationHandler(
        entry_points=[CommandHandler('tren', trenirovka)],
        states={
            21: [MessageHandler(filters.TEXT & ~filters.COMMAND, second_trenirovka)],
            221: [MessageHandler(filters.TEXT & ~filters.COMMAND, trenirovka_ruki_molodnyak_one)],
            222: [MessageHandler(filters.TEXT & ~filters.COMMAND, trenirovka_ruki_molodnyak_two)],
            223: [MessageHandler(filters.TEXT & ~filters.COMMAND, trenirovka_ruki_molodnyak_three)],
            224: [MessageHandler(filters.TEXT & ~filters.COMMAND, trenirovka_ruki_molodnyak_four)],
            225: [MessageHandler(filters.TEXT & ~filters.COMMAND, trenirovka_ruki_molodnyak_five)],
            231: [MessageHandler(filters.TEXT & ~filters.COMMAND, trenirovka_ruki_one)],
            232: [MessageHandler(filters.TEXT & ~filters.COMMAND, trenirovka_ruki_two)],
            233: [MessageHandler(filters.TEXT & ~filters.COMMAND, trenirovka_ruki_three)],
            234: [MessageHandler(filters.TEXT & ~filters.COMMAND, trenirovka_ruki_four)],
            235: [MessageHandler(filters.TEXT & ~filters.COMMAND, trenirovka_ruki_five)],
            241: [MessageHandler(filters.TEXT & ~filters.COMMAND, trenirovka_grud_molodnyak_one)],
            242: [MessageHandler(filters.TEXT & ~filters.COMMAND, trenirovka_grud_molodnyak_two)],
            251: [MessageHandler(filters.TEXT & ~filters.COMMAND, trenirovka_grud_one)],
            252: [MessageHandler(filters.TEXT & ~filters.COMMAND, trenirovka_grud_two)],
            253: [MessageHandler(filters.TEXT & ~filters.COMMAND, trenirovka_grud_three)],
            254: [MessageHandler(filters.TEXT & ~filters.COMMAND, trenirovka_grud_four)],
            255: [MessageHandler(filters.TEXT & ~filters.COMMAND, trenirovka_grud_five)],
            261: [MessageHandler(filters.TEXT & ~filters.COMMAND, trenirovka_nogi_molodnyak_one)],
            262: [MessageHandler(filters.TEXT & ~filters.COMMAND, trenirovka_nogi_molodnyak_two)],
            263: [MessageHandler(filters.TEXT & ~filters.COMMAND, trenirovka_nogi_molodnyak_three)],
            264: [MessageHandler(filters.TEXT & ~filters.COMMAND, trenirovka_nogi_molodnyak_four)],
            265: [MessageHandler(filters.TEXT & ~filters.COMMAND, trenirovka_nogi_molodnyak_five)],
            271: [MessageHandler(filters.TEXT & ~filters.COMMAND, trenirovka_nogi_one)],
            272: [MessageHandler(filters.TEXT & ~filters.COMMAND, trenirovka_nogi_two)],
            273: [MessageHandler(filters.TEXT & ~filters.COMMAND, trenirovka_nogi_three)],
            274: [MessageHandler(filters.TEXT & ~filters.COMMAND, trenirovka_nogi_four)],
            275: [MessageHandler(filters.TEXT & ~filters.COMMAND, trenirovka_nogi_five)],
            276: [MessageHandler(filters.TEXT & ~filters.COMMAND, trenirovka_nogi_five)]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )
    application.add_handler(tren_handler)
    application.add_handler(reg_handler)
    application.add_handler(login_handler)
    application.add_handler(age_handler)
    application.add_handler(rost_handler)
    application.add_handler(ves_handler)
    application.run_polling()


if __name__ == "__main__":
    main()

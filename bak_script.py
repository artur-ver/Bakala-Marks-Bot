import time
import os

import csv

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import selenium.common.exceptions
from selenium_stealth import stealth

from fake_useragent import UserAgent

from bs4 import BeautifulSoup

import telebot
from telebot import types

from dotenv import load_dotenv

load_dotenv()

bot = telebot.TeleBot(os.getenv('TELEGRAM_BOT_TOKEN'))
admin_id = os.getenv('ADMIN_ID')

# {
# id {'account_name': 'user_account_name',
# 'password': '0215454512015',
# 'school':'name_school'}
# }
personal_data = {}

params = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
show_profile_b = types.KeyboardButton(text='Show my profile 👽')
create_profile_b = types.KeyboardButton(text='Create/edit profile ✍')
table_marks_b = types.KeyboardButton(text='Show table marks ✨')
contact_admin_b = types.KeyboardButton(text='Contact admin 📞')
params.add(show_profile_b, create_profile_b, table_marks_b, contact_admin_b)


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 'Welcome! Let\'s get started. Use /save_my_data to begin.',  reply_markup=params)


@bot.message_handler(commands=['save_my_data'])
def save_data(message):
    mail = bot.send_message(message.chat.id, 'Please send your email 📧')
    bot.register_next_step_handler(mail, get_mail)


def get_mail(message):
    personal_data[message.from_user.id] = {'account_name': message.text}
    password = bot.send_message(message.chat.id, 'Please send your password 🔑')
    bot.register_next_step_handler(password, get_password)


def get_password(message):
    personal_data[message.from_user.id]['password'] = message.text
    school = bot.send_message(message.chat.id, 'Please send the name of your school 🏫')
    bot.register_next_step_handler(school, get_school)


def get_school(message):
    personal_data[message.from_user.id]['school'] = message.text
    bot.send_message(message.chat.id, 'Your profile has been created successfully 🎉', reply_markup=params)


def solving_complain(message):
    bot.send_message(admin_id, f'User: {message.from_user.username}\n'
                               f'First name: {message.from_user.first_name}\n'
                               f'Message: {message.text}')
    bot.send_message(message.chat.id, 'Your message has been sent. We will resolve it shortly 🛠️')


@bot.message_handler(content_types=['text'])
def text_handler(message):
    if message.text == 'Show my profile 👽':
        if message.chat.id in personal_data:
            bot.send_message(message.chat.id, f'Your school: {personal_data[message.chat.id]['school']} 🏫\n'
                                              f'User name: {personal_data[message.chat.id]['account_name']} 👤\n'
                                              f'Password: {personal_data[message.chat.id]['password']} 🔑\n')
        else:
            bot.send_message(message.chat.id, 'You are not registered ❌')

    elif message.text == 'Create/edit profile ✍':
        mail = bot.send_message(message.chat.id, 'Please send your account name 📧')
        bot.register_next_step_handler(mail, get_mail)
    elif message.text == 'Contact admin 📞':
        complaint = bot.send_message(message.chat.id, 'Please describe your problem 📝')
        bot.register_next_step_handler(complaint, solving_complain)

    elif message.text == 'Show table marks ✨':
        if message.chat.id in personal_data:
            bot.send_message(message.chat.id, 'Please wait for 20-40 seconds ⏳')

            options = webdriver.ChromeOptions()
            options.add_argument('--incognito')
            options.add_argument('--headless')
            options.add_argument(f"--user-agent={UserAgent().random}")
            options.add_argument("--disable-blink-features=AutomationControlled")

            options.add_experimental_option('excludeSwitches', ['enable-automation'])
            options.add_experimental_option('useAutomationExtension', False)

            service = Service(executable_path=ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)

            stealth(driver,
                    languages=["en-US", "en"],
                    vendor="Google Inc.",
                    platform="Win32",
                    webgl_vendor="Intel Inc.",
                    renderer="Intel Iris OpenGL Engine",
                    fix_hairline=True,
                    )

            driver.get('https://google.com')

            accept_rules = driver.find_element('xpath', '//*[@id="L2AGLb"]/div')
            if accept_rules:
                accept_rules.click()

            intput_field = driver.find_element('xpath', '//*[@id="APjFqb"]')
            intput_field.send_keys(f'bakalari {personal_data[message.chat.id]["school"]} \n')

            web_page = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located(('xpath', '//*[@id="rso"]/div[1]/div/div/div[1]/div/div/span/a')))
            text_page = driver.find_element('xpath', '//*[@id="rso"]/div[1]/div/div/div[1]/div/div/span/a/h3')
            if 'Bakaláři' in text_page.text:
                web_page.click()
            else:
                bot.send_message(message.chat.id, 'The school was not found ❌')

            email_input = driver.find_element('xpath', '//*[@id="username"]')
            email_input.send_keys(f'{personal_data[message.chat.id]["account_name"]}')
            password_input = driver.find_element('xpath', '//*[@id="password"]')
            password_input.send_keys(f'{personal_data[message.chat.id]["password"]}')

            button_login = driver.find_element('xpath', '//*[@id="loginButton"]')
            button_login.click()
            try:
                mother_element = driver.find_element('xpath', '//*[@id="_menu_nav"]/li[2]')
                mother_element.click()
                EC.presence_of_element_located(('xpath', '//*[@id="menuklas"]/li[1]'))

                marks = driver.find_element('xpath', '//*[@id="menuklas"]/li[1]')
                try:
                    marks.click()
                except selenium.common.exceptions.ElementNotInteractableException:
                    time.sleep(2)
                    marks.click()

                code_html = driver.page_source

                soup = BeautifulSoup(code_html, 'lxml')
                block = soup.find('div', id='cphmain_DivBySubject')
                els = block.find_all('div', class_='predmet-radek')

                with open('file_marks.csv', 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile, delimiter=';')
                    writer.writerow(['Subject', 'Mark', 'Date', 'Weight Mark'])

                    for el in els:
                        subject = el.find('h3').text
                        mark = el.find('div', class_='ob').text
                        weight = el.select('div.dodatek span')[0].text
                        date = el.select('div.dodatek span')[1].text
                        writer.writerow([subject, mark, date, weight])

                driver.quit()
                bot.send_document(message.chat.id, open('file_marks.csv', 'rb'))
                os.remove('file_marks.csv')
                bot.send_message(message.chat.id, 'Your document has been sent 📄')
            except selenium.common.exceptions.NoSuchElementException:
                driver.quit()
                bot.send_message(message.chat.id, 'Incorrect password or account name ❌')

        else:
            bot.send_message(message.chat.id, 'You are not registered ❌')


bot.polling(none_stop=True)

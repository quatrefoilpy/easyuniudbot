import datetime
import os
import zlib

import requests
from flask import *

from course import Course, Year, Period, Lecture

COURSES_URL = 'https://planner.uniud.it/PortaleStudenti/grid_call.php'
COURSES_INDEX_URL = 'https://planner.uniud.it/PortaleStudenti/combo.php'

WEEK_DAYS = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì']

TELEGRAM_ENDPOINT = 'https://api.telegram.org/bot5170440192:AAFrr7eCrLszcHoQBIN4H2kg3ssrGgmcPGI'
BOT_TOKEN = '5170440192:AAFrr7eCrLszcHoQBIN4H2kg3ssrGgmcPGI'

app = Flask(__name__)


@app.route('/5170440192:AAFrr7eCrLszcHoQBIN4H2kg3ssrGgmcPGI', methods=['POST'])
def handle_message():
    update = request.json
    try:
        if 'message' in update:
            message = update['message']
            chat_id = message['chat']['id']
            if 'text' in message:
                text = message['text']
                handle_text(str(chat_id), text)
        elif 'callback_query' in update:
            callback = update['callback_query']
            chat_id = callback['message']['chat']['id']
            callback_query = callback['data']
            handle_callback(str(chat_id), callback_query)
    except Exception as e:
        print(e)
    return update


def handle_callback(chat_id, callback_data):
    print(callback_data)
    callback_query = decompress_callback_data(callback_data)
    if 'one=' in callback_query:
        data = callback_query.split('=')[1]

        year_code = data.split(':')[0]
        year_name = data.split(':')[1]
        course_code = data.split(':')[2]

        periods = get_course_by_code(course_code, get_courses(2021)).periods

        send_periods_selection(chat_id, year_code, year_name, course_code, periods)
    if 'two=' in callback_query:
        data = callback_query.split('=')[1]

        year_code = data.split(':')[0]
        year_name = data.split(':')[1]
        course_code = data.split(':')[2]
        period_code = data.split(':')[3]

        send_lectures_selection(chat_id=chat_id, year_name=year_name, year_code=year_code, course_code=course_code, period_code=period_code)
    if 'three=' in callback_query:
        data = callback_query.split('=')[1]

        year_code = data.split(':')[0]
        year_name = data.split(':')[1]
        course_code = data.split(':')[2]
        period_code = data.split(':')[3]
        lecture_name = data.split(':')[4]

        send_lecture_info(chat_id=chat_id, lecture_name=lecture_name, year_name=year_name, year_code=year_code, course_code=course_code, period_code=period_code)


def handle_text(chat_id, text):
    if '/' not in text:
        send_courses_selection(chat_id, text)


def get_lectures(year, name, course_code, year_code, period):
    today = datetime.date.today()
    date = today.strftime("%d-%m-%Y")
    headers = {'content-type': 'application/x-www-form-urlencoded; charset=UTF-8'}
    body = f"view=easycourse&form-type=corso&include=corso&txtcurr=&anno={year}&corso={course_code}&anno2%5B%5D={year_code}&visualizzazione_orario=std&date={date}&periodo_didattico={period}&list=0&week_grid_type=-1&ar_codes_=&ar_select_=&col_cells=0&empty_box=0&only_grid=0&highlighted_date=0&all_events=0&faculty_group=0&_lang=it&txtcurr={name}"
    response = requests.post(url=COURSES_URL, headers=headers, data=body).json()
    lectures = []
    for cell in response['celle']:
        lecture = Lecture(name=cell['nome_insegnamento'], time=cell['orario'], teacher=cell['docente'],
                          day=WEEK_DAYS[int(cell['giorno']) - 1], room=cell['aula'])
        lectures.append(lecture)
    return lectures


def get_courses(year):
    response = requests.get(url=COURSES_INDEX_URL, params={'sw': 'ec_', 'aa': year, 'page': 'corsi'}).text
    json_start = response.find('[')
    json_end = response.find('\n')
    json_string = '{ "courses": ' + response[json_start:json_end].replace(';', '') + '}'
    courses = json.loads(json_string)['courses']
    courses_list = []
    for course in courses:
        years = course['elenco_anni']
        periods = course['periodi']
        c = Course(code=course['valore'],
                   course_type=course['tipo'],
                   name=course['label'] + ' - ' + course['tipo'])
        for period in periods:
            c.add_period(Period(code=period['valore'], name=period['label']))
        for year in years:
            c.add_year(
                Year(code=year['valore'], number=year['valore'][year['valore'].find('|') + 1:], name=year['label']))
        courses_list.append(c)
    return courses_list


def get_courses_by_name(courses, name):
    results = []
    for course in courses:
        if name.lower() in course.name.lower():
            results.append(course)
    return results


def get_lectures_index(lectures):
    results = []
    for lecture in lectures:
        if lecture.name not in results:
            results.append(lecture.name)
    return results


def get_lectures_by_name(name, lectures):
    results = []
    for lecture in lectures:
        if name.lower() in lecture.name.lower():
            lectures.append(lecture)
    return results


def get_course_by_code(code, courses):
    for course in courses:
        if course.code == code:
            return course
    return None


def get_year_by_code(code, course):
    for year in course.years:
        if year.code == code:
            return year
    return None


def get_periods_from_string(periods_string):
    result = []
    if '-' in periods_string and '.' in periods_string:
        periods = periods_string.split('.')
        for period in periods:
            parts = period.split(';')
            result.append(Period(parts[0], parts[1]))
    return result


def compress_callback_data(data):
    return zlib.compress(data)  # .decode('utf-8')


def decompress_callback_data(data):
    return zlib.decompress(data).decode('utf-8')


'''
Telegram functions
'''


def send_lecture_info(chat_id, lecture_name, course_code, year_name, year_code, period_code):
    lectures = get_lectures_by_name(lecture_name,
                                    get_lectures(2021, course_code=course_code, name=year_name,
                                                 year_code=year_code, period=period_code))
    if len(lectures) > 0:
        text = f"*{lectures[0].name}* \n {lectures[0].teacher} \n\n"
        for lecture in lectures:
            text += f'{lecture.day} - {lecture.time} - {lecture.room} \n'
        send_message(chat_id, text)
    else:
        send_message(chat_id, 'Nessuna lezione presente!')


def send_lectures_selection(chat_id, course_code, year_code, year_name, period_code):
    lectures_index = get_lectures_index(
        get_lectures(year=2021, course_code=course_code, name=year_name, year_code=year_code,
                     period=period_code))
    title = 'Lezioni disponibili per il periodo selezionato:'
    keyboard = {'inline_keyboard': []}
    for lecture in lectures_index:
        callback_data = f'three={year_code}:{year_name}:{course_code}:{period_code}:{lecture}'
        print(f'callback_data payload len: {str(len(callback_data.encode("utf-8")))}')
        row = [{'text': f'{lecture}', 'callback_data': compress_callback_data(callback_data)}]
        keyboard['inline_keyboard'].append(row)
    send_message_with_keyboard(chat_id, title, keyboard)


def send_periods_selection(chat_id, year_code, year_name, course_code, periods):
    title = 'Periodi disponibili'
    keyboard = {'inline_keyboard': []}
    for period in periods:
        callback_data = f'two={year_code}:{year_name}:{course_code}:{period.code}'
        row = [{'text': f'{period.name}', 'callback_data': compress_callback_data(callback_data)}]
        keyboard['inline_keyboard'].append(row)
    send_message_with_keyboard(chat_id, title, keyboard)


def send_courses_selection(chat_id, query):
    courses = get_courses_by_name(get_courses(2021), query)
    for course in courses:
        title = f'*{course.name}* \n Anni disponibili:'
        keyboard = {'inline_keyboard': []}
        for year in course.years:
            callback_data = f'one={year.code}:{year.name}:{course.code}'
            row = [{'text': f'{year.name}', 'callback_data': compress_callback_data(callback_data)}]
            keyboard['inline_keyboard'].append(row)
        send_message_with_keyboard(chat_id, title, keyboard)


def send_message_with_keyboard(chat_id, text, keyboard):  # message keyboard
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    payload = {'chat_id': chat_id, 'text': text, 'reply_markup': keyboard, 'parse_mode': 'Markdown'}
    r = requests.post(TELEGRAM_ENDPOINT + '/sendMessage', headers=headers, json=payload)
    print(r.content)


def send_message(chat_id, text):
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    payload = {'chat_id': chat_id, 'text': text, 'parse_mode': 'Markdown'}
    requests.post(TELEGRAM_ENDPOINT + '/sendMessage', headers=headers, json=payload)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

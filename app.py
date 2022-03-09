import datetime

import requests
import speech_recognition
from flask import *
from pydub import AudioSegment
from speech_recognition import *

from course import Course, Year, Period
from lecture import Lecture

COURSES_URL = 'https://planner.uniud.it/PortaleStudenti/grid_call.php'
COURSES_INDEX_URL = 'https://planner.uniud.it/PortaleStudenti/combo.php'

WEEK_DAYS = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì']

TELEGRAM_ENDPOINT = 'https://api.telegram.org/bot5170440192:AAFrr7eCrLszcHoQBIN4H2kg3ssrGgmcPGI'
BOT_TOKEN = '5170440192:AAFrr7eCrLszcHoQBIN4H2kg3ssrGgmcPGI'
BOT_URL = 'https://easyuniudbot.herokuapp.com'

app = Flask(__name__)


@app.route('/1091562071:AAEQ5eVuRSWS-9tj0c24KTNRA9sQ004ahfA', methods=['POST'])
def handle_message():
    update = request.json
    try:
        if 'message' in update:
            message = update['message']
            chat_id = message['chat']['id']
            if 'text' in message:
                text = message['text']
                handle_text(str(chat_id), text)
            elif 'voice' in message:
                file_id = message['voice']['file_id']
                handle_voice(str(chat_id), file_id)
        elif 'callback_query' in update:
            callback = update['callback_query']
            chat_id = callback['message']['chat']['id']
            callback_query = callback['data']
            handle_callback(str(chat_id), callback_query)
    except Exception as e:
        print(e)
    return update


def handle_voice(chat_id, file_id):
    file_url = f'https://api.telegram.org/bot1091562071:AAEQ5eVuRSWS-9tj0c24KTNRA9sQ004ahfA/getFile?file_id={file_id}'
    response = requests.get(url=file_url)
    file_info = response.json()
    file_path = file_info['result']['file_path']
    download_url = f'https://api.telegram.org/file/bot1091562071:AAEQ5eVuRSWS-9tj0c24KTNRA9sQ004ahfA/{file_path}'
    r = requests.get(download_url)
    with open(chat_id + '.oga', 'wb') as file:
        file.write(r.content)
    AudioSegment.from_ogg(chat_id + '.oga').export(chat_id + '.wav', format='wav')
    recognizer = speech_recognition.Recognizer()
    with speech_recognition.AudioFile(chat_id + '.wav') as source:
        audio = recognizer.record(source)
        try:
            input_text = recognizer.recognize_google(audio)
            handle_text(chat_id, input_text)
        except speech_recognition.UnknownValueError:
            send_message(chat_id, 'Impossibile elaborare correttamente il messaggio vocale, riprovare più tardi')
        except speech_recognition.RequestError:
            send_message(chat_id, 'Impossibile elaborare correttamente il messaggio vocale, riprovare più tardi')


def handle_callback(chat_id, callback_query):
    if 'step_one=' in callback_query:
        data = json.loads(callback_query.split('=')[1])
        send_periods_selection(chat_id, data)
    if 'step_two=' in callback_query:
        data = json.loads(callback_query.split('=')[1])
        send_lectures_selection(chat_id, data)
    if 'step_three=' in callback_query:
        data = json.loads(callback_query.split('=')[1])
        send_lecture_info(chat_id, data)


def handle_text(chat_id, text):
    if '/' not in text:
        send_courses_selection(chat_id, text)


def get_lectures(year, name, course_code, year_code, period):
    today = datetime.date.today()
    date = today.strftime("%d-%m-%Y")
    headers = {
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8'
    }
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
            c.add_period(Period(code=period['valore'], label=period['label']))
        for year in years:
            c.add_year(
                Year(code=year['valore'], number=year['valore'][year['valore'].find('|') + 1:], label=year['label']))
        courses_list.append(c)
    return courses_list


def get_courses_by_name(courses, name):
    results = []
    for course in courses:
        if name in course.name:
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
        if name in lecture.name:
            lectures.append(lecture)
    return results


'''
Telegram functions
'''


def send_lecture_info(chat_id, data):
    lectures = get_lectures_by_name(data['lecture'],
                                    get_lectures(2021, course_code=data['course_code'], name=data['year_label'],
                                                 year_code=data['year_code'], period=data['period_code']))
    if len(lectures) > 0:
        text = f"*{lectures[0].name}* \n {lectures[0].teacher} \n\n"
        for lecture in lectures:
            text += f'{lecture.day} - {lecture.time} - {lecture.room} \n'
        send_message(chat_id, text)
    else:
        send_message(chat_id, 'Nessuna lezione presente!')


def send_lectures_selection(chat_id, data):
    lectures_index = get_lectures_index(
        get_lectures(year=2021, course_code=data['course_code'], name=data['year_label'], year_code=data['year_code'],
                     period=data['period_code']))
    title = 'Lezioni disponibili per il periodo selezionato:'
    keyboard = {'inline_keyboard': []}
    for lecture in lectures_index:
        callback_data = data
        callback_data['lecture'] = lecture.name
        row = [{'text': f'{lecture.name}', 'callback_data': f'step_three{json.dumps(callback_data)}'}]
        keyboard['inline_keyboard'].append(row)
    send_message_with_keyboard(chat_id, title, keyboard)


def send_periods_selection(chat_id, data):
    title = 'Periodi disponibili'
    keyboard = {'inline_keyboard': []}
    for period in data['periods']:
        callback_data = data
        callback_data['period_code'] = period.code
        row = [{'text': f'{period.label}', 'callback_data': f'step_two{json.dumps(callback_data)}'}]
        keyboard['inline_keyboard'].append(row)
    send_message_with_keyboard(chat_id, title, keyboard)


def send_courses_selection(chat_id, query):
    courses = get_courses_by_name(get_courses(2021), query)
    for course in courses:
        title = f'*{course.name}* \n Anni disponibili:'
        keyboard = {'inline_keyboard': []}
        for year in course.years:
            periods_list = {}
            for period in course.periods:
                periods_list[period.label] = period.code
            callback_data = {'course_code': course.code, 'year_code': year.code, 'year_label': year.label,
                             'periods': periods_list}
            row = [{'text': f'{year.label}', 'callback_data': f'step_one={json.dumps(callback_data)}'}]
            keyboard['inline_keyboard'].append(row)
        send_message_with_keyboard(chat_id, title, keyboard)


def ask_location(chat_id):
    keyboard = {
        'keyboard': [[{'text': '\uD83D\uDCCD Condividi la tua posizione', 'request_location': True}],
                     [{'text': '\u274C Annulla'}]],
        'one_time_keyboard': True}
    send_keyboard(chat_id, keyboard)


def send_message_with_keyboard(chat_id, text, keyboard):  # message keyboard
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    payload = {'chat_id': chat_id, 'text': text, 'reply_markup': keyboard, 'parse_mode': 'Markdown'}
    requests.post(TELEGRAM_ENDPOINT + '/sendMessage', headers=headers, json=payload)


def send_message(chat_id, text):
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    payload = {'chat_id': chat_id, 'text': text, 'parse_mode': 'Markdown'}
    requests.post(TELEGRAM_ENDPOINT + '/sendMessage', headers=headers, json=payload)


def send_keyboard(chat_id, keyboard):
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    payload = {'chat_id': chat_id, 'reply_markup': keyboard, 'text': 'Scegli una opzione', 'parse_mode': 'Markdown'}
    requests.post(TELEGRAM_ENDPOINT + '/sendMessage', headers=headers, json=payload)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

import os
from playwright.sync_api import Playwright, sync_playwright
from dotenv import load_dotenv

load_dotenv()

sarkor_username = os.environ.get('sarkor_username')
sarkor_password = os.environ.get('sarkor_password')


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://dealertravel.sip.uz/#/")
    page.get_by_placeholder("umarjon").dblclick()
    page.get_by_placeholder("umarjon").fill(sarkor_username)
    page.locator("input[type=\"password\"]").click()
    page.locator("input[type=\"password\"]").fill(sarkor_password)
    page.get_by_role("button", name="Войти").click()
    page.get_by_role("navigation").locator("div").filter(has_text="История").click()
    page.get_by_role("button", name="Текущая неделя").click()
    # page.get_by_text("Сегодня", exact=True).click()
    page.get_by_text("Вчера", exact=True).click()

    def convert_to_seconds(value: str) -> int:
        try:
            minutes, seconds = map(int, value.split(':'))

            total_seconds = minutes * 60 + seconds

            return total_seconds
        except Exception:
            return 0

    def extract_table_data(table_locator):
        rows = table_locator.locator("tr[class=\"itl-table-row history-table-row\"]")
        data = []
        for i in range(rows.count()):
            row = rows.nth(i)
            cells = row.locator("td")
            row_data = {
                'Сотрудник': '',
                'Длительность': '',
                'Ожидание': ''
            }
            counter = 0
            for j in range(cells.count()):
                match counter:
                    case 2:
                        row_data['Сотрудник'] = cells.nth(j).text_content().strip()
                    case 6:
                        row_data['Длительность'] = cells.nth(j).text_content().strip()
                    case 5:
                        row_data["Ожидание"] = cells.nth(j).text_content().strip()
                counter += 1
            data.append(row_data)
            ctx = {}
            for i in data:
                if i['Сотрудник'] not in ctx:
                    ctx[i['Сотрудник']] = []
                ctx[i['Сотрудник']].append({
                    'Длительность': i['Длительность'],
                    'Ожидание': i['Ожидание']
                })
            finally_data = []
            for name, records in ctx.items():
                all_calls_count, missed_calls_count, calls_count, calls_second = 0, 0, 0, 0
                for record in records:
                    check = [1 if key.lower().startswith('д') else 0 for key in record.keys()]
                    if sum(check) > 0:
                        dialing = record['Длительность']
                        if not dialing.lower().startswith('н'):
                            calls_second += convert_to_seconds(record['Длительность'])
                        else:
                            missed_calls_count += 1
                        all_calls_count += 1

                finally_data.append({
                    'name': name,
                    'calls_average': round(calls_second / all_calls_count if all_calls_count != 0 else 0, 1),
                    'missed_calls_count': missed_calls_count,
                    'calls_second': calls_second,
                    'all_calls_count': all_calls_count
                })

        return finally_data

    def combine_finally_data(in_calls, out_calls):
        all_names = set(call['name'] for call in in_calls).union(set(call['name'] for call in out_calls))
        combined_data = []

        out_calls_dict = {call['name']: call for call in out_calls}
        in_calls_dict = {call['name']: call for call in in_calls}

        for name in all_names:
            in_call = in_calls_dict.get(name, {})
            out_call = out_calls_dict.get(name, {})

            combined_data.append({
                'name': name,
                'calls_average': round((in_call.get('calls_average', 0) + out_call.get('calls_average', 0)) / 2, 1),
                'missed_calls_count': in_call.get('missed_calls_count', 0) + out_call.get('missed_calls_count', 0),
                'call_in': in_call.get('all_calls_count', 0),
                'call_out': out_call.get('all_calls_count', 0),
                'calls_second': in_call.get('calls_second', 0) + out_call.get('calls_second', 0),
                'all_calls_count': in_call.get('all_calls_count', 0) + out_call.get('all_calls_count', 0)
            })

        return combined_data

    page.get_by_text(' Входящие ', exact=True).click()
    page.wait_for_selector("table[class=\"history-table\"]")
    in_calls_table = page.locator("table[class=\"history-table\"]")
    in_data = extract_table_data(in_calls_table)

    page.get_by_text(' Исходящие ', exact=True).click()
    page.wait_for_selector("table[class=\"history-table\"]")
    out_calls_table = page.locator("table[class=\"history-table\"]")
    out_data = extract_table_data(out_calls_table)

    combined_data = combine_finally_data(in_data, out_data)

    return combined_data


def get_sarkor_datas():
    with sync_playwright() as play:
        datas = run(play)
    return datas

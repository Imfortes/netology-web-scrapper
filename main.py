


import time
import csv
import os
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fake_useragent import UserAgent
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

KEYWORDS = ['дизайн', 'фото', 'web', 'python']
CSV_FILE = 'habr_articles.csv'
# data = []
MAX_THREADS = 5

file_exists = os.path.isfile(CSV_FILE)

existing_links = set()
if file_exists:
    with open(CSV_FILE, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            existing_links.add(row['link'])


def save_to_csv(data):
    if isinstance(data, dict):
        data = [data]

    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['title', 'link', 'description', 'full_text']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        try:
            writer.writerows(data)
        except Exception as e:
            print(f"Ошибка при записи в CSV: {e}")


def parse_article(link, title):
    ua = UserAgent()
    options = webdriver.ChromeOptions()
    options.add_argument(f'user-agent={ua.random}')
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)

    try:
        driver.get(link)
        full_text_elem = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.tm-article-body'))
        )
        full_text = full_text_elem.text
        description = full_text[:200] + '...' if len(full_text) > 200 else full_text

        full_text_lower = full_text.lower()
        keyword_found = any(keyword.lower() in title.lower() or keyword.lower() in full_text_lower for keyword in KEYWORDS)

        if keyword_found:
            article_data = {
                'title': title,
                'link': link,
                'description': description,
                'full_text': full_text,
            }
            save_to_csv([article_data])
            return article_data
        return None

    except TimeoutException:
        print(f'Не удалось загрузить статью {link}')
        return None
    finally:
        driver.quit()


def web_scrapping():
    ua = UserAgent()
    options = webdriver.ChromeOptions()
    options.add_argument(f'user-agent={ua.random}')
    options.add_argument('--headless')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)


    try:
        driver.get('https://habr.com/ru/articles/')
        print(f'Текущий URL {driver.current_url}')
        wait = WebDriverWait(driver, 10)

        try:
            pagination_list = wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a.tm-pagination__page'))
            )
        except TimeoutException:
            print(f'HTML страницы {driver.page_source[:2000]}')
            return

        total_pages = int(pagination_list[-1].text)
        print(f'Всего страниц {total_pages}')

        for page in tqdm(range(1, total_pages + 1), desc="Парсинг страниц", unit="страница"):
            driver.get(f'https://habr.com/ru/articles/page{page}/')
            print(f"Открыта страница: {page}, URL: {driver.current_url}")
            wait_driver = WebDriverWait(driver, 10)
            article_blocks = wait_driver.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.tm-article-snippet'))
            )

            with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
                futures = []
                for article in article_blocks:
                    article_title = article.find_element(By.CSS_SELECTOR, 'h2.tm-title a')
                    title = article_title.text
                    link = article_title.get_attribute('href')

                    if link in existing_links:
                        continue

                    futures.append(executor.submit(parse_article, link, title))

                for future in as_completed(futures):
                    result = future.result()
                    if result:
                        print(f'{result["title"]} - {result["link"]}')
    except Exception as e:
        print(f'Ошибка при работе с пагинацией: {e}')
    finally:
        driver.quit()



if __name__ == '__main__':
    web_scrapping()


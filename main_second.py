import time
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fake_useragent import UserAgent
from tqdm import tqdm
import pprint

ua = UserAgent()
user_agent = ua.random
options = webdriver.ChromeOptions()
options.add_argument(f'user-agent={user_agent}')
options.add_argument('--headless')

KEYWORDS = ['дизайн', 'фото', 'web', 'python']
data = []

driver = webdriver.Chrome(options=options)
driver.get('https://habr.com/ru/articles/')
wait = WebDriverWait(driver, 10)

pagination_list = wait.until(
    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a.tm-pagination__page'))
)

pagination_counter = pagination_list[-1]

print(type(pagination_counter.text))
print(pagination_counter.text)

# for page in range(1, int(pagination_counter.text)):
for page in tqdm(range(1, int(pagination_counter.text) + 1), desc="Парсинг страниц", unit="страница"):

    driver.get(f'https://habr.com/ru/articles/page{page}')
    wait_driver = WebDriverWait(driver, 10)

    article_blocks = wait_driver.until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.tm-article-snippet'))
    )

    print(article_blocks)

    for article in article_blocks:
        article_title = article.find_element(By.CSS_SELECTOR, 'h2.tm-title a')
        title = article_title.text
        link = article_title.get_attribute('href')
        # article_preview_description = article.find_element(By.CSS_SELECTOR, 'div.article-formatted-body')

        try:
            article_preview_description = article.find_element(By.CSS_SELECTOR, 'div.tm-article-body p')
            article_preview_formatted_description = article.find_element(By.CSS_SELECTOR, 'div.article-formatted-body p')
            description = article_preview_description.text if article_preview_description.text else article_preview_formatted_description.text
        except NoSuchElementException:
            description = 'Описание не найдено!'

        print(title)
        print(description)

        if any(keyword.lower() in description for keyword in KEYWORDS) or any(keyword.lower() in title for keyword in KEYWORDS):
            data.append(
                {
                    'title': title,
                    'link': link,
                    'description': description
                }
            )

pprint.pp(f'data: {data}')
driver.quit()
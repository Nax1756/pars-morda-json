from bs4 import BeautifulSoup
import requests, os, time, json
from selenium import webdriver
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By


# URL сайта
url = 'https://morda72.ru'
response = requests.get(url)
soup = BeautifulSoup(response.text, 'lxml')

data = []

def get_available(driver=False):
    available = True
    try:
        if driver:
            product_delivery_in_stock = driver.find_element('xpath', "(//ul[contains(@class, 'product-delivery list-unstyled  show-instock')])/li[contains(@class, 'preorder d-flex fl-start t-red')]")
        else:
            product_delivery_in_stock = product_soup.find('ul', class_='product-delivery list-unstyled  show-instock').find('li', class_='preorder d-flex fl-start t-red')
        available=False
        return available
    except:
        pass


def get_price(weight_text=None):
    if weight_text:
        price_text = driver.find_element('xpath', "(//div[contains(@class, 'price-block d-flex fl-ai-end xs-1 sm-3 md-1')])/span[contains(@class, 'price')]").text.replace(" ₽", "").strip()
        available = get_available(True)

    else:
        price_text = product_soup.find('div', class_='price-block d-flex fl-ai-end xs-1 sm-3 md-1').find('span', class_='price').text.replace(" ₽", "").strip()
        available = get_available()


    weight_price = {
        "weight": weight_text,
        "price": price_text,
        "available": available
    }
    weight_prices.append(weight_price)

# кошки, собаки, грызуны...
categories = soup.find('ul', class_='menu-level-1 list-unstyled d-flex fl-m10 fl-ai-start').find_all('li', class_='menu-li-1')
# с [::len(categories) - 1] код парсит только первую и последнюю категории
for category in categories[:4:3]:
    category_href = 'https://morda72.ru' + category.find('a').get('href')
    print(category.find('a').get('href'))
    category_response = requests.get(category_href)
    category_soup = BeautifulSoup(category_response.text, 'lxml')

    category_name = category_soup.find('div', id='product-category').find('h1').text.strip()
    print(f'категория: {category_name} ({category_href})')

    category_dict = {
        "name": category_name,
        "subcategories": []
    }

    data.append(category_dict)

    # корм для кошек, наполнители...
    subcategories = category_soup.find('ul', class_='subcategories-list list-unstyled d-flex fl-wrap').find_all('li', class_='xs-2 sm-3 md-4')
    for subcategory in subcategories[::len(subcategories) - 1]:
        subcategory_href = subcategory.find('a').get('href')
        subcategory_response = requests.get(subcategory_href)
        subcategory_soup = BeautifulSoup(subcategory_response.text, 'lxml')

        subcategory_name = subcategory.find('a').text.strip()
        print(f'подкатегория: {subcategory_name} ({subcategory_href})')

        subcategory_dict = {
            "name": subcategory_name,
            "products": []
        }

        category_dict["subcategories"].append(subcategory_dict)

        # формирование списка страниц
        try:
            paginator = subcategory_soup.find('ul', class_='pagination').find_all('li')[-1].find('a').get('href').split('?page=')
            paginator_list = []
            page_number = 0
            for item in range(int(paginator[1])):
                page_number += 1
                paginator_num = f'{paginator[0]}/?page={page_number}'
                paginator_list.append(paginator_num)

            condition = True

        except Exception as e:
            condition = False

        # на случай если у категории всего 1 страница
        iterable = paginator_list[::len(paginator_list) - 1] if condition else [subcategory_href]
        get_out = False
        previous_href = None

        for page in iterable:

            # ниже есть объяснения почему происходит выход (ctrl+f - "if previous_href")
            if get_out:
                break

            # на случай если у категории всего 1 страница
            page_response = requests.get(page) if condition else requests.get(subcategory_href)

            page_soup = BeautifulSoup(page_response.text, 'lxml')

            if condition:
                page_num = page.split('?page=')[1]
            else:
                page_num = 1
            print(f'Страница: {page_num}')

            products_grid = page_soup.find('div', class_='product-grid d-flex fl-wrap')
            products = products_grid.find_all('div', class_='product-item d-flex fl-column xs-2 sm-3 md-3 xl-4')

            # парс по каждому товару
            for product in products[::len(products) - 1]:
                product_href = product.find('a', class_='product-link').get('href')
                product_response = requests.get(product_href)
                product_soup = BeautifulSoup(product_response.text, 'lxml')

                print(f'Продукт: {product_href}')

                # на самом сайте идет сбой в одной из категорий, поэтому приходиться полностью выходить из парсинга всей кате на этом моменте
                if previous_href == "https://morda72.ru/tovari-dlya-koshek/odejda-koshkam/vodolazka-osso-uteplennaya-dlya-koshek-svetlo-seraya" and product_href == "https://morda72.ru/tovari-dlya-sobak/odezhda-obuv-dlya-sobak/kofta-pet-fashion-style-zvezda":
                    get_out = True
                    break

                title = product_soup.find('div', class_='product-wrapper').find('h1').text.strip()

                # скачивание изображения
                image_path = product_soup.find('div', class_='main-thumb').find('img').get('src')
                img_response = requests.get(image_path)
                filename = title.replace('"', '_').replace('/', '').replace('<', '').replace('>', '').replace(':', '').replace('\\', '').replace('|', '').replace('?', '').replace('*', '')
                filename = filename.rstrip('. ').replace('.', '_')
                with open(os.path.join('images/', filename + '.svg'), 'wb') as f:
                    f.write(img_response.content)

                # код
                code_tag = product_soup.find('div', class_='product-model')
                code = code_tag.text.replace('Код Товара: ', '').strip()

                # атрибуты
                attributes_ul = product_soup.find('ul', class_='product-attributes list-unstyled d-flex fl-wrap sm-hidden')
                attributes_li = attributes_ul.find_all('li', class_='d-flex fl-ai-start xs-1') if attributes_ul else []
                attribute_dict = {}
                for item in attributes_li:
                    name_tag = item.find('div', class_='attribute-name-wrapper d-flex fl-ai-end xs-2')
                    text_tag = item.find('div', class_='attribute-text xs-2')
                    if name_tag and text_tag:
                        attribute_name = name_tag.find('span', class_='attribute-name').text.strip()
                        attribute_text = text_tag.text.strip()
                        attribute_dict[attribute_name] = attribute_text

                # описание
                description_tag = product_soup.find('div', id='tab-description')
                description = description_tag.text.strip() if description_tag else ""

                # теги
                tags_div = product_soup.find('div', class_='tags')
                tags_a = tags_div.find_all('a') if tags_div else []
                tag_list = [tag.text.strip() for tag in tags_a]



                # вес\цена
                weight_prices = []

                # if "есть выборка между весами"
                if product_soup.find('div', class_='options-block d-flex fl-wrap fl-ai-center fl-m7'):
                    max_attempts = 2
                    for attempt in range(max_attempts):
                        try:
                            #driver
                            gecko_driver_path = GeckoDriverManager().install()
                            service = Service(executable_path=gecko_driver_path)
                            driver = webdriver.Firefox(service=service)
                            driver.get(product_href)
                            print('driver ON')

                            weight_btns = driver.find_elements(By.XPATH, "//div[contains(@class, 'options-block d-flex fl-wrap fl-ai-center fl-m7')]/label[contains(@class, 'radio2')]")
                            for weight_btn in weight_btns:
                                weight_text = weight_btn.text.strip()
                                weight_btn.click()
                                time.sleep(1)

                                get_price(weight_text)

                            driver.quit()
                            print('driver OFF')
                            break

                        except Exception as e:
                            print(f"ошибка - {str(e)}")
                            try:
                                driver.quit()
                            except:
                                pass
                            if attempt < max_attempts - 1:
                                print(f"повторная попытка ({attempt + 1}/{max_attempts})")
                                time.sleep(2)
                            else:
                                print("максимальное количество попыток исчерпано.")
                                raise

                else:
                    get_price()

                product_dict = {
                    "title": title,
                    "image": filename,
                    "href": product_href,
                    "code": code,
                    "attributes": attribute_dict,
                    "description": description,
                    "tags": tag_list,
                    "weight_prices": weight_prices
                }


                subcategory_dict["products"].append(product_dict)
                previous_href = product_href


with open('scraped_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print("сохранение данных авершено.")

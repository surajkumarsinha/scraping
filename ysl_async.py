import aiohttp
import asyncio
from bs4 import BeautifulSoup
import pandas as pd

# Constants
url_param = "?start=0&sz=100"
headers = {'user agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36'}


class WebScraper(object):

    def __init__(self, base_url, beauty_products):
        self.base_url = base_url
        self.beauty_products = beauty_products
        self.product_list = []
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            print('Async event loop already running. Adding coroutine to the event loop.')
            task = loop.create_task(self.scrape_main())
        else:
            print('Starting new event loop')
            result = asyncio.run(self.scrape_main())

    async def runner(self):
        await self.scrape_main()

    async def extract_product_list_info(self, text):
        instance = BeautifulSoup(text, 'html.parser')
        for product in instance.find_all('div', attrs={'class':'c-product-tile__wrapper'}):
            try:
                product_title = product.find('h2', attrs={'class':'c-product-tile__name'})
                product_price = product.find(lambda s: s.name == 'span' and s.get('class') == ['c-product-price__value'])
                product_instance = {}
                product_instance['name'] = product_title.text
                product_instance['href'] = product_title.find('a').attrs['href']
                product_instance['price'] = product_price.text.strip()
                self.product_list.append(product_instance)
            except:
                pass

    async def scrape_main_pages(self, session, url):
        try:
            async with session.get(url) as response:
                text = await response.text()
                # Extract Info on the main pages
                await self.extract_product_list_info(text)
                return text
        except Exception as e:
            print(str(e))

    async def scrape_main(self):
        tasks = []
        async with aiohttp.ClientSession(headers=headers) as session:
            for prods in beauty_products:
                url = self.base_url + prods + "/?start=0&sz=100"
                tasks.append(self.scrape_main_pages(session, url))
            await asyncio.gather(*tasks)
        print(len(self.product_list))

    async def scrape_product_list(self):
        tasks = []
        async with aiohttp.ClientSession(headers=headers) as session:
            for prod in self.product_list:
                url = self.base_url + prod['href']
                tasks.append(self.scrape_product(session, url, prod))
            await asyncio.gather(*tasks)

    async def scrape_product(self, session, url, prod):
        try:
            async with session.get(url) as response:
                text = await response.text()
                # Extract Info on the main pages
                await self.extract_product_info(text, prod)
                return text
        except Exception as e:
            print(str(e))

    async def extract_product_info(self, text, product_instance):
        product_soup_instance = BeautifulSoup(text, 'html.parser')
        try:
            product_instance['how_to_apply'] = product_soup_instance.find('div', attrs={
                "data-tab-hash": 'how-to-apply'}).text.strip()
        except:
            pass
        try:
            product_instance['ingredients'] = product_soup_instance.find('div', attrs={
                "data-tab-hash": 'ingredients'}).text.strip()
        except:
            pass
        try:
            # product_instance['description'] = product_soup_instance.find('div',attrs={"data-tab-hash":'description'})
            product_description = product_soup_instance.find('div', attrs={"data-tab-hash": 'description'})
            for description_keys in product_description.find_all('div', attrs={'class': 'subsection_wrapper'}):
                if description_keys.find('span').text == 'Type':
                    product_instance['description'] = description_keys.find('p').text.strip()
        except:
            pass
        pass

    def get_product_list(self):
        return self.product_list


if __name__ == '__main__':
    base_url = "https://www.yslbeautyus.com/"
    beauty_products = ["makeup", "fragrance", "skincare"]
    scraper = WebScraper(base_url=base_url, beauty_products=beauty_products)
    asyncio.run(scraper.scrape_product_list())
    pd.DataFrame(scraper.get_product_list()).to_excel("ysl.xlsx")


# See PyCharm help at https://www.jetbrains.com/help/pycharm/

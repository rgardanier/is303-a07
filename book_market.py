'''
book market analysis

inputs: books.toscrape.com
processes: scrape book listings, store in SQLite via Peewee, query and analyze with Pandas, create a chart
outputs: printed analysis, chart, book_market.db
'''
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
import requests, time
from peewee import SqliteDatabase, Model, CharField, FloatField, IntegerField

db = SqliteDatabase('book_market.db')

RATING_WORDS = {'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5}

class Book(Model):
    title = CharField(unique=True)
    price = FloatField()
    rating = IntegerField()

    class Meta:
        database = db

def scrape_books(num_pages=3):
    books = []
    for page in range(1, num_pages +1):
        base_url = f'http://books.toscrape.com/catalogue/page-{page}.html'
        soup = fetch_url(base_url)
        if soup is None:
            continue
        for article in soup.find_all('article', class_='product_pod'):
            title = article.h3.a['title']
            price = article.find('p', class_='price_color').text 
            rating = article.find('p', class_='star-rating')['class'][1] # get the second class for rating
            books.append({'title': title, 'price': price, 'rating': rating})
        time.sleep(1)
    return books


def fetch_url(url):
    response = requests.get(url)
    if response.status_code == 200:
        return BeautifulSoup(response.text, 'html.parser')
    else:
        print(f'Failed to fetch {url}')
        return None


def store_books(books):
    new_count = 0
    for book in books:
        clean_price = ''
        for c in book['price']:
            if c.isdigit() or c == '.':
                clean_price += c
        price_num = float(clean_price)

        rating_num = RATING_WORDS[book['rating']]

        if not Book.select().where(Book.title == book['title']).exists():
            Book.create(title=book['title'], price=price_num, rating=rating_num)
            new_count += 1

    print(f"Stored {new_count} new books")


def analyze():
    query = Book.select()
    df = pd.DataFrame(list(query.dicts()))

    total = len(df)
    avg_price = df['price'].mean()
    most_expensive = df.loc[df['price'].idxmax()]
    least_expensive = df.loc[df['price'].idxmin()]

    avg_by_rating = df.groupby('rating')['price'].mean()

    print('=====Analytics=====')
    print(f"Total books in database: {total}")
    print(f"Average Price Overall: ${avg_price:.2f}")
    print(f"Most expensive Book: {most_expensive['title']} ${most_expensive['price']:.2f}")
    print(f"Least Expensive Book: {least_expensive['title']} ${least_expensive['price']:.2f}")
    print("\nAverage price by star rating")
    print(avg_by_rating.round(2))

    return df


def visualize(df):
    avg_by_rating = df.groupby('rating')['price'].mean()

    plt.figure(figsize=(8, 5))
    plt.bar(avg_by_rating.index, avg_by_rating.values)

    plt.title('Average Book Price by Rating')
    plt.xlabel("Star Rating")
    plt.ylabel("Average Price ($)")

    plt.savefig('price_chart.png')
    print("\nChart saved as price_chart.png")
    
def main():
    db.connect()
    db.create_tables([Book])

    books = scrape_books(3)
    print(f"Scraped {len(books)} books:")
    store_books(books)

    df = analyze()
    visualize(df)


main()
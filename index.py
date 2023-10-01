import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By

PRINT_SCROLL_LOGS_MODIFIER = 20
TOTAL_THRESHOLD = 5
MAX_SCROLLS = 5000
#MAX_SCROLLS = 2

ZONES = [
    # { zone: "Mumbai MUM Andheri East", subzone: "JB Nagar metro station", url: "https://www.zomato.com/mumbai/delivery-in-chakala?delivery_subzone=9854&place_name=Jb+Nagar+Metro+Station%2C++Shaheed+Bhagat+Singh+Society%2C++S+B+Singh+Colony" }
    { "zone": "Mumbai MUM Thane East", "subzone": "Korum mall", "url": "https://www.zomato.com/mumbai/delivery-in-wagle-estate-thane-west?delivery_subzone=8268&place_name=Korum+Mall+Parking%2C++Samata+Nagar%2C++Thane+West" }
]

def log(data):
    print(data)

browser = webdriver.Chrome()

for zoneEntry in ZONES:

    startTime = time.time()

    zone = zoneEntry['zone']
    subzone = zoneEntry['subzone']
    url = zoneEntry['url']

    log(f"Scraping {zone}, {subzone}")

    browser.get(url)

    time.sleep(7)

    log(">>>> Scrolling to Delivery Restaurants Section")
    # Scroll to Delivery Restaurants section
    browser.execute_script('''
       const xpathResult = document.evaluate(
         "//h1[contains(., 'Delivery Restaurants')]",
           document,
         null,
         XPathResult.ORDERED_NODE_ITERATOR_TYPE,
         null
       );
       const deliveryRestaurantHeading = xpathResult.iterateNext();
       deliveryRestaurantHeading.scrollIntoView();
    ''')
    log(">>>> DONE: Scrolling to Delivery Restaurants Section")


    # TODO: Scan first 3 sections seperately

    # Scroll to last enabled restaurant
    time.sleep(3)

    log('>>>> Starting automatic scroll to end')
    restaurantData = []
    numScrolls = 0

    while(True):
        if numScrolls > MAX_SCROLLS:
            log('>>> >>> MAX_SCROLLS number of scrolls completed. Exiting loop')
            break

        disabledRestaurantsCount = browser.execute_script("return document.getElementsByClassName('jgMwFA').length");
        if disabledRestaurantsCount > TOTAL_THRESHOLD:
            log('>>> >>> TOTAL_THRESHOLD number of restaurants found. Exiting loop')
            break
        else:
            if numScrolls % PRINT_SCROLL_LOGS_MODIFIER == 0:
                log(f'>>> >>> Still Scrolling. Scrolls: {numScrolls}')
            time.sleep(1)
            browser.execute_script("window.scrollBy(0, 400)")
            numScrolls = numScrolls + 1

    log('>>>> DONE: Starting automatic scroll to end')

    browser.execute_script('''
        restaurantCards = document.getElementsByClassName('jgMwFA');
        if (restaurantCards) {
            restaurantCards[restaurantCards.length - 1].scrollIntoView({ behaviour: "smooth" })
            window.scrollBy(0, -650)
        }
    ''')
    browser.save_screenshot(f'screenshots/{zone}_{subzone}.png');

    data = browser.execute_script('''restaurantCards = document.getElementsByClassName('sc-dzOgQY');
    restaurantData = Array.from(restaurantCards).map((card) => {
        const cuisine = card.getElementsByClassName('sc-fGSyRc eWQqcH')?.[0];
        const name = card.getElementsByClassName('flnmvC')?.[0];
        const offer = card.getElementsByClassName('sc-ijnzTp bbfjcv')?.[0];
        const url = card.querySelector('a');

        return {
            name: name?.innerText,
            offer: offer?.innerText,
            cuisine: cuisine?.innerText,
            url: url?.href
        }
    });
    return restaurantData;
    ''') 
    restaurantData.extend(data)

    restaurantDataDf = pd.DataFrame(restaurantData)
    restaurantDataDf.to_csv(f"results/restaurants_{zone}_{subzone}.csv", index=False)

    endTime = time.time()
    duration = (endTime-startTime) * 10**3
    log(f"Completed {zone}, {subzone} in {duration} ms")
    time.sleep(10)


from seleniumwire import webdriver
from selenium.webdriver.common.by import By
import re

def detect_season(episode_titles):
    season_pattern = re.compile(r'Season (\d+)')
    seasons = set()
    for title in episode_titles:
        match = season_pattern.search(title)
        if match:
            seasons.add(int(match.group(1)))
    
    # if seasons were detected but Season 1 is missing, add it
    if seasons and 1 not in seasons:
        seasons.add(1)
    
    # if no seasons were detected at all, assume all episodes are from season 1
    if not seasons:
        seasons.add(1)
    
    return list(sorted(seasons))

def fetchLinks(cartoon_url):
    '''Fetches the episode links and detects seasons from given URL'''
    if not isinstance(cartoon_url, str):
        return "error: cartoon_url must be a string"
    
    options = webdriver.FirefoxOptions()
    options.add_argument("-headless")
    print(">> running selenium in headless mode")
    driver = webdriver.Firefox(options=options)

    driver.get(cartoon_url)

    # fetching user agent
    for request in driver.requests:
        if request.response:
            useragent = request.headers["User-Agent"]
            break

    try:
        sidebar_right3_div = driver.find_element(By.XPATH, '//*[@id="sidebar_right3"]')
        child_divs = sidebar_right3_div.find_elements(By.XPATH, './/*')

        links = []
        episode_titles = []
        for div in child_divs:
            div_links = div.find_elements(By.TAG_NAME, 'a')
            for link in div_links:
                href = link.get_attribute('href')
                title = link.text
                links.append(href)
                episode_titles.append(title)

        links = links[::-1]  # reversing the list for the actual episode order
        episode_titles = episode_titles[::-1]

        # detect seasons
        seasons = detect_season(episode_titles)
        cartoon_name = driver.find_element(By.XPATH, '/html/body/div[3]/div/div/div[1]/div[1]/h1/div/a').text

        cartoon_name_new = ''.join([char for char in cartoon_name if char not in r'\/:*?"<>|']) # remove specific symbols to avoid windows directory name errors

        return links, useragent, seasons, episode_titles, cartoon_name_new
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return None, None, None, None, None
    finally:
        driver.quit()
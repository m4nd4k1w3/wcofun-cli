import os
import sys
import time
import re
import argparse
import logging
from helpers.fetchEpisodes import fetchLinks
from helpers.dlVideo import download_video

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def download_episode(url: str, filename: str, directory: str, useragent: str, episode_number: int, episode_count: int) -> bool:
    logging.info(f"Preparing to download {filename} from this link: {url}")
    start_timer = time.time()
    if download_video(url, f"{filename}.mp4", directory, useragent):
        end_timer = time.time()
        logging.info(f"{filename} downloaded successfully. {episode_number}/{episode_count} ({round(end_timer - start_timer, 2)} seconds)")
        return True
    else:
        logging.error(f"Error: {filename} failed to download. Moving on...")
        return False

def process_season(season: int, season_links: list, directory: str, useragent: str, episode_titles: list) -> list:
    episode_count = len(season_links)
    logging.info(f"There are {episode_count} episodes in season {season}")

    # Initial download of all episodes
    for episode_number, (url, title) in enumerate(zip(season_links, episode_titles), start=1):
        filename = f"S{season}E{episode_number:02d}"
        if not os.path.exists(os.path.join(directory, f"{filename}.mp4")):
            download_episode(url, filename, directory, useragent, episode_number, episode_count)

    # Check for missing episodes after download
    existing_files = os.listdir(directory)
    existing_episodes = [int(file.split('E')[1].split('.')[0]) for file in existing_files if file.endswith('.mp4')]
    existing_episodes.sort()

    all_episodes = set(range(1, episode_count + 1))
    missing_episodes = list(all_episodes - set(existing_episodes))
    missing_episodes.sort()

    if missing_episodes:
        missing_episodes_formatted = [f"S{season}E{episode:02d}" for episode in missing_episodes]
        logging.warning(f"Found {len(missing_episodes)} missing episodes after download: {', '.join(missing_episodes_formatted)}")
        download_missing = input("Do you want to try downloading these missing episodes again? (y/n): ")
        if download_missing.lower() == 'y':
            for episode_number in missing_episodes:
                filename = f"S{season}E{episode_number:02d}"
                url = season_links[episode_number - 1]
                download_episode(url, filename, directory, useragent, episode_number, episode_count)
        else:
            logging.info("Skipping missing episodes...")
    else:
        logging.info("All episodes downloaded successfully.")

    return missing_episodes_formatted if missing_episodes else []

def main():
    parser = argparse.ArgumentParser(description="Download episodes of a cartoon.")
    parser.add_argument("cartoon_url", help="URL of the cartoon to download")
    args = parser.parse_args()
    cartoon_url = args.cartoon_url

    logging.info("Fetching episode links and detecting seasons...")
    fetch_result = fetchLinks(cartoon_url)
    if fetch_result is None or len(fetch_result) != 5:
        logging.error("Failed to fetch episode links or detect seasons.")
        sys.exit(1)

    links, useragent, available_seasons, episode_titles, cartoon_name = fetch_result

    if not available_seasons:
        logging.error("Failed to fetch seasons.")
        sys.exit(1)

    logging.info(f"Available seasons: {available_seasons}")

    start_season = int(input("Please input the starting season you want to download: "))
    end_season = int(input("Please input the ending season you want to download: "))

    # Validate input
    if end_season > max(available_seasons):
        logging.warning(f"Ending season cannot be more than {max(available_seasons)}. Setting ending season value to {max(available_seasons)}.")
        end_season = max(available_seasons)

    if end_season < start_season:
        logging.error("Ending season cannot be less than the starting season.")
        sys.exit(1)

    if start_season < min(available_seasons):
        logging.warning(f"Starting season cannot be less than {min(available_seasons)}. Setting starting season value to {min(available_seasons)}.")
        start_season = min(available_seasons)

    all_missing_episodes = []

    # Loop through each season in the specified range
    for season in range(start_season, end_season + 1):
        if season not in available_seasons:
            logging.info(f"Season {season} not available. Skipping...")
            continue

        logging.info(f"Downloading season {season}")

        # Create directory to download the episodes into
        if not os.path.exists(cartoon_name):
            os.makedirs(cartoon_name)

        directory = f"{cartoon_name}/S{season}"
        if not os.path.exists(directory):
            logging.info(f"Creating directory for season {season}")
            os.makedirs(directory)

        logging.info("Fetching the episode links")
        season_pattern = re.compile(f'Season {season}' if season != 1 else r'(?!Season [2-9])')
        season_links = [link for link, title in zip(links, episode_titles) if season_pattern.search(title)]
        season_episode_titles = [title for title in episode_titles if season_pattern.search(title)]

        missing_episodes = process_season(season, season_links, directory, useragent, season_episode_titles)
        all_missing_episodes.extend(missing_episodes)

        logging.info(f"Season {season} downloaded successfully.")

    if all_missing_episodes:
        logging.warning(f"Missing episodes: {', '.join(all_missing_episodes)}")
    else:
        logging.info("All episodes from all seasons downloaded successfully.")

    logging.info("All desired seasons downloaded successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()

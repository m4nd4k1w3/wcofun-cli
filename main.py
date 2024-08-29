from helpers.fetchEpisodes import fetchLinks
from helpers.dlVideo import download_video
import os
import sys
import time
import re
import argparse

def download_episode(url, filename, directory, useragent, episode_number, episode_count):
    print(f">> preparing to download {filename} from this link: {url}")
    start_timer = time.time()
    if download_video(url, f"{filename}.mp4", directory, useragent):
        end_timer = time.time()
        print(f">> {filename} downloaded successfully. {episode_number}/{episode_count} ({round(end_timer - start_timer, 2)} seconds)\n")
        return True
    else:
        print(f">> error: {filename} failed to download. moving on...\n")
        return False

def process_season(season, season_links, directory, useragent, episode_titles):
    episode_count = len(season_links)
    print(f">> there are {episode_count} episodes in season {season}")

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
        print(f">> Found {len(missing_episodes)} missing episodes after download:")
        print(f">> Missing episodes: {', '.join(missing_episodes_formatted)}")
        download_missing = input(">>> Do you want to try downloading these missing episodes again? (y/n): ")
        if download_missing.lower() == 'y':
            for episode_number in missing_episodes:
                filename = f"S{season}E{episode_number:02d}"
                url = season_links[episode_number - 1]
                download_episode(url, filename, directory, useragent, episode_number, episode_count)
        else:
            print(">> Skipping missing episodes...")
    else:
        print(">> All episodes downloaded successfully.")

    return missing_episodes_formatted if missing_episodes else []

def main():
    parser = argparse.ArgumentParser(description="Download episodes of a cartoon.")
    parser.add_argument("cartoon_url", help="URL of the cartoon to download")

    args = parser.parse_args()
    cartoon_url = args.cartoon_url

    print("\n===========")
    print("wcofun-cli")
    print("===========\n")

    print(">> fetching episode links and detecting seasons...")
    fetch_result = fetchLinks(cartoon_url)
    if fetch_result is None or len(fetch_result) != 5:
        print(">> error: failed to fetch episode links or detect seasons.")
        sys.exit(1)

    links, useragent, available_seasons, episode_titles, cartoon_name = fetch_result

    if not available_seasons:
        print("error: failed to fetch seasons.")
        sys.exit(1)

    print(f">> available seasons: {available_seasons}\n")

    start_season = int(input(">>> please input the starting season you want to download: "))
    end_season = int(input(">>> please input the ending season you want to download: "))

    print() # newline

    # validate input
    if end_season > max(available_seasons):
        print(f">> error: ending season cannot be more than {max(available_seasons)}. Setting ending season value to {max(available_seasons)}...")
        end_season = max(available_seasons)

    if end_season < start_season:
        print(">> error: ending season cannot be less than the starting season.")
        sys.exit(1)

    if start_season < min(available_seasons):
        print(f">> error: starting season cannot be less than {min(available_seasons)}. Setting starting season value to {min(available_seasons)}...")
        start_season = min(available_seasons)

    all_missing_episodes = []

    # loop through each season in the specified range
    for season in range(start_season, end_season + 1):
        if season not in available_seasons:
            print(f">> Season {season} not available. Skipping...")
            continue

        print(f">> downloading season {season}")

        # create directory to download the episodes into
        if not os.path.exists(cartoon_name): 
            os.makedirs(cartoon_name)

        directory = f"{cartoon_name}/S{season}"
        if not os.path.exists(directory):
            print(f">> creating directory for season {season}")
            os.makedirs(directory)

        print(">> fetching the episode links")
        if season == 1:
            # for season 1, include episodes without a season number and exclude episodes from other seasons
            season_pattern = re.compile(r'(?!Season [2-9])')
        else:
            season_pattern = re.compile(f'Season {season}')
        
        season_links = [link for link, title in zip(links, episode_titles) if season_pattern.search(title)]
        season_episode_titles = [title for title in episode_titles if season_pattern.search(title)]
        
        missing_episodes = process_season(season, season_links, directory, useragent, season_episode_titles)
        all_missing_episodes.extend(missing_episodes)

        print(f"\n>> Season {season} downloaded successfully.\n")

    if all_missing_episodes:
        print(f">> missing episodes: {', '.join(all_missing_episodes)}")
    else:
        print(">> All episodes from all seasons downloaded successfully.")

    print("All desired seasons downloaded successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()
from helpers.fetchEpisodes import fetchLinks
from helpers.dlVideo import download_video
import os
import sys
import time
import re
import argparse

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
        else:
            choose = input(f">>> there is a directory named 'S{season}'. would you want to overwrite it? (y/n): ")
            if choose.lower() != "y":
                print(">> skipping this season...")
                continue

        print(">> fetching the episode links")
        if season == 1:
            # for season 1, include episodes without a season number and exclude episodes from other seasons
            season_pattern = re.compile(r'(?!Season [2-9])')
        else:
            season_pattern = re.compile(f'Season {season}')
        
        season_links = [link for link, title in zip(links, episode_titles) if season_pattern.search(title)]
        episode_count = len(season_links)
        print(f">> there are {episode_count} episodes in season {season}")

        # scan the directory for existing episode files
        existing_files = os.listdir(directory)
        existing_episodes = [int(file.split('E')[1].split('.')[0]) for file in existing_files if file.endswith('.mp4')]
        existing_episodes.sort()
        
        # determine the starting episode number
        if existing_episodes:
            start_episode = existing_episodes[-1] + 1
            print(f">> resuming download from episode {start_episode}")
        else:
            start_episode = 1

        # download remaining episodes
        for i in range(start_episode - 1, len(season_links)):
            episode_number = i + 1
            filename = f"S{season}E{episode_number:02d}"
            url = season_links[i]
            
            print(f">> preparing to download {filename} from this link: {url}")
            start_timer = time.time()
            if download_video(url, f"{filename}.mp4", directory, useragent):
                end_timer = time.time()
                print(f">> {filename} downloaded successfully. {episode_number}/{episode_count} ({round(end_timer - start_timer, 2)} seconds)\n")
            else:
                print(f">> error: {filename} failed to download. moving on...\n")

        print(f"\n>> Season {season} downloaded successfully.\n")

    print("All desired seasons downloaded successfully.")
    sys.exit(1)

if __name__ == "__main__":
    main()
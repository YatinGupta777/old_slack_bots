import json
import os
import pickle
from slack import WebClient
from slack.errors import SlackApiError
from git import Repo
import git
import re
import urllib
from datetime import datetime, timedelta
import requests

slack_channel = os.getenv('SLACK_CHANNEL')
repo_path = './'
branch_name = 'origin/master'
bot_token = os.getenv('API_USER')
git_cmd_runner = git.cmd.Git(repo_path)
client = WebClient(token=bot_token)


# Read previous contributors names
def read_old_state():

    previous_contributors_file = 'cache/previous_contributors.txt'
    previous_contributors = []
    if os.path.exists(previous_contributors_file):
        with open(previous_contributors_file, 'r') as fp:
            for line in fp:
                previous_contributors.append(line[:-1])

    return previous_contributors


# Read number of md files present in directory
def read_current_state():

    current_md_files = 0

    path = "docs"
    for root, directories, files in os.walk(path):
        for file in files:
            if file.endswith('.md'):
                current_md_files += 1

    return current_md_files


def find_new_contributors(previous_contributors, last_week_contributors):
    new_contributors = []

    for i in last_week_contributors:
        if not i in previous_contributors:
            new_contributors.append(i)

    return new_contributors


def get_last_week_commits():
    repo = Repo(repo_path)
    commits = []
    # check that the repository loaded correctly
    if not repo.bare:
        print('Repo at {} successfully loaded.'.format(repo_path))

        # Get 1 week ago commits
        last_week_commits = git_cmd_runner.execute(
            ['git', 'log', 'origin/master', '--after=1 week ago'])
        last_week_commits = last_week_commits.split("commit")
        # Removing empty space
        del last_week_commits[0]
        commits = list(repo.iter_commits(
            branch_name, max_count=len(last_week_commits)))
        commits.reverse()
    else:
        print('Could not load repository at {} :('.format(repo_path))

    return commits


def get_last_week_contributors():

    last_week_contributors = git_cmd_runner.execute(
        ['git', 'shortlog', 'origin/master', '-se', '--after=1 week ago'])

    last_week_contributors = last_week_contributors.split("\n")
    last_week_contributors = [i[i.find("<")+1:i.find(">")] for i in last_week_contributors]
    if '' in last_week_contributors:
        last_week_contributors.remove('')
    return last_week_contributors


# Get added and modified files in last week
def get_last_week_files():
    new_added_files = []
    new_modified_files = []
    commits = get_last_week_commits()
    for commit in commits:
        if not commit.summary.startswith("Merge branch"):
            # Git command to show file changes in a commit
            files = git_cmd_runner.execute(
                ["git", "diff-tree", "--no-commit-id", "--name-status", "-r", commit.hexsha])
            files = re.sub(r'\t', '', files)
            files = files.split("\n")

            for file in files:
                if(file.startswith("A") and file.endswith(".md")):
                    file = file[1:]
                    if(file.startswith("docs")):
                        new_added_files.append(file)
                elif(file.startswith("M") and file.endswith(".md")):
                    file = file[1:]
                    # Removing duplicates
                    if file not in new_added_files and file not in new_modified_files and file.startswith("docs"):
                        new_modified_files.append(file)

    return new_added_files, new_modified_files


# Save current contributors
def write_current_state(current_contributors):

    with open('cache/previous_contributors.txt', 'w') as fp:
        for i in current_contributors:
            fp.write(i + "\n")


def get_authors_streak(last_week_contributors):
    last_week_contributors_streaks = {}

    for contributor in last_week_contributors:
        last_week_contributors_streaks[contributor] = 0

        commit_dates = git_cmd_runner.execute(
            ["git", "log", "origin/master", "--format=%ci", "--author=" + contributor, "--use-mailmap"])

        if commit_dates != '':

            commit_dates = commit_dates.split("\n")

            for (idx, val) in enumerate(commit_dates):
                x = val.split(' ')[0]
                x += ' '
                x += val.split(' ')[1]
                commit_dates[idx] = datetime.fromisoformat(x)

            streak_running = True
            repo_start_date = datetime(2020, 6, 25)
            start_date = datetime.today() - timedelta(days=7)
            end_date = datetime.now()

            while(start_date >= repo_start_date and streak_running):

                streak_running = any(
                    date.date() >= start_date.date() and date.date() <= end_date.date() for date in commit_dates)

                if(streak_running):
                    last_week_contributors_streaks[contributor] += 1

                end_date = start_date
                start_date = end_date - timedelta(days=7)

    return last_week_contributors_streaks

# Get names from slack to avoid mismatches
def get_name_from_email(email):

    response = requests.post(
        "https://slack.com/api/users.lookupByEmail", {"token": bot_token, "email": email})
    data = json.loads(response.content)
    if(data['ok']):
        return data['user']['real_name']

    return email

def send_message_to_slack(new_contributors_with_names, new_added_files, new_modified_files, wiki_growth_percentage, last_week_contributors_streaks_with_names):

    new_added_files = [f.replace('docs/', '') for f in new_added_files]
    new_added_files = [f.replace('.md', '') for f in new_added_files]

    new_added_files_with_links = []
    for i in new_added_files:
        link = "https://wiki.hyperverge.co/" + urllib.parse.quote(i) + ".html"
        new_added_files_with_links.append("<" + link + "|" + i + ">")

    new_added_files_with_links = [
        ':white_small_square: ' + f for f in new_added_files_with_links]

    new_modified_files = [f.replace('docs/', '') for f in new_modified_files]
    new_modified_files = [f.replace('.md', '') for f in new_modified_files]

    new_modified_files_with_links = []
    for i in new_modified_files:
        link = "https://wiki.hyperverge.co/" + urllib.parse.quote(i) + ".html"
        new_modified_files_with_links.append("<" + link + "|" + i + ">")

    new_modified_files_with_links = [
        ':white_small_square: ' + f for f in new_modified_files_with_links]

    new_contributors_message = ''
    last_week_contributors_message = ''
    new_added_files_message = ''
    new_modified_files_message = ''
    wiki_growth_percentage_message = ''

    new_contributors_image = ''
    last_week_contributors_image = ''
    wiki_growth_percentage_image = ''

    if(len(new_contributors_with_names) > 0):
        new_contributors_message = '*New Contributors*\n:star: ' + \
            '\n:star: '.join(new_contributors_with_names)
        new_contributors_image = 'https://files.slack.com/files-pri/T04CAHQGR-F01AE0JTD42/welcome.png?pub_secret=3c964d9f91'
    else:
        new_contributors_message = 'No new contributors :sad_parrot: '
        new_contributors_image = 'https://files.slack.com/files-pri/T04CAHQGR-F01AE0LMNRY/image.png?pub_secret=9a81d8a673'

    # Sort last week contributors by streak in ascending order
    last_week_contributors_streaks_with_names = {key: value for key, value in sorted(last_week_contributors_streaks_with_names.items(), key=lambda item: item[1])}
    
    if(len(last_week_contributors_streaks_with_names) > 0):
        last_week_contributors_message = '*Contributors this week*\n'

        for i in last_week_contributors_streaks_with_names:
            last_week_contributors_message += ":star: " + i + " "

            if(last_week_contributors_streaks_with_names[i] <= 1):
                last_week_contributors_message += " (" + str(
                    last_week_contributors_streaks_with_names[i]) + " week streak :red_car:)"+"\n"

            if(last_week_contributors_streaks_with_names[i] >= 2 and last_week_contributors_streaks_with_names[i] <= 3):
                last_week_contributors_message += " (" + str(
                    last_week_contributors_streaks_with_names[i]) + " weeks streak :racing_car:)"+"\n"

            if(last_week_contributors_streaks_with_names[i] >= 4 and last_week_contributors_streaks_with_names[i] <= 5):
                last_week_contributors_message += " (" + str(
                    last_week_contributors_streaks_with_names[i]) + " weeks streak :railway_car:)"+"\n"

            if(last_week_contributors_streaks_with_names[i] > 5):
                last_week_contributors_message += " (" + str(
                    last_week_contributors_streaks_with_names[i]) + " weeks streak :rocket:)"+"\n"

        last_week_contributors_image = "https://files.slack.com/files-pri/T04CAHQGR-F019G1VU02J/contribution.png?pub_secret=008fc9a42c"
    else:
        last_week_contributors_message = 'No contributors this week :sad_parrot: '
        last_week_contributors_image = 'https://files.slack.com/files-pri/T04CAHQGR-F019Z7VMAKH/sad-git.png?pub_secret=8304e1c3df'

    if(len(new_added_files) > 0):
        new_added_files_message = '*New Additions*:pencil:\n' + \
            '\n'.join(new_added_files_with_links)
    else:
        new_added_files_message = 'No new additions :sad_parrot: '

    if(len(new_modified_files) > 0):
        new_modified_files_message = '*New Modifications*\n' + \
            '\n'.join(new_modified_files_with_links)
    else:
        new_modified_files_message = 'No new modifications :sad_parrot: '

    if(wiki_growth_percentage > 5):
        wiki_growth_percentage_message = '*Wiki Growth this week *\n' + \
            str(wiki_growth_percentage) + \
            "% !"
        wiki_growth_percentage_image = 'https://files.slack.com/files-pri/T04CAHQGR-F01A1CHVDRP/image.png?pub_secret=18784e7658'
    else:
        wiki_growth_percentage_message = '*Wiki Growth this week *\n' + \
            str(wiki_growth_percentage) + "%  :/ "
        wiki_growth_percentage_image = 'https://files.slack.com/files-pri/T04CAHQGR-F019P12VD3M/image.png?pub_secret=cbeb0cb336'

    # How to add image in msg : https://stackoverflow.com/questions/58186399/how-to-create-a-slack-message-containing-an-uploaded-image/58189401#58189401

    divider = {
        "type": "divider"
    }
    heading = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "Hey Everyone, This is the weekly <https://hvlabs.gitlab.io/engineering-wiki|*Engineering Wiki*> update !!"
        }
    }
    new_contributor_section = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": new_contributors_message
        },
        "accessory": {
            "type": "image",
            "image_url": new_contributors_image,
            "alt_text": "Contribution"
        }
    }
    last_week_contributors_section = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": last_week_contributors_message
        },
        "accessory": {
            "type": "image",
            "image_url": last_week_contributors_image,
            "alt_text": "Contribution"
        }
    }
    new_added_files_section = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": new_added_files_message
        },
        "accessory": {
            "type": "image",
            "image_url": "https://files.slack.com/files-pri/T04CAHQGR-F019P08GXMH/articles.png?pub_secret=353050d0c2",
            "alt_text": "Additions"
        }
    }
    new_modified_files_section = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": new_modified_files_message
        },
    }
    wiki_growth_percentage_section = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": wiki_growth_percentage_message
        },
        "accessory": {
            "type": "image",
            "image_url": wiki_growth_percentage_image,
            "alt_text": "Growth"
        }
    }

    entire_block = [divider,
                    heading,
                    divider,
                    new_contributor_section,
                    last_week_contributors_section,
                    new_added_files_section,
                    new_modified_files_section,
                    divider,
                    wiki_growth_percentage_section, divider]

    try:
        client.chat_postMessage(
            channel=slack_channel,
            icon_url="https://files.slack.com/files-pri/T04CAHQGR-F01A3RPBLRF/bot.png?pub_secret=8cce67fe05",
            blocks=entire_block
        )
    except SlackApiError as e:
      # You will get a SlackApiError if "ok" is False
        print(e)
        assert e.response["error"]


def main():
    current_contributors = {}
    current_md_files = 0

    previous_contributors = {}

    last_week_contributors = get_last_week_contributors()
    last_week_contributors_streaks = get_authors_streak(last_week_contributors)

    previous_contributors = read_old_state()
    current_md_files = read_current_state()

    new_contributors = find_new_contributors(
        previous_contributors, last_week_contributors)
    new_added_files, new_modified_files = get_last_week_files()

    # print(new_contributors)
    # print(new_added_files)
    # print(new_modified_files)

    wiki_growth_percentage = round(
        (len(new_added_files)/current_md_files)*100, 2)

    if(len(new_contributors) != 0):
        current_contributors = new_contributors + previous_contributors
        write_current_state(current_contributors)

    new_contributors_with_names = []
    last_week_contributors_streaks_with_names = {}

    for email in last_week_contributors_streaks:
        name = get_name_from_email(email).title()
        last_week_contributors_streaks_with_names[name] = last_week_contributors_streaks[email]

        if email in new_contributors:
            new_contributors_with_names.append(name)

    if(len(new_contributors_with_names) != 0 or len(last_week_contributors_streaks_with_names) != 0 or len(new_added_files) != 0 or len(new_modified_files) != 0):
        send_message_to_slack(new_contributors_with_names, new_added_files,
                              new_modified_files, wiki_growth_percentage, last_week_contributors_streaks_with_names)


if __name__ == "__main__":
    main()

import git
import requests
import os
import json
import urllib
import dominate
from dominate.tags import *

repo_path = './'
git_cmd_runner = git.cmd.Git(repo_path)
bot_token = os.getenv('API_USER')


# Get name, title and image from slack using user's email
def get_user_details(email):

    required_details = {}
    response = requests.post(
        "https://slack.com/api/users.lookupByEmail", {"token": bot_token, "email": email})
    data = json.loads(response.content)

    if(data['ok']):
        required_details['real_name'] = data['user']['real_name']
        required_details['title'] = data['user']['profile']['title']
        required_details['image'] = data['user']['profile']['image_original']

    return required_details


# Get emails of contributors
def get_unique_emails():
    emails = git_cmd_runner.execute(
        ['git', 'shortlog', 'origin/master', '-sne'])
    emails = emails.split('\n')
    for idx, val in enumerate(emails):
        emails[idx] = val[val.find("<")+1:val.find(">")]

    return emails


# Write result to index.md
def write_to_md_file(all_users_details):
    md_file = 'docs/index.md'

    entire_html = div()

    with entire_html:
        h3("Meet our contributors")

        with table().add(tbody()):
            for idx, user in enumerate(all_users_details):

                if(idx % 4 == 0):
                    row = tr()

                data = td()
                data += img(src=user['image'], cls="user_image")
                data += h5(user['real_name'], cls="user_name")

                row += data

    with open(md_file, "a") as f:
        f.write(str(entire_html))


def main():
    emails = get_unique_emails()
    all_users_details = []
    for email in emails:
        details = get_user_details(email)
        if (details):
            all_users_details.append(details)

    write_to_md_file(all_users_details)


if __name__ == "__main__":
    main()

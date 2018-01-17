# Andy Zhang
# Wizards Bot - Automated Game Threads for the Washington Wizards Subreddit

import praw
import time
import datetime
import requests

SUBREDDIT = 'washingtonwizards'


# Logging in using credentials from praw.ini
def authenticate():
    robot = praw.Reddit('WizardsBot',
                        user_agent="Wizard's Game Thread Bot")
    print("Logged in as {}!".format(robot.user.me()))
    return robot


# Requests the game details for gameid and returns it in JSON format
def send_request(gameid):
    url = 'https://data.nba.com/data/10s/v2015/json/mobile_teams/nba/2017/scores/gamedetail/{}_gamedetail.json'.format(gameid)
    response = requests.get(url)
    print('Sending request to {}'.format(url))
    return response


# Returns the current gameID in the Wizards Schedule
# First line in gameIDs.txt represents the line_number of the gameID
def get_current_gameID(file):
    file_lines = file.readlines()
    line_number = int(file_lines[0].strip())
    gameID = file_lines[line_number].strip()
    return gameID


# Increments the gameID by 1, meaning that we continue to the next game in the Schedule
# First line in gameIDs.txt represents the line_number of the gameID
def update_gameID(file):
    file_lines = file.readlines()
    line_number = int(file_lines[0].strip())
    file_lines[0] = str(line_number + 1) + '\n'
    with open("gameIDs.txt", "w") as f:
        f.writelines(file_lines)


# Opens gameIDs.txt to get the next game in the schedule
# Submits a Game Thread before the game and Post Game Thread after the game
def main():
    robot = authenticate()
    file = open('gameIDs.txt')
    gameID = get_current_gameID(file)
    print('Next Game ID: {}'.format(gameID))
    gameinfo = send_request(gameID).json()
    gametime = gameinfo['g']['gcode'][:-7] + ' ' + gameinfo['g']['stt'][:-3]
    gametime = datetime.datetime.strptime(gametime, '%Y%m%d %I:%M %p') - datetime.timedelta(hours=1)

    # Waiting till around 1 hour before game time to post
    while datetime.datetime.now() < gametime:
        print('Waiting until ' + str(gametime))
        time.sleep(1300)

    # Posting Game Thread
    awayteam = gameinfo['g']['vls']['tc'] + ' ' + gameinfo['g']['vls']['tn']
    hometeam = gameinfo['g']['hls']['tc'] + ' ' + gameinfo['g']['hls']['tn']
    title = '[Game Thread] {} @ {} ({})'.format(awayteam, hometeam, gametime.strftime('%m-%d-%Y'))
    print('Game Thread Ready! {}'.format(title))
    gamethread = robot.subreddit(SUBREDDIT).submit(title=title, selftext='')
    gamethread.mod.sticky(state=True)
    time.sleep(10500)

    # Waiting for game to finish by checking status
    while gameinfo['g']['stt'] != 'Final':
        print('Still waiting on game to finish...')
        time.sleep(35)
        gameinfo = send_request(gameID).json()

    # Posting Post Game Thread
    gamethread.mod.sticky(state=False)
    title = '[Post Game Thread] {} @ {} ({})'.format(awayteam, hometeam, gametime.strftime('%m-%d-%Y'))
    print('Post Game Thread Ready! {}'.format(title))
    postgamethread = robot.subreddit(SUBREDDIT).submit(title=title, selftext='')
    postgamethread.mod.sticky(state=True)
    update_gameID(file)


if __name__ == '__main__':
    main()

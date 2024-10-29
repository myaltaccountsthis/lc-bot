import os
import random
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import io
import discord
import gql.transport.exceptions

import query

PROBLEM_PATH = "out/questionList.txt"
CONTEST_PATH = "out/contestList.txt"
PROBLEM_LINK = "https://leetcode.com/problems/"
CONTEST_LINK = "https://leetcode.com/contest/"

question_data = []
contest_info_data = []
question_info_from_slug = {}
contest_info_from_slug = {}
contest_id_from_slug = {}

# Loads the question data by calling the query, stores into array by id, TIME_EXPENSIVE
async def load_question_data(check_server=False, force_fetch=False):
    global question_data
    if force_fetch or len(question_data) == 0:
        # load all questions into question_data
        if force_fetch or not os.path.exists(PROBLEM_PATH):
            result = await query.do_query("problemsetQuestionList", values={"categorySlug": "", "skip": 0, "limit": -1, "filters": {}})
            question_data = result["problemsetQuestionList"]["questions"]
            with open(PROBLEM_PATH, "w") as file:
                file.write(str(question_data))
            print("Loaded all question data from server!")
        else:
            with open(PROBLEM_PATH, "r") as file:
                question_data = eval(file.read())
            print("Loaded all question data from file!")

        # Store the question info into a dict for easy access
        for question in question_data:
            question["url"] = PROBLEM_LINK + question["titleSlug"]
            question_info_from_slug[question["titleSlug"]] = question


    if check_server:
        # check for unloaded problems
        # skip current problem count
        old_len = len(question_data)
        if old_len == 0:
            print("Question data file was empty, doing a full reload")
            await load_question_data(force_fetch=True, check_server=True)
            return

        result = await query.do_query("problemsetQuestionList", values={"categorySlug": "", "skip": old_len, "limit": old_len, "filters": {}})
        # print(result)
        new_len = result["problemsetQuestionList"]["total"]

        # the query won't have all the new problems so do a full reload
        if old_len <= new_len / 2:
            question_data = []
            print("More than half of the question data likely missing, doing a full reload")
            await load_question_data(force_fetch=True, check_server=True)
            return

        result = result["problemsetQuestionList"]["questions"]

        # add all the new questions into question_data
        for question in result:
            question["url"] = PROBLEM_LINK + question["titleSlug"]
            question_info_from_slug[question["titleSlug"]] = question
            question_data.append(question)

        # write to file if updated
        if len(result) > 0:
            print(f"Found {len(result)} question data on server!")
            with open(PROBLEM_PATH, "w") as file:
                file.write(str(question_data))
        else:
            print("No new question data found on server")


#import discord

def create_line_chart(userInfoList, knightCutoff=1850, guardianCutoff=2150):#dates, points, username, knightCutoff=1850, guardianCutoff=2150):
    # Convert string dates to datetime objects if necessary
    #dates = [datetime.strptime(date, '%Y-%m-%d') if isinstance(date, str) else date for date in userInfoList[0]]
    # print(len(dates))
    # print(len(points))
    # Determine the min and max points to set y-axis limits
    min_points = 99999
    max_points = 0
    #print(userInfoList)
    for user in userInfoList:
        min_points = min(min(user[1]), min_points)  # Adding a bit of padding
        max_points = max(max(user[1]), max_points)
    max_points += 100
    min_points -= 100

    # Create the plot
    fig, ax = plt.subplots()
    fig.set_figwidth(8)
    fig.set_figheight(6)

    # Define the Codeforces divisions and their exact colors
    divisions = [
        (0, 1199, '#CCCCCC'),     # Newbie: gray
        (1200, 1399, '#77FF77'),  # Pupil: light green
        (1400, 1599, '#77DDBB'),  # Specialist: cyan/teal
        (1600, 1899, '#AAAAFF'),  # Expert: light blue
        (1900, 2099, '#FF88FF'),  # Candidate Master: pink
        (2100, 2299, '#FFCC88'),  # Master: light orange/yellow
        (2300, 2399, '#FFBB55'),  # International Master: orange
        (2400, 2999, '#FF7777'),  # Grandmaster: red
        (3000, 4000, '#FF3333')   # International Grandmaster: darker red
    ]

    # Add colored backgrounds only for the divisions that fall within the relevant range
    for lower_bound, upper_bound, color in divisions:
        if lower_bound <= max_points and upper_bound >= min_points:
            ax.axhspan(max(lower_bound, min_points), min(upper_bound, max_points), facecolor=color, alpha=0.8, zorder=-2)


    # Plot the data
    for x in range(len(userInfoList)):
        user = userInfoList[x]
        print(user)
        #print(user)
        #print(user[0])
        #print(user[1])
        dates = user[0]
        points = user[1]
        username = user[2]
        #user0 = [datetime.strptime(date, '%Y-%m-%d') if isinstance(date, str) else date for date in user[0]]
        color = "black"
        if x == 1:
            color = "blue"
        if x == 2:
            color = "green"
        if x == 3:
            color = "purple"
        if x == 4:
            color = "red"
        if x == 5:
            color = "orange"
        if x == 6:
            color = 'tan'
        ax.plot(dates, points, marker='o', linestyle='-', color=color, markerfacecolor='white', markeredgecolor='black', markersize=3, zorder=2, label=username)
        # Add horizontal lines for knight and guardian cutoffs
        # Format the date on the x-axis
        #ax.plot(user[0], user[1], label='Line 2', color='green', marker='x', markersize=9)
        #break
    
    #ax.plot(userInfoList[0][1], userInfoList[0][0], marker='o', linestyle='-', color='black', markerfacecolor='white', markeredgecolor='black', markersize=3, zorder=2)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        #ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))  # Adjust the interval as necessary
    ax.xaxis.set_major_locator(plt.MaxNLocator(10))
        # Set the y-axis limits dynamically based on the data
    ax.set_ylim(min_points, max_points)
        # Rotate and align the x labels
    plt.gcf().autofmt_xdate()
    if (min_points < 1650 and max_points > 1650):
        ax.axhline(y=knightCutoff, color='blue', linestyle='--',zorder=1)# label=f'Knight Cutoff: {knightCutoff}', zorder=1)
        ax.text(user[0][0], knightCutoff,  f'Knight - {knightCutoff}', color='blue', verticalalignment='bottom', horizontalalignment='left')
    if (min_points < 2150 and max_points > 2150):
        ax.axhline(y=guardianCutoff, color='red', linestyle='--',zorder=1)# label=f'Guardian Cutoff: {guardianCutoff}', zorder = 1)
        ax.text(user[0][0], guardianCutoff,f'Guardian - {guardianCutoff}', color='red', verticalalignment='bottom', horizontalalignment='left')
    # Add labels for the cutoffs
        
    # Add labels and title
    plt.xlabel('Date')
    plt.ylabel('Rating')
    '''
    s = 'Username: ' + str(userInfoList[0][2])
    if (str(userInfoList[0][2]).lower() == 'hastorius'):
        s = "Hastorius of Mordor"
    elif (str(userInfoList[0][2]).lower() == 'sahasrad'):
        s = "Chippi Chappa"
    else:
        s = ""
    '''
    s = ""
    plt.title(s)
    # Add the legend for the cutoffs
    lX = 0.5
    lY = 1.15
    if (len(userInfoList) > 3):
        lY = 1.18
    plt.legend(loc='upper center', bbox_to_anchor=(lX, lY), ncol=3)
    #plt.show()
    # Save the figure to a buffer in PNG format
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)

    return buf  # Return buffer with image content

# Loads the contest info data by calling the query, stores into array and dict, TIME_EXPENSIVE
async def load_contest_info_data(check_server=False, force_fetch=False):
    global contest_info_data, contest_info_from_slug, contest_id_from_slug
    await load_question_data()

    fetched = False
    if force_fetch or len(contest_info_data) == 0:
        if force_fetch or not os.path.exists(CONTEST_PATH):
            result = await query.do_query("contestGeneralInfo", values={"pageNo": 1, "numPerPage": -1})
            result = result["pastContests"]["data"]
            fetched = True
            with open(CONTEST_PATH, "w") as file:
                file.write(str(result))
            print("Loaded all contest data from server!")
        else:
            with open(CONTEST_PATH, "r") as file:
                result = eval(file.read())
            print("Loaded all contest data from file!")
        
        contest_info_data = result
        # Store the contest info into a dict for easy access
        for contest in result:
            contest["url"] = CONTEST_LINK + contest["titleSlug"]
            for question in contest["questions"]:
                question_from_slug = question_info_from_slug[question["titleSlug"]]
                question["url"] = question_from_slug["url"]
                question["difficulty"] = question_from_slug["difficulty"]
            contest_info_from_slug[contest["titleSlug"]] = contest

    if check_server and not fetched:
        # load 15 entries
        load_count = 10
        result = await query.do_query("contestGeneralInfo", values={"pageNo": 1, "numPerPage": load_count})
        result = result["pastContests"]["data"]
        loaded = 0

        # prepend ones that are missing into contest_info_data
        for contest in result:
            if contest["titleSlug"] not in contest_info_from_slug:
                contest["url"] = CONTEST_LINK + contest["titleSlug"]
                for question in contest["questions"]:
                    question_from_slug = question_info_from_slug[question["titleSlug"]]
                    question["url"] = question_from_slug["url"]
                    question["difficulty"] = question_from_slug["difficulty"]
                contest_info_from_slug[contest["titleSlug"]] = contest
                contest_info_data.append(contest)
                loaded += 1

        if loaded > 0:
            print(f"Found {loaded} updated contest data on server")
            with open(CONTEST_PATH, "w") as file:
                file.write(str(contest_info_data))
        else:
            print("No new contest data found on server")

        # if all are missing, call the function again to do a full reload
        if loaded == load_count:
            contest_info_data = []
            print("More than 10 contest data likely missing, doing a full reload")
            await load_contest_info_data(force_fetch=True)

    for i in range(len(contest_info_data)):
        contest_id_from_slug[contest_info_data[i]["titleSlug"]] = i


# Returns the link of a random question
async def random_question(difficulty, allow_premium):
    await load_question_data()
    # The data of a random question, keep looping if
    # it is a premium question and we don't want premium questions
    question = None
    while True:
        question = question_data[random.randrange(0, len(question_data))]
        if (allow_premium or not question["paidOnly"]) and (difficulty == "Random" or question["difficulty"] == difficulty.value):
            break
    return question["url"]

# Get generic info (questions and links) of a specific contest
# Returns None if the contest does not exist
async def get_contest_info(contest_type, contest_number):
    if contest_type is None and contest_number:
        return "You cannot specify a contest number without a contest type"

    await load_contest_info_data()

    title_slug = await get_valid_title_slug(contest_type, contest_number)

    # Check if the contest exists
    if title_slug not in contest_info_from_slug:
        return None
    return contest_info_from_slug[title_slug]

async def get_valid_title_slug(contest_type, contest_number):
    title_slug = ""
    # Creating a valid title slug
    if contest_number is None:
        if contest_type is None:
            # Get the latest contest
            title_slug = contest_info_data[0]["titleSlug"]
        else:
            # Get the latest contest of the specified type
            type_bool = contest_type == "biweekly"
            curr = 0
            # Max of 3 iterations
            while ("biweekly" in contest_info_data[curr]["titleSlug"]) != type_bool:
                curr += 1
            title_slug = contest_info_data[curr]["titleSlug"]
    else:
        # Get the specified contest
        title_slug = f"{contest_type}-contest-{contest_number}"
        if contest_type == "weekly" and contest_number < 58:
            title_slug = "leetcode-" + title_slug
    return title_slug

async def get_contest_ranking(contest_type, contest_number, userList):
    if contest_type is None and contest_number:
        return "You cannot specify a contest number without a contest type"
    
    title_slug = await get_valid_title_slug(contest_type, contest_number)
    user_info = []
    for user in userList:
        user_data = await get_user_contest_history(user)
        contests = user_data["userContestRankingHistory"]
        
        if title_slug not in contest_info_from_slug:
            return title_slug + " does not exist"
        
        contest = None
        for c in contests:
            if c["contest"]["titleSlug"] == title_slug:
                contest = c
                break
        if contest is None:
            return "Ratings aren't out for " + contest_info_from_slug[title_slug]["title"]
        if contest["attended"]:
            user_info.append({
                "username": user,
                "rank": contest["ranking"],
                "rating": contest["rating"],
                "solved": contest["problemsSolved"],
                "time": convert_seconds_to_time(contest["finishTimeInSeconds"])
            })

    if len(user_info) == 0:
        return "No participants found for " + contest_info_from_slug[title_slug]["title"]

    return user_info


# Returns general user info, including contest rating, problems solved, etc.
async def get_user_info(user_slug):
    user_info = None
    try:
        user_info = await query.do_query("userProfile", values={"username": user_slug})
    except gql.transport.exceptions.TransportQueryError:
        return { "message": f"User `{user_slug}` does not exist", "error": True }

    if user_info["userContestRanking"] is None:
        user_info["userContestRanking"] = {
            "rating": 0,
            "badge": None,
            "globalRanking": 0,
            "attendedContestsCount": 0,
            "topPercentage": 100,
        }
    if user_info["userContestRanking"]["badge"] is None:
        user_info["userContestRanking"]["badge"] = { "name": "None" }
    
    return {
        "username": user_info["matchedUser"]["username"], # Username of user
        "user_avatar": user_info["matchedUser"]["profile"]["userAvatar"], # Avatar of user
        "rating": user_info["userContestRanking"]["rating"], # Contest rating of user
        "badge": user_info["userContestRanking"]["badge"]["name"] if user_info["userContestRanking"]["badge"] else None, # Badge of user
        # Ranking of user based on contests
        "contest_rank": user_info["userContestRanking"]["globalRanking"],
        # Number of contests taken
        "contests_attended": user_info["userContestRanking"]["attendedContestsCount"],
        # Top percent of user based on contests
        "top_percentage": user_info["userContestRanking"]["topPercentage"],
        # Ranking of user based on problems solved
        "solved_rank": user_info["matchedUser"]["profile"]["ranking"],
        # Array of difficulty and percentage, ac rate based on submissions vs solved
        "ac_rate": user_info["matchedUser"]["problemsSolvedBeatsStats"],
        # Array of difficulty and count, number of problems solved, includes difficulty "All"
        "problems_solved": user_info["matchedUser"]["submitStatsGlobal"],
    }

async def get_user_recent_solves(user_slug, limit = 10):
    recent_solves = await query.do_query("userRecentAcSubmissions", values={"username": user_slug, "limit": limit})
    # TODO error handling
    return recent_solves["recentAcSubmissionList"]

async def get_user_recent_submissions(user_slug, limit = 10):
    recent_submissions = await query.do_query("userRecentSubmissions", values={"username": user_slug, "limit": limit})
    # TODO error handling
    return recent_submissions["recentSubmissionList"]

async def get_user_contest_history(user_slug):
    recent_contests= await query.do_query("userContestHistory", values={"username": user_slug})
    # TODO error handling
    return recent_contests


char_pop = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%&"
# generate verification code
def generate_unique_code():
    return ''.join(random.choices(char_pop, k=12))

def IDENTIFY_IMAGE():
    return discord.File("resources/identify_instructions.png", filename="identify_instructions.png")

def convert_timestamp_to_date(timestamp):
    # Convert the timestamp to a datetime object
    date_time = datetime.utcfromtimestamp(timestamp)
    # Format the date to a string in 'YYYY-MM-DD' format
    #date_string = date_time.strftime('%Y-%m-%d')
    return date_time

def convert_seconds_to_time(seconds):
    # Convert the seconds to a datetime object
    time = datetime.utcfromtimestamp(seconds)
    # Format the time to a string in 'HH:MM:SS' format
    time_string = time.strftime('%H:%M:%S')
    return time_string
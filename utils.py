import os
import random

import discord
import gql.transport.exceptions

import query
import psycopg2

PROBLEM_PATH = "out/questionList.txt"
CONTEST_PATH = "out/contestList.txt"
PROBLEM_LINK = "https://leetcode.com/problems/"
CONTEST_LINK = "https://leetcode.com/contest/"

question_data = []
contest_info_data = []
question_info_from_slug = {}
contest_info_from_slug = {}

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



# Loads the contest info data by calling the query, stores into array and dict, TIME_EXPENSIVE
async def load_contest_info_data(check_server=False, force_fetch=False):
    global contest_info_data, contest_info_from_slug
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

        # prepend ones that are missing into contest_info_data,
        result = result[::-1]
        for contest in result:
            if contest["titleSlug"] not in contest_info_from_slug:
                contest["url"] = CONTEST_LINK + contest["titleSlug"]
                for question in contest["questions"]:
                    question_from_slug = question_info_from_slug[question["titleSlug"]]
                    question["url"] = question_from_slug["url"]
                    question["difficulty"] = question_from_slug["difficulty"]
                contest_info_from_slug[contest["titleSlug"]] = contest
                contest_info_data.insert(0, contest)
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

    # Check if the contest exists
    if title_slug not in contest_info_from_slug:
        print("not in")
        return None
    return contest_info_from_slug[title_slug]

# Returns general user info, including contest rating, problems solved, etc.
async def get_user_info(user_slug):
    try:
        user_info = await query.do_query("userProfile", values={"username": user_slug})
    except gql.transport.exceptions.TransportQueryError:
        return {"message": f"User {user_slug} does not exist", "error": True}
    if user_info["matchedUser"] is None:
        return { "message": f"User {user_slug} does not exist", "error": True }

    if user_info["userContestRanking"] is None:
        user_info["userContestRanking"] = {
            "rating": 0,
            "badge": None,
            "globalRanking": 0,
            "attendedContestsCount": 0,
            "topPercentage": 100,
        }
    
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

char_pop = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%&"
# generate verification code
def generate_unique_code():
    return ''.join(random.choices(char_pop, k=12))

def IDENTIFY_IMAGE():
    return discord.File("resources/identify_instructions.png", filename="identify_instructions.png")
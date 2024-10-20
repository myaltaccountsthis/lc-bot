import re
import os
import random
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
async def load_question_data(force_fetch=False):
    global question_data
    if len(question_data) == 0:
        if force_fetch or not os.path.exists(PROBLEM_PATH):
            result = await query.do_query("problemsetQuestionList", values={"categorySlug": "", "skip": 0, "limit": -1, "filters": {}})
            with open(PROBLEM_PATH, "w") as file:
                file.write(str(result))
        else:
            with open(PROBLEM_PATH, "r") as file:
                result = eval(file.read())
        question_data = result["problemsetQuestionList"]["questions"]

        # Store the question info into a dict for easy access
        for question in question_data:
            question["url"] = PROBLEM_LINK + question["titleSlug"]
            question_info_from_slug[question["titleSlug"]] = question
        print("Loaded question data!")

# Loads the contest info data by calling the query, stores into array and dict, TIME_EXPENSIVE
async def load_contest_info_data(force_fetch=False):
    global contest_info_data, contest_info_from_slug
    await load_question_data()
    if len(contest_info_data) == 0:
        if force_fetch or not os.path.exists(CONTEST_PATH):
            result = await query.do_query("contestGeneralInfo", values={"titleSlug": ""})
            result = result["pastContests"]["data"]

            with open(CONTEST_PATH, "w") as file:
                file.write(str(result))
        else:
            with open(CONTEST_PATH, "r") as file:
                result = eval(file.read())

        contest_info_data = result
        # contest_info_data.reverse()

        # Store the contest info into a dict for easy access
        for contest in result:
            contest["url"] = CONTEST_LINK + contest["titleSlug"]
            for question in contest["questions"]:
                question_from_slug = question_info_from_slug[question["titleSlug"]]
                question["url"] = question_from_slug["url"]
                question["difficulty"] = question_from_slug["difficulty"]
            contest_info_from_slug[contest["titleSlug"]] = contest
        print("Loaded contest data!")

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
        return None

    return contest_info_from_slug[title_slug]

# Returns general user info, including contest rating, problems solved, etc.
async def get_user_info(user_slug):
    user_info = await query.do_query("userProfile", values={"username": user_slug})
    if user_info["matchedUser"] is None:
        return { "message": f"User {user_slug} does not exist", "error": True }
    if user_info["userContestRanking"] is None:
        user_info["userContestRanking"] = {
            "rating": 0,
            "badge": { "name": "None" },
            "globalRanking": 0,
            "attendedContestsCount": 0,
            "topPercentage": 100,
        }
    
    return {
        "username": user_info["matchedUser"]["username"], # Username of user
        "user_avatar": user_info["matchedUser"]["profile"]["userAvatar"], # Avatar of user
        "rating": user_info["userContestRanking"]["rating"], # Contest rating of user
        "badge": user_info["userContestRanking"]["badge"]["name"], # Badge of user
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
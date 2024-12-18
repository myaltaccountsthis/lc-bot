import asyncio
import os
from datetime import datetime
from fileinput import filename
from importlib.metadata import files
from itertools import compress
from functools import cmp_to_key

import discord
from discord import app_commands
from dotenv import load_dotenv

import emojis
import utils
import database

import io
from PIL import Image, ImageDraw, ImageFont
load_dotenv()

bot = discord.Client(intents=discord.Intents.default())
tree = app_commands.CommandTree(bot)

USERNAME_MAX_LENGTH = 30
# How many characters to display for a username in a table (i.e. leaderboard)
USERNAME_DISPLAY_LENGTH = 15

db = database.Database()

async def check_user_not_found_response(interaction: discord.Interaction, user_info, should_edit=False):
    if "error" in user_info:
        embed = discord.Embed(title="Error", description=user_info["message"], color=discord.Color.red())
        if should_edit:
            await interaction.edit_original_response(content="", embed=embed)
        else:
            await interaction.response.send_message(embed=embed)
        return True
    return False

async def check_user_not_found(interaction: discord.Interaction, user_slug, should_edit=False):
    user_info = await utils.get_user_info(user_slug)
    if await check_user_not_found_response(interaction, user_info, should_edit):
        return True
    return user_info

async def batch_check_user_not_found_contest_history(interaction: discord.Interaction, user_list, should_edit=False):
    result = await utils.get_batch_user_contest_history(user_list)
    for user_info in result:
        if await check_user_not_found_response(interaction, user_info, should_edit):
            return True
    return result

# BOT EVENTS

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        # Sync slash command tree
        synced = await tree.sync()
        # Check server every 5 minutes
        asyncio.create_task(check_server())
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


# GENERAL COMMANDS

@tree.command(name="ping", description="Display latency information")
async def ping(interaction: discord.Interaction):
    text = f'Pong! {round (bot.latency * 1000)} ms initial.'
    # Initial ping message
    await interaction.response.send_message(text)
    msg = await interaction.original_response()

    # Edit the message with the latency of original response
    time = round((msg.created_at - interaction.created_at).total_seconds() * 1000)
    await msg.edit(content=text + f' {time} ms round-trip.')

@tree.command(name="leaderboard", description="Get a leaderboard of the server's verified users by rating")
async def leaderboard(interaction: discord.Interaction):
    
    if len(verified_users) == 0:
        await interaction.response.send_message("No users have verified their LeetCode account.")
        return
    
    user_info = await utils.get_batch(utils.get_user_info, verified_users.values())
    user_info = sorted(user_info, key=lambda x: x["rating"], reverse=True)
    for i, user in enumerate(user_info):
        user["rank"] = i + 1
        discUsername = await bot.fetch_user(list(verified_users.keys())[list(verified_users.values()).index(user["username"])])
        if discUsername is None:
            user["discordUsername"] = "Unknown"
        discUsername = discUsername.name
        user["discordUsername"] = discUsername

    # Column widths for formatting
    colWidths = [len("#"), len("Username"), len("Handle"), len("Rating")]
    for user in user_info:
        user["rating"] = round(user["rating"], 2)
        colWidths[0] = max(colWidths[0], len(str(user["rank"])))
        colWidths[1] = max(colWidths[1], len(user["discordUsername"]))
        colWidths[2] = max(colWidths[2], len(user["username"]))
        colWidths[3] = max(colWidths[3], len(str(user["rating"])))
    colWidths[1] = min(colWidths[1], USERNAME_DISPLAY_LENGTH)
    colWidths[2] = min(colWidths[2], USERNAME_DISPLAY_LENGTH)

    embed = discord.Embed(title="Leaderboard", color=discord.Color.green())
    description = f"```graphql\n{"#":>{colWidths[0]}}  {"Username".center(colWidths[1])}  {"Handle".center(colWidths[2])}  {"Rating".center(colWidths[3])}\n"
    description += f"{"  ".join(['-' * colWidth for colWidth in colWidths])}\n"
    
    description += "\n".join([f"{user['rank']:>{colWidths[0]}}  {user['discordUsername'][:colWidths[1] - 3] + "..." if len(user['discordUsername']) > colWidths[1] else user['discordUsername']:<{colWidths[1]}}  {user['username'][:colWidths[2] - 3] + "..." if len(user['username']) > colWidths[2] else user['username']:<{colWidths[2]}}  {user['rating']:>{colWidths[3]}.2f}" for user in user_info])
    description += "```"
    embed.description = description
    await interaction.response.send_message(embed=embed)

# PROBLEM COMMANDS

# Displays a random leetcode problem, can specifiy if you want premium problems
@tree.command(name="random", description="Get a random question from LeetCode")
@app_commands.choices(difficulty=[
    app_commands.Choice(name="Easy", value="Easy"),
    app_commands.Choice(name="Medium", value="Medium"),
    app_commands.Choice(name="Hard", value="Hard"),
    app_commands.Choice(name="Random", value="Random")
])
async def randomQuestion(interaction: discord.Interaction, difficulty: app_commands.Choice[str] = "Random", allow_premium: bool = False):
    await interaction.response.send_message(await utils.random_question(difficulty, allow_premium))


# CONTEST COMMANDS

# Group for all contest related commands
contest = app_commands.Group(name="contest", description="Commands related to contests")
# Command to get problems from a specific contest
@contest.command(name="info", description="Get information about a specific contest")
@app_commands.choices(contest_type=[
    app_commands.Choice(name="Weekly", value="weekly"),
    app_commands.Choice(name="Biweekly", value="biweekly")
])
async def info(interaction: discord.Interaction, contest_type: app_commands.Choice[str] = None, contest_number: int = None):
    contest_info = await utils.get_contest_info(contest_type.value if contest_type else None, contest_number)
    if contest_info is None:
        await interaction.response.send_message(f"Could not find {contest_type.name} Contest {contest_number}.")
    elif type(contest_info) == str:
        await interaction.response.send_message(contest_info)
    else:
        embed = discord.Embed(title=contest_info["title"], url=contest_info["url"])
        # add each hyperlink to the embed as a line in description
        embed.color = discord.Color.orange()
        embed.description = "\n".join([f"**{i + 1}.** [{question['title']}]({question['url']}) *({question['difficulty']})*"
                                       for i, question in enumerate(contest_info['questions'])])

        embed.set_footer(text=f"Contest held on {datetime.fromtimestamp(contest_info['startTime']).strftime('%b %d, %Y')}")
        await interaction.response.send_message(embed=embed)

# Command to get the rankings of verified users in the server for a given contest
@contest.command(name="ranking", description="Get the rankings of a specific contest")
@app_commands.choices(contest_type=[
    app_commands.Choice(name="Weekly", value="weekly"),
    app_commands.Choice(name="Biweekly", value="biweekly")
])
async def ranking(interaction: discord.Interaction, contest_type: app_commands.Choice[str] = None, contest_number: int = None):
    await interaction.response.defer()
    contest_info = await utils.get_contest_info(contest_type.value if contest_type else None, contest_number)
    if contest_info is None:
        await interaction.followup.send(f"Could not find {contest_type.name} Contest {contest_number}.")
        return
    if type(contest_info) == str:
        await interaction.followup.send(contest_info)
        return
    
    # has username, rank, rating, and solved
    user_info = await utils.get_contest_ranking(contest_type.value if contest_type else None, contest_number, list(verified_users.values()))
    if isinstance(user_info, str):
        await interaction.followup.send(user_info)
        return
    
    # Make the embed
    embed = discord.Embed(title=f"{contest_info['title']} Rankings", url=contest_info["url"])
    embed.color = discord.Color.red()
    num_questions = await utils.get_contest_info(contest_type.value if contest_type else None, contest_number)
    num_questions = len(num_questions["questions"])
    user_info = sorted(user_info, key=cmp_to_key(lambda item1, item2: item1['rank'] - item2['rank']))

    # Column widths for formatting
    colWidths = [len("#"), len("Username"), len("="), len("Finish Time"), len("Rating")]
    for user in user_info:
        user["rating"] = round(user["rating"], 2)
        colWidths[0] = max(colWidths[0], len(str(user["rank"])))
        colWidths[1] = max(colWidths[1], len(user["username"]))
        colWidths[2] = max(colWidths[2], len(f"{user['solved']}/{num_questions}"))
        colWidths[3] = max(colWidths[3], len(user["time"]))
        colWidths[4] = max(colWidths[4], len(str(user["rating"])))
    colWidths[1] = min(colWidths[1], USERNAME_DISPLAY_LENGTH)

    # Make the table
    description = f"```graphql\n{"#":>{colWidths[0]}}  {"Username".center(colWidths[1])}  {"=".center(colWidths[2])}  {"Finish Time".center(colWidths[3])}  {"Rating".center(colWidths[4])}\n"
    description += f"{"  ".join(['-' * colWidth for colWidth in colWidths])}\n"
    description += "\n".join([f"{user['rank']:>{colWidths[0]}}  {user['username'][:colWidths[1] - 3] + "..." if len(user['username']) > colWidths[1] else user['username']:<{colWidths[1]}}  {str(user['solved']) + '/' + str(num_questions):>{colWidths[2]}}  {user['time']:>{colWidths[3]}}  {user['rating']:>{colWidths[4]}}" for user in user_info])
    description += "```"
    embed.description = description
    await interaction.followup.send(embed=embed)

tree.add_command(contest)


# USER COMMANDS

active_identification = {}
# Discord id to leetcode username
verified_users = {}
for user in db.get_all_users():
    verified_users[user[0]] = user[1]
# Leetcode username back to discord id
leetcode_to_discord = {v: k for k, v in verified_users.items()}

@tree.command(name="identify", description="Link your LeetCode account to your Discord account")
async def identify(interaction: discord.Interaction, username: str):
    if len(username) > USERNAME_MAX_LENGTH:
        await interaction.response.send_message(f"Username too long, must be less than {USERNAME_MAX_LENGTH} characters.")
        return
    
    user_id = interaction.user.id

    # allow users to reverify only if the new username is different
    if user_id in verified_users and verified_users[user_id].lower() == username.lower():
        await interaction.response.send_message(f"You have already verified that you are `{verified_users[user_id]}` on LeetCode.")
        return

    user_info = await check_user_not_found(interaction, username)
    if (user_info == True):
        return

    # get the official username from the user info
    username = user_info["username"]
    recent_sub_list = await utils.get_user_recent_submissions(username)
    embed = discord.Embed(title="Verification Instructions", color=discord.Color.orange())
    unique_code = utils.generate_unique_code()

    if len(recent_sub_list) == 0:
        # use add-two-integers
        embed.description = f"Please verify that you are `{username}` on LeetCode by adding\n```Verifying with LeetCode Bot - {unique_code}```\nas a note on your most recent problem submission. If you don't have one, you can submit anything to [2235. Add Two Integers]({utils.PROBLEM_LINK}add-two-integers/)."
    else:
        last_sub = recent_sub_list[0]
        embed.description = f"Please verify that you are `{username}` on LeetCode by adding\n\n```Verifying with LeetCode Bot - {unique_code}```\nas a note on either your most recent submission **[({last_sub['title']})]({utils.PROBLEM_LINK + last_sub['titleSlug']}/submissions/{last_sub['id']})** or on a new one."

    embed.set_footer(text="Click the button below when you're finished verifying")

    # Upload the image to discord
    # TODO: store image as an external url instead
    image = utils.IDENTIFY_IMAGE()
    embed.set_image(url=f"attachment://{image.filename}")

    if user_id in active_identification:
        active = active_identification[user_id]
        button = active[2]
        message = active[3]
        # disable the previous button
        button.button_callback.disabled = True
        await message.edit(view=button)

    button = FinishIdentification(user_id)
    await interaction.response.send_message(embed=embed, file=image, view=button)
    # store the active identification session
    active_identification[user_id] = [username, unique_code, button, await interaction.original_response()]

class FinishIdentification(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=180)
        self.user_id = user_id

    @discord.ui.button(label="I'm finished", style=discord.ButtonStyle.primary)
    async def button_callback(self, interaction: discord.Interaction, button: discord.Button):
        user_id = interaction.user.id

        # check if the button is clicked by the same user
        if user_id != self.user_id:
            await interaction.response.send_message("This button is not for you.", ephemeral=True)
            return
        if user_id not in active_identification:
            await interaction.response.send_message("You haven't started the verification process yet.", ephemeral=True)
            return

        # error handling
        username, unique_code, target_button, message = active_identification[user_id]
        if self != target_button:
            return
        user_info = await check_user_not_found(interaction, username)
        if (user_info == True):
            return

        # check if the user has added the note
        recent_sub_list = await utils.get_user_recent_submissions(username)
        found = False
        valid_note = f"Verifying with LeetCode Bot - {unique_code}"
        for submission in recent_sub_list:
            if len(submission["notes"]) <= len(valid_note) + 4 and valid_note == str(submission["notes"]).strip():
                found = True
                break

        # if the note is found, add the user to the verified list
        if found:
            verified_users[user_id] = username
            db.add_user(user_id, username)
            button.disabled = True
            await message.edit(view=self)
            del active_identification[user_id]
            await interaction.response.send_message(f"Successfully verified that you are `{username}` on LeetCode.")
            del self
        else:
            await interaction.response.send_message("Could not find the verification note on your **recent submissions**. Please try again.", ephemeral=True)

    async def on_timeout(self):
        if self != active_identification[self.user_id][2]:
            return

        self.button_callback.disabled = True
        message = active_identification[self.user_id][3]
        embed = discord.Embed(title="Verification Timed Out", description="Please try again.", color=discord.Color.red())
        await message.edit(embed=embed, view=self, attachments=[])
        del active_identification[self.user_id]
        del self

@tree.command(name="profile", description="Get information about a specific user")
async def profile(interaction: discord.Interaction, username: str = None):
    # if no username is specified, use the discord user's leetcode username
    if username is None:
        if interaction.user.id in verified_users:
            username = verified_users[interaction.user.id]
        else:
            await interaction.response.send_message("Please specify a user to get information about.")
            return
    
    if (len(username) > USERNAME_MAX_LENGTH):
        await interaction.response.send_message(f"Username too long, must be less than {USERNAME_MAX_LENGTH} characters.")
        return
    
    user_info = await check_user_not_found(interaction, username)
    if (user_info == True):
        return
        
    num_solved = {}
    for category in user_info["problems_solved"]["acSubmissionNum"]:
        num_solved[category["difficulty"]] = category["count"]
    lines = [
        "**Contests**",
        f"Rating: {round(user_info['rating'], 1)} {emojis.get_emoji(user_info['badge'])}",
        f"Top {user_info['top_percentage']}%",
        "",
        f"**Problems Solved:**",
        f"Easy: {num_solved['Easy']}",
        f"Medium: {num_solved['Medium']}",
        f"Hard: {num_solved['Hard']}",
        f"Total: {num_solved['All']}"
    ]

    embed = discord.Embed()
    embed.set_author(name=user_info["username"], icon_url=user_info["user_avatar"], url=f"https://leetcode.com/u/{user_info['username']}")
    embed.description = "\n".join(lines)
    await interaction.response.send_message(embed=embed)

@tree.command(name="plot", description="Plots your Rating over Time")
async def plot(interaction: discord.Interaction, usernames: str = None):
    # usernames is required if not verified
    if usernames is None:
        if interaction.user.id in verified_users:
            usernames = verified_users[interaction.user.id]
        else:
            await interaction.response.send_message("Please specify a user to get information about.")
            #print(3)
            return
        
    # check validity of input
    user_list = usernames.split(" ")
    for user in user_list:
        if len(user) > USERNAME_MAX_LENGTH:
            await interaction.response.send_message(f"Username too long, must be less than {USERNAME_MAX_LENGTH} characters.")
            return
    
    # Fetch user data
    await interaction.response.defer()
    user_info_list = []
    user_contest_list = await batch_check_user_not_found_contest_history(interaction, user_list, True)
    if (user_contest_list == True):
        return
    
    # Assume all users exist since if statement would otherwise return
    for i, user in enumerate(user_list):
        contest_data = user_contest_list[i]
        contestList = contest_data["userContestRankingHistory"]
        dates = []
        points = []
        for contest in contestList:
            if (not contest["attended"]):
                continue
            #print("attended another contest")
            dates.append(utils.convert_timestamp_to_date(contest["contest"]["startTime"]))
            points.append(int(contest["rating"]))

        if (len(dates) > 0):
            user_info_list.append([dates, points, user])

    if (len(user_info_list) > 0):
        chart_image = utils.create_line_chart(user_info_list)
        file = discord.File(fp=chart_image, filename='chart.png')
        await interaction.followup.send("Here is the rating over time chart:", files=[file])
    else:
        await interaction.followup.send("What a loser, " + str(usernames) + " hasn't even done a single LeetCode contest.")


# load data from server
asyncio.run(utils.load_question_data(check_server=True))
asyncio.run(utils.load_contest_info_data(check_server=True))

# Check server every 5 minutes
async def check_server():
    while True:
        await asyncio.sleep(300)
        await utils.load_question_data(check_server=True)
        await utils.load_contest_info_data(check_server=True)


test_bot = os.getenv("TESTING") == "True"
bot.run(token=(os.getenv('BOT_TOKEN') if not test_bot else os.getenv('TEST_BOT_TOKEN')))

import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import utils
import asyncio
load_dotenv()

bot = discord.Client(intents=discord.Intents.default())
tree = app_commands.CommandTree(bot)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        # Sync slash command tree
        synced = await tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

    

@tree.command(name="ping", description="Display latency information")
async def ping(interaction: discord.Interaction):
    text = f'Pong! {round (bot.latency * 1000)} ms initial.'
    # Initial ping message
    await interaction.response.send_message(text)
    msg = await interaction.original_response()

    # Edit the message with the latency of original response
    time = round((msg.created_at - interaction.created_at).total_seconds() * 1000)
    await msg.edit(content=text + f' {time} ms round-trip.')

# Displays a random leetcode problem, can specifiy if you want premium problems
@tree.command(name="random", description="Get a random question from LeetCode")
async def randomQuestion(interaction: discord.Interaction, allow_premium: bool = False):
    await interaction.response.send_message(await utils.random_question(allow_premium))

# Group for all contest related commands
contest = app_commands.Group(name="contest", description="Commands related to contests")


# Command to get problems from a specific contest
@contest.command(name="info", description="Get information about a specific contest")
@app_commands.choices(contest_type=[
    app_commands.Choice(name="Weekly", value="weekly"),
    app_commands.Choice(name="Biweekly", value="biweekly")
])
async def info(interaction: discord.Interaction, contest_type: app_commands.Choice[str] = None, contest_number: int = None):
    await interaction.response.send_message(await utils.get_contest_info(f"{contest_type.value}-contest-{contest_number}" if contest_type    else None))

tree.add_command(contest)

@tree.command(name="daily_time", description="sus", nsfw=True)
async def gif(interaction: discord.Interaction):
    await interaction.response.send_message("https://cdn.discordapp.com/attachments/1124365604523081748/1296155709393735853/leetcodedaily.gif?ex=6713e592&is=67129412&hm=fec412a88da2b6ff773ae3a8419c06efb9218119d9f63b8129797fae31087bba&")

# Force fetch question data
# asyncio.run(utils.load_question_data(True))
# asyncio.run(utils.load_contest_info_data(True))

bot.run(token=os.getenv('BOT_TOKEN'))
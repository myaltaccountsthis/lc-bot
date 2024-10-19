import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import utils
load_dotenv()

bot = discord.Client(intents=discord.Intents.default())
tree = discord.app_commands.CommandTree(bot)

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
    await interaction.response.send_message(utils.random_question(allow_premium))

# Group for all contest related commands
contest = discord.app_commands.Group(name="contest", description="Commands related to contests")

# Command to get problems from a specific contest
@contest.command(name="info", description="Get information about a specific contest", )
async def info(interaction: discord.Interaction, contest_slug: str = ""):
    await interaction.response.send_message(utils.get_contest_info(contest_slug))

tree.add_command(contest)
bot.run(token=os.getenv('BOT_TOKEN'))
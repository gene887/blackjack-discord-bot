import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import random
import asyncio

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='pls ', intents=intents)

player_bals = {}

deck = {
    "2♦": 2, "3♦": 3, "4♦": 4, "5♦": 5, "6♦": 6, "7♦": 7,
    "8♦": 8, "9♦": 9, "10♦": 10, "J♦": 10, "Q♦": 10, "K♦": 10, "A♦": 11,
 
    "2♣": 2, "3♣": 3, "4♣": 4, "5♣": 5, "6♣": 6, "7♣": 7,
    "8♣": 8, "9♣": 9, "10♣": 10, "J♣": 10, "Q♣": 10, "K♣": 10, "A♣": 11,
 
    "2♥": 2, "3♥": 3, "4♥": 4, "5♥": 5, "6♥": 6, "7♥": 7,
    "8♥": 8, "9♥": 9, "10♥": 10, "J♥": 10, "Q♥": 10, "K♥": 10, "A♥": 11,
 
    "2♠": 2, "3♠": 3, "4♠": 4, "5♠": 5, "6♠": 6, "7♠": 7,
    "8♠": 8, "9♠": 9, "10♠": 10, "J♠": 10, "Q♠": 10, "K♠": 10, "A♠": 11
}

def get_bal(user_id):
    return player_bals.setdefault(user_id, 1000.0)

def adjust_bal(user_id, amount):
    player_bals[user_id] = round(get_bal(user_id) + amount, 2)

def generate_random_unique_card(used):
    card = random.choice(list(deck.keys()))
    while card in used:
        card = random.choice(list(deck.keys()))
    used.append(card)
    return card

@bot.event
async def on_ready():
    print(f"We are ready to go, {bot.user.name}")


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    print(f"Message from {message.author}: {message.content}")
    await bot.process_commands(message)

@bot.command(name="blackjack")
async def blackjack(ctx):
    user_id = ctx.author.id
    used = []
    player_value = 0
    dealer_value = 0
    player_aces = []
    dealer_aces = []

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    async with ctx.typing():
        await ctx.send("How much do you bet? ")

    try:
        bet_msg = await bot.wait_for("message", check=check, timeout=60)
        bet = round(float(bet_msg.content), 2)
        if bet <= 0 or bet > get_bal(user_id):
            return
    except (ValueError, asyncio.TimeoutError):
        return

    async with ctx.typing():
        player_card1 = generate_random_unique_card(used)
        dealer_card1 = generate_random_unique_card(used)
        player_card2 = generate_random_unique_card(used)
        dealer_card2 = generate_random_unique_card(used)

        player_value += (deck[player_card1] + deck[player_card2])
        if player_value == 22:
            player_value = 12
            player_aces.append("A")
        elif deck[player_card1] == 11 or deck[player_card2] == 11:
            player_aces.append("A")

        dealer_value += (deck[dealer_card1] + deck[dealer_card2])
        if dealer_value == 22:
            dealer_value = 12
            dealer_aces.append("A")
        elif deck[dealer_card1] == 11 or deck[dealer_card2] == 11:
            dealer_aces.append("A")

        await ctx.send(f"Dealer's cards: {dealer_card1} + ? = ?")
        await ctx.send(f"Your cards: {player_card1} + {player_card2} = {player_value}")

    if player_value == 21 and dealer_value == 21:
        async with ctx.typing():
            await ctx.send("It's a Tie!")
        return
    elif player_value == 21 and dealer_value != 21:
        async with ctx.typing():
            await ctx.send("You win on Blackjack!")
        adjust_bal(user_id, round(bet * 1.5, 2))
        return
    elif dealer_value == 21 and player_value != 21:
        async with ctx.typing():
            await ctx.send("Dealer wins on Blackjack.")
        adjust_bal(user_id, -bet)
        return

    while player_value <= 21:
        async with ctx.typing():
            await ctx.send("Do you want to (h)it or (s)tand?")
        try:
            action_msg = await bot.wait_for("message", check=check, timeout=60)
            action = action_msg.content.lower()
        except asyncio.TimeoutError:
            adjust_bal(user_id, -bet)
            return

        if action in ("h", "hit"):
            async with ctx.typing():
                player_hit_card = generate_random_unique_card(used)
                player_value += deck[player_hit_card]
                while player_value > 21 and len(player_aces) > 0:
                    player_value -= 10
                    player_aces.pop(0)
                await ctx.send(f"You hit: {player_hit_card}\n= {player_value}")
                if player_value > 21:
                    await ctx.send("You bust, Dealer wins.")
            if player_value > 21:
                adjust_bal(user_id, -bet)
                return
        elif action in ("s", "stand"):
            async with ctx.typing():
                await ctx.send(f"You stand with: {player_value}")
                while dealer_value <= 16:
                    dealer_hit_card = generate_random_unique_card(used)
                    dealer_value += deck[dealer_hit_card]
                    while dealer_value > 21 and len(dealer_aces) > 0:
                        dealer_value -= 10
                        dealer_aces.pop(0)
                    await ctx.send(f"Dealer hits: {dealer_hit_card}")
                    await ctx.send(f"= {dealer_value}.")

                if dealer_value > 21:
                    await ctx.send("Dealer busts, You win!")
                    adjust_bal(user_id, round(bet))
                else:
                    await ctx.send(f"Dealer stands with: {dealer_value}.")
                    if 21 - player_value < 21 - dealer_value:
                        adjust_bal(user_id, bet)
                        await ctx.send(f"You win with: {player_value}!")
                    elif 21 - player_value > 21 - dealer_value:
                        adjust_bal(user_id, -bet)
                        await ctx.send(f"Dealer wins with: {dealer_value}.")
                    else:
                        await ctx.send("It's a Tie!")
            return
        else:
            adjust_bal(user_id, -bet)
            return

@bot.command(name="bal")
async def bal(ctx):
    async with ctx.typing():
        await ctx.send(f"{get_bal(ctx.author.id):.2f}")

bot.run(token, log_handler=handler, log_level=logging.DEBUG)
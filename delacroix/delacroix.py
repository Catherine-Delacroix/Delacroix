from redbot.core import commands
from redbot.core import Config
import asyncio
from collections import Counter
from random import choice, randint
import json
from recordclass import recordclass

import discord
from discord.ext import tasks
import datetime
from async_timeout import timeout
#from discord.ext import commands

from .cogs.utils import checks
from .cogs.utils.data import MemberConverter, NumberConverter, get, chain, create_pages, IntConverter
from .cogs.utils.translation import _, format_table

guildlist = []
# CHECK IF BAL[0] IS BANK OR HAND, SET TO BANK, REMOVE HAND FUNCTIONALITY

class Delacroix(commands.Cog):
    """My custom cog"""

    def __init__(self, bot):
        self.bot = bot
        self.bids = list()
        self.config = Config.get_conf(self, identifier=1234567890)
        default_global = {}
        default_guild = { 
            "market": {},
            "auctionchannel":{}
        }
        default_member = {
            "balance":0
        }
        self.config.register_global(**default_global)
        self.config.register_guild(**default_guild)
        self.config.register_member(**default_member)


    @tasks.loop(minutes=60)
    async def auctionchecks(self, ctx):
        for guild in guildlist:
            market = await self.config.guild(guild).market()
            channel = await self.config.guild(guild).auctionchannel()
            channel = guild.get_channel(channel['channel'])
            for id in market:
                date = datetime.datetime.utcnow()
                expire = id['expiration']
                if expire < date:
                    msg = await channel.get_partial_message(id['message'])
                    await msg.delete(msg)
                    await channel.send("{} has won {} for {} cash").format(id['user'].id, id['item'], id['cost'])

    @commands.command()
    async def getguild(self, ctx):
        guildlist = [ctx.guild]
        await ctx.send(ctx.guild)

    @commands.group(aliases=["bal", "balance", "eco", "e"], invoke_without_command=True)
    async def economy(self, ctx, *, member: discord.Member = None):
        """Check your or another users balance """

        dest = ctx.channel

        if member is None:
            member = ctx.author

#        gd = await self.bot.get_guild_data(ctx.guild)
        #balances = await self.config.member(ctx.author).balances()

        try:
            is_mod = checks.role_or_permissions(ctx,
                                                lambda r: r.name in ('Bot Mod', 'Bot Admin', 'Bot Moderator'),
                                                manage_server=True)
        except:
            is_mod = False

        #hide = gd.get("hideinv", False)

#        if not is_mod:
#            member = ctx.author

#        if hide:
#            dest = ctx.author

        bal = await self.config.member(member).balance()

        data = """Total:\t\t {} Lewds"""

        embed = discord.Embed(
            description=data.format(int(bal)),
            color=randint(0, 0xFFFFFF),
        )

        embed.set_author(name=member.display_name, icon_url=member.avatar_url)
        embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/761074204828631040.png?size=96")
        await dest.send(embed=embed)

    @checks.mod_or_permissions()
    @commands.command(aliases=["setb", "setbal"])
    async def setbalance(self, ctx, amount: NumberConverter, *members: MemberConverter):
        """Set the Lewds of the given members to an amount
        Example: !setbalance 500 everyone
        Example: !setbalance 500 @Henry#6174 @JohnDoe#0001
        Requires Bot Moderator or Bot Admin"""

        members = chain(members)

        for member in members:
            await self.config.member(member).balance.set(amount)

        await ctx.send("Balances changed")

    @checks.mod_or_permissions()
    @commands.command()
    async def givemoney(self, ctx, amount: NumberConverter, *members: MemberConverter):
        """Give the member's Lewds
        Example: !givemoney 5000 @Henry#6174 @JohnDoe#0001
        Example: !givemoney 50 everyone (or @\u200beveryone)
        Requires Bot Moderator or Bot Admin"""
        members = chain(members)

        for member in members:
            bal = await self.config.member(member).balance()
            final = amount + bal
            await self.config.member(member).balance.set(final)

        await ctx.send("Lewds given")

    @checks.mod_or_permissions()
    @commands.command()
    async def takemoney(self, ctx, amount: NumberConverter, *members: MemberConverter):
        """Take the user's Lewds
        Example: !takemoney 5000 @Henry#6174
        Requires Bot Moderator or Bot Admin"""
        members = chain(members)

        for member in members:
            bal = await self.config.member(member).balance()
            final = bal - amount
            await self.config.member(member).balance.set(final)
            await ctx.send("Lewds taken")

    @commands.command()
    async def pay(self, ctx, amount: NumberConverter, member: discord.Member):
        """Pay another user Lewds
        Example: rp!pay 500 @Henry#6174"""
        if ctx.author.bot:
            await ctx.send(
                await ("Bots don't have Lewds to pay other people! Use !givemoney instead of !pay"))
            return
        amount = abs(amount)

        ##Giver
        bal = await self.config.member(ctx.author).balance()
        final = bal - amount
        await self.config.member(ctx.author).balance.set(final)

        ##Receiver
        bal = await self.config.member(member).balance()
        final = bal + amount
        await self.config.member(member).balance.set(final)
        await ctx.send("Successfully paid {} Lewds to {}").format(amount, member)

    @commands.command(aliases=["createlisting", "new", "list"])
    async def create(self, ctx, item: str, cost: NumberConverter, picture: str, expires_in: int, *,description: str):
        """Create a new auction listing. The listing will return a unique identifier for the item.
         This is used to buy the item later.
        Example: !list item 500 pictureurl"""
        #try:
        cost = abs(cost)
        market = await self.config.guild(ctx.guild).market()
        expiration = datetime.datetime.now() + datetime.timedelta(hours=expires_in)

        id = str(randint(1000,9999))
        market[id] = dict(id=id, item=item, user=ctx.author.id, cost=cost, picture=picture, description=description, expiration=expiration)

        channel = await self.config.guild(ctx.guild).auctionchannel()
        channel = ctx.guild.get_channel(channel['channel'])
        #print(channel)

        embed = discord.Embed(description=description, title=market[id]['item'])
        #embed.set_author(name=market[id]['user'])
        embed.set_thumbnail(url=market[id]['picture'])
        embed.add_field(name='ID', value=market[id]['id'], inline=True)
        #embed.add_field(name='NAME', value=market[id]['item'], inline=True)
        embed.add_field(name='OWNER', value=f"<@{market[id]['user']}>", inline=True)
        embed.add_field(name='COST', value=market[id]['cost'], inline=True)
        embed.set_image(url = market[id]['picture'])
        footer = "Expires {} UTC".format(expiration)
        embed.set_footer(text=footer)

        message = await channel.send(embed = embed)
        market[id]['message'] = message.id
        await self.config.guild(ctx.guild).market.set(market)
        await ctx.send((await _(ctx, "Item listed with ID {}")).format(id))
        #except Exception:
        #    await ctx.send("Please check that you formatted the command correctly. Otherwise I'll spank you.")



    @commands.group(aliases=["m", "auction"], invoke_without_command=True)
    async def market(self, ctx):
        """View the current auction listings"""
        um = await self.config.guild(ctx.guild).market()
        market = list(um.values())
        desc = """\u27A1 to see the next page
                    \n\u2B05 to go back
                    \n\u274C to exit"""

        if not market:
            await ctx.send("No items on the market to display.")
            return

        emotes = ("\u2B05", "\u27A1", "\u274C")
        embed = discord.Embed(description=desc, title="User Market", color=randint(0, 0xFFFFFF), )
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)

        chunks = []
        clen = 1
        for i in range(0, len(market), clen):
            chunks.append(market[i:i + clen])

        i = 0
        try:
            users = [await ctx.guild.fetch_member(x['user']) for x in chunks[i]]
        except Exception:
            br = []
            fr = dict()
            for listing, data in um.items():
                for datum in data:
                    if 'item' not in listing:
                        id = str(randint(1000,9999))
                        fr[id] = dict(id=id, item=listing, user=ctx.author.id, cost=datum['cost'],
                                      picture=datum['picture'], description=datum['description'])
                br.append(listing)

            for i in br:
                del um[i]
            um.update(fr)

            market = list(um.items())
            chunks = []
            for i in range(0, len(market), clen):
                chunks.append(market[i:i + clen])

            users = get(ctx.guild.members, id=[x['user'] for x in chunks[i]])

        currency = "Lewds" #await ctx.bot.di.get_currency(ctx.guild)

        fin = [[x['id'], f"{x['cost']} {currency}", x['item'], str(y)] for x, y in
               zip(chunks[i], users)]
        image = [[x['picture']] for x , y in zip(chunks[i], users)][0][0]
        fin.insert(0, [await _(ctx, "ID"),
                       await _(ctx, "COST"),
                       await _(ctx, "ITEM"),
                       await _(ctx, "OWNER"),
                       await _(ctx, "DESCRIPTION")])
        #embed.description = "```\n{}\n```".format(format_table(fin))
        embed.set_thumbnail(url = image)
        embed.add_field(name= fin[0][2], value = fin[1][2])
        embed.add_field(name= fin[0][0], value = fin[1][0], inline=True)
        embed.add_field(name = fin[0][1], value = fin[1][1], inline=True)
        embed.add_field(name = fin[0][3], value = fin[1][3], inline=True)
        embed.add_field(name= fin[0][4], value = fin[1][4])
        footer = "Expires {} UTC".format(fin[1][5])
        embed.set_footer(text=footer)
        embed.set_image(url = image)

        max = len(chunks) - 1
        i = 0

        msg = await ctx.send(embed=embed)
        for emote in emotes:
            await msg.add_reaction(emote)

        while True:
            try:
                r, u = await self.bot.wait_for("reaction_add", check=lambda r, u: r.message.id == msg.id, timeout=80)
            except asyncio.TimeoutError:
                #await ctx.send("Timed out! Try again")
                #await msg.delete()
                return

            if u == ctx.guild.me:
                continue

            if u != ctx.author or r.emoji not in emotes:
                try:
                    await msg.remove_reaction(r.emoji, u)
                except:
                    pass
                continue

            if r.emoji == emotes[0]:
                if i == 0:
                    i = max#+1
                    #i -= 1
                else:
                    i -=1
                embed.clear_fields()
                users = get(ctx.guild.members, id=[x["user"] for x in chunks[i]])
                fin = [[x['id'], f"{x['cost']} dollars", x['item'], str(y)] for x, y in
                        zip(chunks[i], users)]
                image = [[x['picture']] for x , y in zip(chunks[i], users)][0][0]
                fin.insert(0, [await _(ctx, "ID"),
                                await _(ctx, "COST"),
                                await _(ctx, "ITEM"),
                                await _(ctx, "OWNER"),
                                await _(ctx, "DESCRIPTION")])
                #embed.description = "```\n{}\n```".format(format_table(fin))
                embed.set_thumbnail(url = image)
                embed.add_field(name= fin[1][2], value = fin[1][2])
                embed.add_field(name= fin[0][0], value = fin[1][0], inline=True)
                embed.add_field(name = fin[0][1], value = fin[1][1], inline=True)
                embed.add_field(name = fin[0][3], value = fin[1][3], inline=True)
                embed.add_field(name= fin[0][4], value = fin[1][4])
                footer = "Expires {} UTC".format(fin[1][5])
                embed.set_footer(text=footer)
                embed.set_image(url = image)

                await msg.edit(embed=embed)
                await msg.remove_reaction(emotes[0], u)

            elif r.emoji == emotes[1]:
                if i == max:
                    i = 0#-1
                    #i += 1
                else:
                    i += 1
                embed.clear_fields()
                users = get(ctx.guild.members, id=[x["user"] for x in chunks[i]])
                fin = [[x['id'], f"{x['cost']} dollars", x['item'], str(y)] for x, y in
                        zip(chunks[i], users)]
                image = [[x['picture']] for x , y in zip(chunks[i], users)][0][0]
                fin.insert(0, [await _(ctx, "ID"),
                                await _(ctx, "COST"),
                                await _(ctx, "ITEM"),
                                await _(ctx, "OWNER"),
                                await _(ctx, "DESCRIPTION")])
                #embed.description = "```\n{}\n```".format(format_table(fin))
                embed.set_thumbnail(url = image)
                embed.add_field(name= fin[1][2], value = fin[1][2])
                embed.add_field(name= fin[0][0], value = fin[1][0], inline=True)
                embed.add_field(name = fin[0][1], value = fin[1][1], inline=True)
                embed.add_field(name = fin[0][3], value = fin[1][3], inline=True)
                embed.add_field(name= fin[0][4], value = fin[1][4])
                footer = "Expires {} UTC".format(fin[1][5])
                embed.set_footer(text=footer)
                embed.set_image(url = image)

                await msg.edit(embed=embed)
                await msg.remove_reaction(emotes[1], u)
            else:
                await msg.delete()
                #await ctx.send("Closing")
                return

            try:
                await msg.remove_reaction(r.emoji, u)
            except:
                pass

    @commands.command()
    async def bid(self, ctx, id:str, cost: NumberConverter):
        """Place a bid on a item at the auction. Example: !bid itemname 500"""

        market = await self.config.guild(ctx.guild).market()
        bal = await self.config.member(ctx.author).balance()
        channel = await self.config.guild(ctx.guild).auctionchannel()
        channel = ctx.guild.get_channel(channel['channel'])
        msg = await channel.get_partial_message(market[id]['message'])

        if cost > market[id]['cost']:
            if bal < market[id]['cost']:
                await ctx.send("You don't have enough funds.")
            else:
                market[id]['cost'] = cost
                market[id]['user'] = ctx.author.id
                await self.config.guild(ctx.guild).market.set(market)
                await ctx.send("Your bid was successful. Good luck.")
                
                embed = msg.embeds[0]
                embed.set_field_at(1, name="OWNER", value=f"<@{market[id]['user']}>", inline=True)
                embed.set_field_at(2, name="COST", value=market[id]['cost'], inline=True)
                await msg.edit(embed=embed)
        else:
            await ctx.send("Your bid isn't high enough.")

    @commands.command()
    async def resetmarket(self, ctx):
        empty = {}
        await self.config.guild(ctx.guild).market.set(empty)
        await ctx.send("Market cleared.")
    
    @checks.mod_or_permissions()
    @commands.command()
    async def setauctionchannel(self, ctx, channel:discord.TextChannel):
        auctionchannel = {'channel': channel.id}
        await self.config.guild(ctx.guild).auctionchannel.set(auctionchannel)
        await ctx.send("Channel set successfully.")
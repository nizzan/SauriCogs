import asyncio
import discord
import datetime

from discord.utils import get

from redbot.core import Config, checks, commands
from redbot.core.utils.predicates import MessagePredicate
from redbot.core.utils.chat_formatting import humanize_list

from redbot.core.bot import Red


class Application(commands.Cog):
    """
    Receive and moderate staff applications with customizable questions.
    """

    __version__ = "2.0.0a"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(
            self, 5641654654621651651, force_registration=True
        )
        self.config.register_guild(
            applicant_id=None,
            accepter_id=None,
            channel_id=None,
            applications={},
            message_id=None,
        )

    async def red_delete_data_for_user(self, *, requester, user_id):
        # nothing to delete
        return

    def format_help_for_context(self, ctx: commands.Context) -> str:
        context = super().format_help_for_context(ctx)
        return f"{context}\n\nVersion: {self.__version__}"

    @commands.max_concurrency(1, commands.BucketType.member, wait=True)
    @commands.command()
    @commands.guild_only()
    @checks.bot_has_permissions(manage_roles=True)
    async def apply(self, ctx: commands.Context):
        """Apply to be a staff member."""
        # TODO delete
        if not await self.config.guild(ctx.guild).channel_id():
            return await ctx.send(
                "Uh oh, the configuration is not correct. Ask the Admins to set it."
            )

        role_add = None
        channel = None

        if await self.config.guild(ctx.guild).applicant_id():
            try:
                role_add = ctx.guild.get_role(
                    await self.config.guild(ctx.guild).applicant_id()
                )
            except TypeError:
                pass
            if not role_add:
                role_add = get(ctx.guild.roles, name="Staff Applicant")
                if not role_add:
                    return await ctx.send(
                        "Uh oh, the configuration is not correct. Ask the Admins to set it."
                    )
        try:
            channel = ctx.guild.get_channel(
                await self.config.guild(ctx.guild).channel_id()
            )
        except TypeError:
            pass
        if not channel:
            channel = get(ctx.guild.text_channels, name="applications")
            if not channel:
                return await ctx.send(
                    "Uh oh, the configuration is not correct. Ask the Admins to set it."
                )

        try:
            await ctx.author.send("Let's start right away!")
        except discord.Forbidden:
            return await ctx.send(
                "I don't seem to be able to DM you. Do you have closed DMs?"
            )
        await ctx.send(f"Okay, {ctx.author.mention}, I've sent you a DM.")

        embed = discord.Embed(
            color=await ctx.embed_colour(), timestamp=datetime.datetime.now()
        )
        embed.set_author(name="New application!", icon_url=ctx.author.avatar)
        embed.set_footer(
            text=f"{ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})"
        )
        embed.title = (
            f"User: {ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})"
        )

        def check(m):
            return m.author == ctx.author and m.channel == ctx.author.dm_channel

        hastebin_content = (
            f"New application in {ctx.guild.name} ({datetime.datetime.now()})\n\n"
            f"User: {ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})\n\n"
            "Questions:"
        )

        questions = await self.config.guild(ctx.guild).questions()  # list of lists
        default_questions = (
            await self._default_questions_list()
        )  # default list of lists just in case
        for i, question in enumerate(questions):  # for list in lists
            try:
                await ctx.author.send(question[0])
                timeout = question[2]
                shortcut = question[1]
            except TypeError:
                await ctx.author.send(default_questions[i][0])
                timeout = default_questions[i][2]
                shortcut = default_questions[i][1]
            try:
                answer = await self.bot.wait_for(
                    "message", timeout=timeout, check=check
                )
            except asyncio.TimeoutError:
                return await ctx.author.send("You took too long. Try again, please.")
            embed.add_field(name=shortcut + ":", value=answer.content)
            hastebin_content += f"\n{shortcut}:\t{answer.content}"

        try:
            await channel.send(embed=embed)
        except discord.errors.HTTPException:
            import requests
            import json

            req = requests.post("https://hastebin.com/documents", data=hastebin_content)
            key = json.loads(req.content)["key"]
            await channel.send(
                content=(
                    f"New application has been submitted by {ctx.author.mention}\n"
                    f"This application is too long, so here's a link to hastebin: https://hastebin.com/{key}"
                )
            )

        if role_add:
            await ctx.author.add_roles(role_add)
        await ctx.author.send(
            "Your application has been sent to the Admins, thank you!"
        )

    @commands.command()
    async def sendappl(self, ctx):
        # TODO rewrite
        class MyModal(discord.ui.Modal, title="Staff application"):
            position = discord.ui.TextInput(label="Position")
            # name = discord.ui.TextInput(label="Name")
            age = discord.ui.TextInput(label="Age")
            timezone = discord.ui.TextInput(label="Timezone")
            active_hours = discord.ui.TextInput(label="Active hours per day")
            # active_days = discord.ui.TextInput(label="Active days per week")
            experience = discord.ui.TextInput(label="Previous experience", style=discord.TextStyle.paragraph)
            # reason = discord.ui.TextInput(label="Reason for applying", style=discord.TextStyle.paragraph)

            async def on_submit(self, interaction):
                author = interaction.user
                await interaction.response.send_message(f"Thanks for applying, {author.name}!", ephemeral=True)
                # await interaction.client.send_to_owners(content=f"User: {self.name}\nResponse: {self.answer}")
                embed = discord.Embed(timestamp=datetime.datetime.now())
                embed.title = "New application!"
                embed.set_footer(
                    text=f"{author.name}#{author.discriminator} ({author.id})",
                    icon_url=author.avatar
                )
                embed.add_field(name="Position:", value=self.position)
                # embed.add_field(name="Name", value=self.name)
                embed.add_field(name="Age", value=self.age)
                embed.add_field(name="Timezone", value=self.timezone)
                embed.add_field(name="Active hours/day", value=self.active_hours)
                # embed.add_field(name="Active days/week", value=self.active_days)
                embed.add_field(name="Previous experience", value=self.experience, inline=False)
                # embed.add_field(name="Reason", value=self.reason, inline=False)
                await interaction.client.send_to_owners(embed=embed)

        class MyView(discord.ui.View):
            @discord.ui.button(label="Apply", style=discord.ButtonStyle.gray)
            async def button_callback(self, interaction, button):
                await interaction.response.send_modal(MyModal())

        await ctx.send(content="Click that shit!", view=MyView())

    # @checks.admin_or_permissions(administrator=True)
    @commands.group(autohelp=True, aliases=["setapply", "applicationset"])
    @commands.guild_only()
    # @checks.bot_has_permissions(manage_channels=True, manage_roles=True)
    async def applyset(self, ctx: commands.Context):
        """Various Application settings."""

    @applyset.group(autohelp=True, name="positions")
    async def applyset_positions(self, ctx: commands.Context):
        """Manage open positions."""

    @applyset_positions.command(name="add")
    async def applyset_positions_add(self, ctx: commands.Context, role: discord.Role):
        """Add a new open position."""
        same_context = MessagePredicate.same_context(ctx)
        valid_bool = MessagePredicate.yes_or_no(ctx)

        list_of_questions = []
        for _ in range(5):
            question_list = []

            await ctx.send("Enter a question (keep it under 45 characters): ")
            while True:
                try:
                    custom_question = await self.bot.wait_for(
                        "message", timeout=60, check=same_context
                    )
                except asyncio.TimeoutError:
                    return await ctx.send("You took too long. Try again, please.")
                if len(custom_question.content) <= 45:
                    break
            question_list.append(custom_question.content)

            await ctx.send("Do you expect a long answer? (yes/no)")
            try:
                await self.bot.wait_for("message", timeout=30, check=valid_bool)
            except asyncio.TimeoutError:
                return await ctx.send("You took too long. Try again, please.")
            question_list.append(valid_bool.result)

            list_of_questions.append(question_list)

        await self.config.guild(ctx.guild).applications.set_raw(
            role.id, value={"questions": list_of_questions}
        )
        await ctx.send("Done.")

    @applyset_positions.command(name="remove", aliases=["del", "rem", "delete"])
    async def applyset_positions_del(self, ctx: commands.Context, role: discord.Role):
        applications = await self.config.guild(ctx.guild).applications()
        if role.id not in applications:
            return await ctx.send("I have no records of this position.")
        await self.config.guild(ctx.guild).applications.clear_raw(role.id)
        await ctx.send("Done.")

    @applyset.command(name="applicant")
    async def applyset_applicant(
        self, ctx: commands.Context, role: discord.Role = None
    ):
        """Set the Staff Applicant role.

        If `role` is not provided, applicants will not get any role."""
        if role:
            await self.config.guild(ctx.guild).applicant_id.set(role.id)
        else:
            await self.config.guild(ctx.guild).applicant_id.set(None)
        await ctx.tick()

    @applyset.command(name="accepter")
    async def applyset_accepter(self, ctx: commands.Context, role: discord.Role = None):
        """Set the role that can accept/reject applications.

        If `role` is not provided, defaults to guild administrators."""
        if role:
            await self.config.guild(ctx.guild).accepter_id.set(role.id)
        else:
            await self.config.guild(ctx.guild).accepter_id.set(None)
        await ctx.tick()

    @applyset.command(name="channel")
    async def applyset_channel(
        self, ctx: commands.Context, channel: discord.TextChannel = None
    ):
        """Set the channel where applications will be sent.

        If `channel` is not provided, applications are disabled."""
        if channel:
            await self.config.guild(ctx.guild).channel_id.set(channel.id)
            await channel.set_permissions(
                ctx.guild.me, read_messages=True, send_messages=True
            )
        else:
            await self.config.guild(ctx.guild).channel_id.set(None)
        await ctx.tick()

    @applyset.command(name="settings")
    async def applyset_settings(self, ctx: commands.Context):
        """See current settings."""
        data = await self.config.guild(ctx.guild).all()
        channel = ctx.guild.get_channel(data["channel_id"])
        channel = channel.mention if channel else "None"
        accepter = ctx.guild.get_role(data["accepter_id"])
        accepter = accepter.name if accepter else "None (guild admins)"
        applicant = ctx.guild.get_role(data["applicant_id"])
        applicant = applicant.name if applicant else "None"
        positions = humanize_list([ctx.guild.get_role(int(role_id)).name for role_id in list(data["applications"])])
        embed = discord.Embed(
            colour=await ctx.embed_colour(), timestamp=datetime.datetime.now()
        )
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
        embed.set_footer(text="*required to function properly")

        embed.title = "**__Application settings:__**"
        embed.add_field(name="Channel*:", value=channel)
        embed.add_field(name="Accepter:", value=accepter)
        embed.add_field(name="Applicant:", value=applicant)
        embed.add_field(name="Positions:", value=positions)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    @checks.bot_has_permissions(manage_roles=True)
    async def accept(self, ctx: commands.Context, target: discord.Member):
        """Accept a staff applicant.

        <target> can be a mention or an ID."""
        if not await self.config.guild(ctx.guild).channel_id():
            return await ctx.send(
                "Uh oh, the configuration is not correct. Ask the Admins to set it."
            )

        try:
            accepter = ctx.guild.get_role(
                await self.config.guild(ctx.guild).accepter_id()
            )
        except TypeError:
            accepter = None
        if (
            not accepter
            and not ctx.author.guild_permissions.administrator
            or (accepter and accepter not in ctx.author.roles)
        ):
            return await ctx.send("Uh oh, you cannot use this command.")

        applicant = None
        if await self.config.guild(ctx.guild).applicant_id():
            try:
                applicant = ctx.guild.get_role(
                    await self.config.guild(ctx.guild).applicant_id()
                )
            except TypeError:
                applicant = None
            if not applicant:
                applicant = get(ctx.guild.roles, name="Staff Applicant")
            if not applicant:
                return await ctx.send(
                    "Uh oh, the configuration is not correct. Ask the Admins to set it."
                )
            if applicant not in target.roles:
                return await ctx.send(
                    f"Uh oh. Looks like {target.mention} hasn't applied for anything."
                )

        await ctx.send(f"What role do you want to accept {target.name} as?")
        role = MessagePredicate.valid_role(ctx)
        try:
            await self.bot.wait_for("message", timeout=30, check=role)
        except asyncio.TimeoutError:
            return await ctx.send("You took too long. Try again, please.")
        role_add = role.result
        try:
            await target.add_roles(role_add)
        except discord.Forbidden:
            return await ctx.send(
                "Uh oh, I cannot give them the role. It might be above all of my roles."
            )
        if applicant:
            await target.remove_roles(applicant)
        await ctx.send(f"Accepted {target.mention} as {role_add}.")
        await target.send(f"You have been accepted as {role_add} in {ctx.guild.name}.")

    @commands.command()
    @commands.guild_only()
    @checks.bot_has_permissions(manage_roles=True)
    async def deny(self, ctx: commands.Context, target: discord.Member):
        """Deny a staff applicant.

        <target> can be a mention or an ID"""
        if not await self.config.guild(ctx.guild).channel_id():
            return await ctx.send(
                "Uh oh, the configuration is not correct. Ask the Admins to set it."
            )

        try:
            accepter = ctx.guild.get_role(
                await self.config.guild(ctx.guild).accepter_id()
            )
        except TypeError:
            accepter = None
        if (
            not accepter
            and not ctx.author.guild_permissions.administrator
            or (accepter and accepter not in ctx.author.roles)
        ):
            return await ctx.send("Uh oh, you cannot use this command.")

        applicant = None
        if await self.config.guild(ctx.guild).applicant_id():
            try:
                applicant = ctx.guild.get_role(
                    await self.config.guild(ctx.guild).applicant_id()
                )
            except TypeError:
                applicant = None
            if not applicant:
                applicant = get(ctx.guild.roles, name="Staff Applicant")
                if not applicant:
                    return await ctx.send(
                        "Uh oh, the configuration is not correct. Ask the Admins to set it."
                    )
            if applicant not in target.roles:
                return await ctx.send(
                    f"Uh oh. Looks like {target.mention} hasn't applied for anything."
                )

        await ctx.send("Would you like to specify a reason? (yes/no)")
        pred = MessagePredicate.yes_or_no(ctx)
        try:
            await self.bot.wait_for("message", timeout=30, check=pred)
        except asyncio.TimeoutError:
            return await ctx.send("You took too long. Try again, please.")
        if pred.result:
            await ctx.send("Please, specify your reason now.")

            def check(m):
                return m.author == ctx.author

            try:
                reason = await self.bot.wait_for("message", timeout=120, check=check)
            except asyncio.TimeoutError:
                return await ctx.send("You took too long. Try again, please.")
            await target.send(
                f"Your application in {ctx.guild.name} has been denied.\n*Reason:* {reason.content}"
            )
        else:
            await target.send(f"Your application in {ctx.guild.name} has been denied.")
        if applicant:
            await target.remove_roles(applicant)
        await ctx.send(f"Denied {target.mention}'s application.")

    async def _default_questions_list(self):
        return [
            ["What position are you applying for?", "Position", 120],
            ["What is your name?", "Name", 120],
            ["How old are you?", "Age", 120],
            ["What timezone are you in? (Google is your friend.)", "Timezone", 120],
            ["How many days per week can you be active?", "Active days/week", 120],
            ["How many hours per day can you be active?", "Active hours/day", 120],
            [
                "Do you have any previous experience? If so, please describe.",
                "Previous experience",
                120,
            ],
            ["Why do you want to be a member of our staff?", "Reason", 120],
        ]

    async def _default_questions_string(self):
        list_of_questions = await self._default_questions_list()
        string = "**Default questions:**"
        for question in list_of_questions:
            string += "\n" + question[0]
        return string

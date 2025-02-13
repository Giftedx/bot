from discord.ext import commands

class TaskCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def create_task(self, ctx, *, task_description: str):
        """Creates a new task."""
        #Dummy task creation. Replace with the correct service call once we define Task Service.
        task_id = hash(task_description)
        await ctx.send(f"Task created: {task_id}")
        #Example for the service to use once implemented
        # task = await self.task_service.create_task({
        #     'description': task_description,
        #     'created_by': ctx.author.id
        # })
        # await ctx.send(f"Task created: {task.id}")

def setup(bot):
    bot.add_cog(TaskCog(bot))
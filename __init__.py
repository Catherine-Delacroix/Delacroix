from .delacroix import Delacroix


def setup(bot):
    bot.add_cog(Delacroix(bot))
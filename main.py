# -*- coding: utf-8 -*-

# Python Libraries
import json
import re
import asyncio
import os, argparse
import time
from datetime import date, datetime
import secrets
import traceback, logging
import random

# External Libraries
import discord
from discord.ext import commands, tasks
import sentry_sdk

# Bot Commands
import bot_commands

# Define Logger
logger = logging.getLogger('bot')
logger.setLevel(logging.DEBUG)
_formatter = logging.Formatter('[%(asctime)s; %(levelname)s] %(message)s','%Y-%m-%d %H:%M:%S')
_stream_handler = logging.StreamHandler()
_stream_handler.setFormatter(_formatter)
logger.addHandler(_stream_handler)

# Import Keys
with open('./keys.json', 'r') as keyFile:
    key = json.loads(keyFile.read())

with open('./registered_servers.json', 'r') as serverFile:
    server_list = json.loads(serverFile.read())
    
    

def input_logger(message):
        # input : class message of discord.py
    with open(os.path.join('bot log', str(date.today()) + '.log'), mode='a', newline='\r\n') as logfile:
        logfile.write('[' + str(time.strftime('%H:%M:%S')) + ' ' + message.guild.name + '#'
                      + message.channel.name + ' ' + str(message.author) + ']' + message.content)
        if message.embeds:
            for embed in message.embeds:
                logfile.write(str(embed.to_dict()) + ' ')
        logfile.write('\n')
        

def guild_check(id):
    return server_list.get(str(id))

def guild_add(id):
    server_list[str(id)] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open ('./registered_servers.json', 'w') as serverFile:
        serverFile.write(json.dumps(server_list, indent=2, ensure_ascii=False))

def guild_delete(id):
    del(server_list[str(id)])
    with open ('./registered_servers.json', 'w') as serverFile:
        serverFile.sritE(json.dumps(server_list, indent=2, ensure_ascii=False))

# Define Bot
bot = commands.Bot(command_prefix=commands.when_mentioned_or('!'), description='FF14')


@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online, activity=discord.Game(name='ff14.tar.to'))
    logger.info('Discord bot logged in as {}({}) at {}'.format(bot.user.name, bot.user.id, str(datetime.now())))
        
        
@bot.event
async def on_message(message):
    if message.author.bot and not message.author == bot.user:
        return
    if not message.guild:
        return
    cog = bot.get_cog('BotCog')
    if cog.test_mode and not message.guild.id == key['test_server_ID']:
        return
    else:
        logger.debug('{} - {} - {} : {}'.format(message.guild.name, message.channel.name, message.author, message.content))
        if message.embeds:
            for embed in message.embeds:
                logger.debug(embed.to_dict())
        if message.author.id == key['admin'] and\
           message.content.startswith('!!봇종료'):
                input_logger(message)
                await bot.close()
        with sentry_sdk.configure_scope() as scope:
            scope.set_extra('Message Content', message.content)
            first_word = message.content.split()[0]
            print(first_word)
            if first_word.startswith('!') and bot_commands.get_command_name(first_word):
                input_logger(message)
                if not guild_check(message.guild.id):
                    guild_add(message.guild.id)
                    await message.channel.send('*(2020년 8월 2일 이전에 추가해두셨던 서버에도 본 메시지가 발송됩니다)\n안녕하세요! FFXIV-ZnBot을 추가해주셔서 감사합니다. \n' +\
                                               '본 봇을 계속해서 사용하시는 것은 본 봇의 개인정보처리방침에 동의하신 것으로 간주됩니다. ' +\
                                               '{} 에 방문하셔서 반드시 개인정보처리방침을 읽으신 후 봇을 사용하시기를 부탁드립니다. \n'.format(key['bot_webpage']) +\
                                               '봇의 모든 기능을 알아보시려면 `!도움말` 을 입력해 주세요.\n'+\
                                               '오류가 발생했을 경우 트위터에서 관련 공지를 안내해드리고 있습니다: https://twitter.com/ffxiv_znbot*')
            if   message.author == bot.user:
                input_logger(message)
            await bot.process_commands(message)
            
        

@bot.event
async def on_guild_remove(guild):
    guild_delete(guild.id)


class BotCog(commands.Cog):
    def __init__(self, bot, args_test):
        self.bot = bot
        self.bot.remove_command('help')
        self.last_chat = None
        self.test_mode = args_test
        
    
    # Bot Commands
    @commands.command(name='주사위', help='주사위를 굴립니다.')
    async def dice(self, ctx, *args):
        message, embed = bot_commands.dice(args)
        await self.send_message(ctx.message.channel, message)
        
    
    @commands.command(name='선택', help='선택지 중에서 고릅니다.')
    async def selector(self, ctx, *args):
        message, embed = bot_commands.selector(args)
        await self.send_message(ctx.message.channel, message)

        
    @commands.command(name='판매정보', help='아이템을 구입할 수 있는 방법을 알려줍니다.',
                      aliases=['판매검색', '판매', '교환정보', '교환검색', '교환'])
    async def item_sellers(self, ctx, *args):
        message, embed = bot_commands.item_sellers(args)
        if embed:
            embed = self.get_embed(title=embed[0], description=embed[1],
                                  url=embed[2], thumb_url=embed[3], list_of_fields=embed[4:])
        await self.send_message(ctx.message.channel, message, embed)
    
    @commands.command(name='도움말', help='도움말', aliases=['도움'])
    async def custom_help(self, ctx, *args):
        message, embed = bot_commands.help(args)
        embed = self.get_embed(title=embed[0], description=embed[1],
                               url=embed[2], thumb_url=embed[3], list_of_fields=embed[4:])
        await self.send_message(ctx.message.channel, message, embed)


    # Bot Functions
    def get_embed(self, title, description, url='', thumb_url='', list_of_fields=[]):
        '''
        LIST OF FIELDS IS A LIST CONTAINING DICTIONARY WITH 3 KEYS: name, value, inline
        '''
        embed = discord.Embed(title=title,
                              description=description,
                              url=url,
                              colour=0x787978)
        for field in list_of_fields:
            embed.add_field(name=field['name'],
                            value=field['value'],
                            inline=field.get('inline', False))
        if thumb_url:
            embed.set_thumbnail(url=thumb_url)
        if url:
            embed.set_footer(text='정보 제공: 타르토맛 타르트',
                             icon_url='https://pbs.twimg.com/profile_images/938004116348870656/Zb9fvk1z_400x400.jpg')
            
        return embed
    


    async def send_message(self, channel, message, embed_object=None):
        message = '*' + message + '*'
        if embed_object:
            await channel.send(message, embed=embed_object)
        else:
            await channel.send(message)


    


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run the Discord bot.')
    parser.add_argument('--test', help='Send the output to the test guild. (Default: Send to live guild)',
                        action='store_true')
    parser.add_argument('--debug', help='Print the log from debug level into the local terminal. (Default: From warning level)',
                        action='store_true')
    args = parser.parse_args()
    
    if not os.path.exists('./bot log'):
        os.makedirs('./bot log')
    if not args.debug:
        logger.setLevel(logging.INFO)
        sentry_sdk.init(key['sentry_key'])
    logger.debug('test: {}, debug: {}'.format( args.test, args.debug))
    logger.info('Starting FFXIVbot-catdog...')
    try:
        bot.add_cog(BotCog(bot, args.test))
        bot.run(key['bot_token'])
    except:
        logger.error(traceback.format_exc())
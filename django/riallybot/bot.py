from telegram import Update

import settings
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
import logging
import pickle
import json
import os
import re
import random
import string
from datetime import datetime

updater = Updater(token=settings.TOKEN)
media_path = "/data/htdocs_committees/rially/media"
python_path = "/data/environment/rially/bin/python"
dispatcher = updater.dispatcher
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

def is_submission_open():
    response = os.popen("{} manage.py telegram-submitstate".format(python_path)).read()
    return json.loads(response)["state"]

def msg(update: Update, context, txt):
    context.bot.send_message(chat_id=update.effective_chat.id, text=str(txt))

def msg_formatted(update: Update, context, txt, mode="Markdown"):
    context.bot.send_message(chat_id=update.effective_chat.id, text=str(txt), parse_mode=mode)

def start(update: Update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text= \
        f"Welcome to the Rially of {datetime.now().year}! \nPlease log in with /login [token]")


def logout(update: Update, context):
    response = os.popen("{} manage.py telegram-unregister --chatid ".format(python_path) + \
                        str(update.effective_chat.id)).read()
    context.bot.send_message(chat_id=update.effective_chat.id, text= \
        "You succesfully logged out. "
        + str(update.effective_chat.id))
    start(update, context)


def login(update: Update, context, args):
    # [A-Za-z0-9]{6}
    # [0-9]{5-15}
    if len(args) == 0:
        msg(update, context, "Please provide your token.")
        return
    token = args[0]
    pattern = re.compile("[A-Za-z0-9]{6}")
    if not pattern.match(token):
        msg(update, context, "This token is not valid.")
        return

    response = os.popen("{} manage.py telegram-register --token ".format(python_path) + token + \
                        " --chatid " + str(update.effective_chat.id)).read()
    response = json.loads(response)

    if not response['result']:
        msg(update, context, "This token is not valid.")
    else:
        msg(update, context, "Successfully registered as " + response['team'] + ". Use /logout to log out.")


def help(update: Update, context):
    response = os.popen("{} manage.py telegram-team --chatid ".format(python_path) + \
                        str(update.effective_chat.id)).read()
    try:
        response = json.loads(response)
    except json.decoder.JSONDecodeError:
        response = dict()
        response['in_team'] = False
    m = ""
    if response['in_team']:
        m = m + f"You are in team {response['team']}.\n\nTo submit a picture or video, send it to me with the correct code in the caption.\n" \
                f"Use e.g. `L-1` for location 1, `PL-1-1` for bonus picture 1, location 1, `TL1-1` for task 1, " \
                f"location 1 or `T-1` for task 1"
    else:
        m = m + "You are not in a team.\n\nTo log in, use /login [token]"
    msg_formatted(update, context, m)

def submit(update: Update, context):
    if not is_submission_open():
        msg(update, context, "Submissions have not opened yet!")
        return
    file_id = 0
    extension = ""
    if len(context.message.photo) > 0:
        file_id = context.message.photo[-1].file_id
        extension = ".jpg"
    elif context.message.video != None:
        file_id = context.message.video.file_id
        extension = ".mp4"
    else:
        msg(update, context, "No video or photo provided.")

    photo_file = update.get_file(file_id)
    name = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase \
                                 + string.digits) for _ in range(32)) + extension
    photo_file.download(os.path.join(media_path, name))


    pattern = re.compile("^(T|L|PL|TL)-\d{1,3}(-\d{1,3})?$")
    if context.message.caption is None or not pattern.match(context.message.caption):
        msg_formatted(update, context, f"Add the code of the task to the caption of the picture.\n" \
            f"Use e.g. `L-1` for location 1, `PL-1-1` for bonus picture 1, location 1, `TL1-1` for task 1, location 1 or `T-1` for task 1")
        os.popen("rm {}".format(os.path.join(media_path, name)))
        return

    command = "{} manage.py telegram-submit --filename {} \
        --chatid {} --id {}".format(python_path, name, update.effective_chat.id, context.message.caption)
    response = json.loads(os.popen(command).read())
    if response['result']:
        msg(update, context, "We received the submission successfully!\nPlease check the website to see its status.")
    else:
        msg(update, context, "Oops!\nThe following error occurred: {}".format(response['reason']))

def submit_open(update: Update, context):
    if is_submission_open():
        msg(update, context, "Submissions have opened!")
    else:
        msg(update, context, "Submissions are closed now.")


start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

# We can also receive videos! (don't forget frontend)
msg_handler = MessageHandler(Filters.photo | Filters.video, submit)
dispatcher.add_handler(msg_handler)

team_handler = CommandHandler('login', login, pass_args=True)
dispatcher.add_handler(team_handler)

myteam_handler = CommandHandler('help', help)
dispatcher.add_handler(myteam_handler)

logout_handler = CommandHandler('logout', logout)
dispatcher.add_handler(logout_handler)

submit_open_handler = CommandHandler('open', submit_open)
dispatcher.add_handler(submit_open_handler)

updater.start_polling()

print("Successfully started the bot")

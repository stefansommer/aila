#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Aula AI
-------

This program is a part of the Aula AI project.

Author: Stefan Sommer
Email: sommer@di.ku.dk

The interface to Aula is written by Morten Helmstedt. E-mail: helmstedt@gmail.com
see https://helmstedt.dk/2021/05/aulas-api-en-opdatering/

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

import aula

from pathlib import Path
from gpt4all import GPT4All

import re
from datetime import datetime, timedelta
from dateutil import parser
import time
import json

# set up LLM
#model_name = 'mistral-7b-instruct-v0.1.Q4_0.gguf'
model_name = 'mistral-7b-openorca.Q4_0.gguf'
model_path = Path.home() / 'Library' / 'Application Support' / 'nomic.ai' / 'GPT4All'
model = GPT4All(model_name, model_path, allow_download=False)

system_template = 'A chat between a user and an artificial intelligence assistant. The user is a parent who has children in school and kindergarten. The parent receives messages from the school and kindergarten, but the parent is only interested in messages that are absolutely imporant: This could be birthday parties for his kids, or meetings with the teachers. The parent particularly dislikes messages that are not important. This could be long discussions between parents, or messages about other kids having lost some of their stuff. The parent only likes very short answers. '
prompt_template = '### Human: {0}\n### Assistant:' 

# read saved info from file
try:
    with open('aila.json', 'r') as file:
        store = json.load(file)
except:
    store = {'message_ids':[],'post_ids':[]}
#store = {'message_ids':[],'post_ids':[]} # debug

def get_data():
    # get data from aula
    aula_posts,aula_messages = aula.run()

    cutoff = lambda current_time: current_time - timedelta(days=4)
    posts = []
    msgs = []
    # extract data and generate responses
    for post in aula_posts['data']['posts']:
        try:
            if post['id'] in store['post_ids']:
                continue
            else:
                store['post_ids'].append(post['id'])
            title = post['title']
            text = re.sub('\n',' ',re.sub('<[^<]+?>', '', post['content']['html']) )
            sender = post['ownerProfile']['fullName']
            date_object = parser.parse(post['timestamp'])
            if date_object < cutoff(datetime.now(date_object.tzinfo)):
                continue

            with model.chat_session(system_template, prompt_template):
                summary = model.generate("Here is a message from the school: <begin message>%s</end message> Please make a one sentence summary" % text)
                important = model.generate("Does the message contain important information? Please answer 'yes' or 'no'")

            summary = re.sub(r"###.*", "", summary) # string prompt if included in response
            important = 'yes' in important.lower()
            #print("%s, %s: %s,%s\n" % (title,sender,summary,important))
            posts.append({'title':title,'sender':sender,'text':text,'response':summary,'important':important})
        except:
            pass

    for thread in aula_messages['data']['threads']:
        try:
            msg = thread['latestMessage']
            if msg['id'] in store['message_ids']:
                continue
            else:
                store['message_ids'].append(msg['id'])
            title = thread['subject']
            text = re.sub('\n',' ',re.sub('<[^<]+?>', '', msg['text']['html']) )
            sender = thread['creator']['fullName']
            date_object = parser.parse(msg['sendDateTime'])
            if date_object < cutoff(datetime.now(date_object.tzinfo)):
                continue

            with model.chat_session(system_template, prompt_template):
                summary = model.generate("Here is a message from the school: <begin message>%s</end message> Please make a one sentence summary" % text)
                important = model.generate("Does the message contain important information? Please answer 'yes' or 'no'")
            important = 'yes' in important.lower()
            summary = re.sub(r"###.*", "", summary) # string prompt if included in response
            #print("%s, %s: %s\n" % (title,sender,summary))
            msgs.append({'title':title,'sender':sender,'text':text,'response':summary,'important':important})
        except:
            pass

    # save store to file
    with open('aila.json', 'w') as file:
        json.dump(store, file)

    return posts, msgs

# output to user
def update_aila():
    posts, msgs = get_data()
    #posts, msgs = [],[]
    #posts = [{'title':'title','sender':'sender','text':'text','response':'response','important':True},
    #         {'title':'title','sender':'sender','text':'text','response':'response','important':False}]
    output = []
    important = False
    if posts:
        for post in posts:
            output.append(("%s, %s, %s: %s\n\n" % (post['title'],post['sender'],post['title'],post['response']),post['important']))
            important = important or post['important']
    if msgs:
        for msg in msgs:
            output.append(("%s, %s, %s: %s\n\n" % (msg['title'],msg['sender'],msg['title'],msg['response']),msg['important']))
            important = important or msg['important']

    original = ""
    if posts:
        for post in posts:
            original += "%s, %s: %s\n\n" % (post['title'],post['sender'],post['text'])
    if msgs:
        for msg in msgs:
            original += "%s, %s: %s\n\n" % (msg['title'],msg['sender'],msg['text'])

    # display on console and return
    return output,important,original

# display gui
import tkinter as tk
import tkinter.font as tkFont

# Create a Tkinter window
root = tk.Tk()
root.title("aila: AI for Aula")
output = "aila: AI for Aula\n\n"

# Set window size (width x height)
root.geometry("600x600")

## Create a label widget to display the text
#label = tk.Label(root, text=output, wraplength=600, anchor='nw', justify='left')
#label.pack(expand=True, fill="both")

# Create a Text widget and a Scrollbar
text_widget = tk.Text(root, wrap=tk.WORD, state=tk.DISABLED)
scrollbar = tk.Scrollbar(root, command=text_widget.yview)

# Configure the Text widget to work with the Scrollbar
text_widget.configure(yscrollcommand=scrollbar.set)
# Define a tag for bold text
default_font = tkFont.nametofont("TkTextFont")
bold_font = default_font.copy()
bold_font.configure(weight="bold")
text_widget.tag_configure("bold", font=bold_font)

# Layout the widgets in the window
text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

def update_text():
    output,important,original = update_aila()

    # Enable the widget to update the text
    text_widget.config(state=tk.NORMAL)
    text_widget.delete('1.0', tk.END)

    # For example, setting it to the current time or any other dynamic data
    if important:
        text_widget.insert(tk.END, "Some messages seems to be important.\n")
    if not important:
        text_widget.insert(tk.END, "No important messages found - you likely didn't miss anything.\n")
    text_widget.insert(tk.END, "Updated at " + time.strftime("%H:%M:%S") + ".\n\n")
    
    for (text,important) in output:
        # Insert the message followed by a newline
        text_widget.insert(tk.END, text + "\n")

        # If the message is important, apply the 'bold' tag
        if important:
            # The start index is the 'end' of text before inserting the message
            start_index = text_widget.index(f"{tk.END}-{len(text) + 2}c")
            # The end index is just before the newline character
            end_index = text_widget.index(f"{tk.END}-1c")
            text_widget.tag_add("bold", start_index, end_index)

    text_widget.insert(tk.END, "\n\n------ Original messages -------\n\n\n" + original)

    #text_widget.see(tk.END)
    # Disable the widget to prevent user editing
    text_widget.config(state=tk.DISABLED)
    
    # Schedule this function to run again after 1 hour (3600000 milliseconds)
    root.after(60*60*1000, update_text)

# Call update_text for the first time
root.after(1000, update_text)

# Start the GUI event loop
root.mainloop()
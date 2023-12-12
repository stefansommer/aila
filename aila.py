#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Aila: AI for Aula
-------

This program is a part of the Aila project.

Copyright (c) 2023 Stefan Sommer

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

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
model = GPT4All(model_name)
# If you already have the model downloaded
#model_path = Path.home() / 'Library' / 'Application Support' / 'nomic.ai' / 'GPT4All'
#model = GPT4All(model_name, model_path, allow_download=False)

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
    daily_summary = ""
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
                summary = model.generate("Here is a message: <begin message>%s</end message> Please make a one sentence summary" % text)
                important = model.generate("Does the message contain important information? Please answer 'yes' or 'no'")

            summary = re.sub(r"###.*", "", summary) # string prompt if included in response
            important = 'yes' in important.lower()
            #print("%s, %s: %s,%s\n" % (title,sender,summary,important))
            posts.append({'title':title,'sender':sender,'text':text,'response':summary,'important':important})

            if True and date_object > datetime.now(date_object.tzinfo)- timedelta(days=1):
                daily_summary += "<begin message>%s</end message>\n" % text
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
                summary = model.generate("Here is a message: <begin message>%s</end message> Please make a one sentence summary" % text)
                important = model.generate("Does the message contain important information? Please answer 'yes' or 'no'")
            important = 'yes' in important.lower()
            summary = re.sub(r"###.*", "", summary) # string prompt if included in response
            #print("%s, %s: %s\n" % (title,sender,summary))
            msgs.append({'title':title,'sender':sender,'text':text,'response':summary,'important':important})

            if True and date_object > datetime.now(date_object.tzinfo)- timedelta(days=1):
                daily_summary += "<begin message>%s</end message>\n" % text
        except:
            pass
    
    # make daily summary
    if daily_summary:
        with model.chat_session(system_template, prompt_template):
            daily_summary = model.generate("Here all todays messages from the school: %s\n Please make a short summary of the messages." % daily_summary)

    # save store to file
    with open('aila.json', 'w') as file:
        json.dump(store, file)

    return posts,msgs,daily_summary

# output to user
def update_aila():
    posts,msgs,daily_summary = get_data()
    #posts, msgs = [],[]
    #posts = [{'title':'title','sender':'sender','text':'text','response':'response','important':True},
    #         {'title':'title','sender':'sender','text':'text','response':'response','important':False}]
    output = []
    important = False
    if posts:
        for post in posts:
            output.append(("%s, %s, %s: %s\n" % (post['title'],post['sender'],post['title'],post['response']),post['important']))
            important = important or post['important']
    if msgs:
        for msg in msgs:
            output.append(("%s, %s, %s: %s\n" % (msg['title'],msg['sender'],msg['title'],msg['response']),msg['important']))
            important = important or msg['important']

    original = ""
    if posts:
        for post in posts:
            original += "%s, %s: %s\n\n" % (post['title'],post['sender'],post['text'])
    if msgs:
        for msg in msgs:
            original += "%s, %s: %s\n\n" % (msg['title'],msg['sender'],msg['text'])

    # display on console and return
    return output,important,original,daily_summary

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
def init_text():
    # initial text
    text_widget.config(state=tk.NORMAL)
    text_widget.delete('1.0', tk.END)
    text_widget.insert(tk.END, "Getting data from Aula and running LLM... (this might take a while)\n")
    text_widget.config(state=tk.DISABLED)

def update_text():
    # Enable the widget to update the text
    text_widget.config(state=tk.NORMAL)
    text_widget.delete('1.0', tk.END)
    text_widget.insert(tk.END, "Getting data from Aula and running LLM... (this might take a while)\n")
    # Disable the widget to prevent user editing
    text_widget.config(state=tk.DISABLED)

    # get data
    output,important,original,daily_summary = update_aila()
    #output = []; important = False; original = ""; daily_summary = ""

    # Enable the widget to update the text
    text_widget.config(state=tk.NORMAL)
    text_widget.delete('1.0', tk.END)

    text_widget.insert(tk.END, "Updated at " + time.strftime("%H:%M:%S") + ".\n\n")
    if important:
        text_widget.insert(tk.END, "Some messages seems to be important. You might want to check them out. ")
        if daily_summary:
            text_widget.insert(tk.END, "Summary:\n" + daily_summary + "\n\n\n")
        else:
            text_widget.insert(tk.END, "\n")
    if not important:
        text_widget.insert(tk.END, "No important messages found - you likely didn't miss anything.\n")
    
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


def run_task():
    # Scheduled task to run
    #print("Task running... " + datetime.now().isoformat())
    try:
        update_text()
    except Exception as e:
        print(e)

    #with open("last_run_time.json", "w") as file:
    #    # Save the current time as the last run time
    #    json.dump({"last_run": datetime.now().isoformat()}, file)

# last time check_run() was exectued
global last_run_time
last_run_time = datetime.now() - timedelta(hours=25)

def check_run():
    global last_run_time
    #try:
    #    with open("last_run_time.json", "r") as file:
    #        last_run_time = datetime.fromisoformat(json.load(file)["last_run"])
    #except (FileNotFoundError, ValueError, KeyError):
    #    last_run_time = datetime.now() - timedelta(hours=25)

    if datetime.now() - last_run_time > timedelta(hours=24):
        run_task()
        last_run_time = datetime.now()

    # Schedule the next check in 1 minute (60000 milliseconds)
    root.after(60000, check_run)

# Start the check loop
root.after(1000, init_text)
root.after(2000, check_run)

# Start the GUI event loop
root.mainloop()

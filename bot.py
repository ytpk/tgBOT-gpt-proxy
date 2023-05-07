import os
import telebot
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('API_KEY')
MODEL = os.getenv('MODEL')
context = {}
system_info = ""
ujb_info = ""

presets = {
    'one': {'system': os.getenv('SYSTEM_ONE'), 'ujb': os.getenv('UJB_ONE')},
    'two': {'system': os.getenv('SYSTEM_TWO'), 'ujb': os.getenv('UJB_TWO')},
    'three': {'system': os.getenv('SYSTEM_THREE'), 'ujb': os.getenv('UJB_THREE')}
}

bot = telebot.TeleBot(os.getenv('BOT_TOKEN'))

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome to the AI chatbot! Use the /ai command to chat with the bot.")

@bot.message_handler(commands=['ai'])
def send_ai_response(message):
    global context
    chat_id = message.chat.id
    if chat_id not in context:
        context[chat_id] = ""
    prompt = get_prompt(message.text[4:], message.from_user.id, chat_id)
    bot.send_chat_action(message.chat.id, 'typing')
    response = get_ai_response(prompt)
    context[chat_id] += f"\nuser{message.from_user.id}: {message.text[4:]}\n"
    context[chat_id] += f"ai: {response}\n"
    bot.reply_to(message, f"ai: {response}")

@bot.message_handler(commands=['system'])
def set_system_info(message):
    global system_info
    system_info = message.text[8:]
    bot.reply_to(message, "System info updated.")

@bot.message_handler(commands=['ujb'])
def set_ujb_info(message):
    global ujb_info
    ujb_info = message.text[4:]
    bot.reply_to(message, "UJB info updated.")

@bot.message_handler(commands=['clear'])
def clear_context(message):
    global context, system_info, ujb_info
    context = {}
    system_info = ""
    ujb_info = ""
    bot.reply_to(message, "Context, system info, and UJB info cleared.")

@bot.message_handler(commands=['preset'])
def set_preset(message):
    global system_info, ujb_info
    preset_name = message.text[8:]
    if preset_name not in presets:
        bot.reply_to(message, "Invalid preset name.")
        return
    preset = presets[preset_name]
    system_info = preset.get('system', '')
    ujb_info = preset.get('ujb', '')
    bot.reply_to(message, f"Preset '{preset_name}' applied.")

@bot.message_handler(func=lambda message: True, content_types=['text'])
def echo_message(message):
    global context
    chat_id = message.chat.id
    if message.reply_to_message and message.reply_to_message.from_user.id == bot.get_me().id:
        if chat_id not in context:
            context[chat_id] = ""
        prompt = get_prompt(message.text, message.from_user.id, chat_id)
        bot.send_chat_action(message.chat.id, 'typing')
        response = get_ai_response(prompt)
        context[chat_id] += f"\nuser{message.from_user.id}: {message.text}\n"
        context[chat_id] += f"ai: {response}\n"
        bot.reply_to(message, f"ai: {response}")

def get_prompt(user_input, user_id, chat_id):
    global context, system_info, ujb_info
    prompt = f"{context.get(chat_id, '')}user{user_id}: {user_input}\n"
    if system_info:
        prompt = f"[system: {system_info}]\n{prompt}"
    if ujb_info:
        prompt += f"[ujb: {ujb_info}]\n"
    prompt += " ai: "
    return prompt

def get_ai_response(prompt):
    response = requests.post(
        'http://127.0.0.1:5004/v1/chat/completions',
        headers={'Authorization': f'Bearer {API_KEY}'},
        json={'model': MODEL, 'messages': [{"role": "user", "content": prompt}], 'temperature': 0.5, 'max_tokens': 300},
        timeout=100
    )

    result=response.json()

    final_result=''
    for i in range(0,len(result['choices'])):
        final_result+=result['choices'][i]['message']['content']

    return final_result

bot.polling()

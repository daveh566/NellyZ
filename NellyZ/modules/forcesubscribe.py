#    Copyright (C) 2020-2021 by @Aspirer2
#    This programme is a part of Daisy TG bot project
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.


import logging
import time

from pyrogram import filters
from pyrogram.errors import RPCError
from pyrogram.errors.exceptions.bad_request_400 import (
    ChannelPrivate,
    ChatAdminRequired,
    PeerIdInvalid,
    UsernameNotOccupied,
    UserNotParticipant,
)
from pyrogram.types import ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup

from NellyZ import BOT_ID

# from NellyZ import OWNER_ID as SUDO_USERS
from NellyZ.services.pyrogram import pbot
from NellyZ.services.sql import forceSubscribe_sql as sql

logging.basicConfig(level=logging.INFO)

static_data_filter = filters.create(
    lambda _, __, query: query.data == "onUnMuteRequest"
)


@pbot.on_callback_query(static_data_filter)
def _onUnMuteRequest(client, cb):
    try:
        user_id = cb.from_user.id
        chat_id = cb.message.chat.id
    except:
        return
    chat_db = sql.fs_settings(chat_id)
    if chat_db:
        channel = chat_db.channel
        try:
            chat_member = client.get_chat_member(chat_id, user_id)
        except:
            return
        if chat_member.restricted_by:
            if chat_member.restricted_by.id == BOT_ID:
                try:
                    client.get_chat_member(channel, user_id)
                    client.unban_chat_member(chat_id, user_id)
                    cb.message.delete()
                    # if cb.message.reply_to_message.from_user.id == user_id:
                    # cb.message.delete()
                except UserNotParticipant:
                    client.answer_callback_query(
                        cb.id,
                        text=f"❗ JOIN OUR @{channel} CHANNEL AND PRESS 'UNMUTE ME' BUTTON.",
                        show_alert=True,
                    )
                except ChannelPrivate:
                    client.unban_chat_member(chat_id, user_id)
                    cb.message.delete()

            else:
                client.answer_callback_query(
                    cb.id,
                    text="❗ You have been muted by admins due to some other reason.",
                    show_alert=True,
                )
        else:
            if not client.get_chat_member(chat_id, BOT_ID).status == "administrator":
                client.send_message(
                    chat_id,
                    f"❗ **{cb.from_user.mention} is trying to UnMute himself but i can't unmute him because i am not an admin in this chat add me as admin again.**\n__#Leaving this chat...__",
                )

            else:
                client.answer_callback_query(
                    cb.id,
                    text="❗ Warning! DON'T PRESS THE BUTTON 😜 BECAUSE YOU HAVE ALREADY BEEN UNMUTED.",
                    show_alert=True,
                )


@pbot.on_message(filters.text & ~filters.private & ~filters.edited, group=1)
def _check_member(client, message):
    chat_id = message.chat.id
    chat_db = sql.fs_settings(chat_id)
    if chat_db:
        try:
            user_id = message.from_user.id
        except:
            return
        try:
            if (
                not client.get_chat_member(chat_id, user_id).status
                in ("administrator", "creator")
                and not user_id == 1141839926
            ):
                channel = chat_db.channel
                try:
                    client.get_chat_member(channel, user_id)
                except UserNotParticipant:
                    try:
                        sent_message = message.reply_text(
                            "WELCOME {} 🙏 \n **You HAVEN'T JOINED OUR @{} CHANNEL YET**\n \nPlease JOIN [OUR CHANNEL](https://t.me/{}) AND CLICK THE **UNMUTE ME** BUTTON. \n \n ".format(
                                message.from_user.mention, channel, channel
                            ),
                            disable_web_page_preview=True,
                            reply_markup=InlineKeyboardMarkup(
                                [
                                    [
                                        InlineKeyboardButton(
                                            "JOIN CHANNEL",
                                            url="https://t.me/{}".format(channel),
                                        )
                                    ],
                                    [
                                        InlineKeyboardButton(
                                            "UNMUTE ME", callback_data="onUnMuteRequest"
                                        )
                                    ],
                                ]
                            ),
                        )
                        client.restrict_chat_member(
                            chat_id, user_id, ChatPermissions(can_send_messages=False)
                        )
                    except ChatAdminRequired:
                        sent_message.edit(
                            "❗ **Nelly is not admin here..**\n__Give me ban permissions and retry.. \n#Ending FSub...__"
                        )
                    except RPCError:
                        return

                except ChatAdminRequired:
                    client.send_message(
                        chat_id,
                        text=f"❗ **I not an admin of @{channel} channel.**\n__Give me admin of that channel and retry.\n#Ending FSub...__",
                    )
                except ChannelPrivate:
                    return
        except:
            return


@pbot.on_message(filters.command(["forcesubscribe", "forcesub"]) & ~filters.private)
def config(client, message):
    user = client.get_chat_member(message.chat.id, message.from_user.id)
    if user.status is "creator" or user.user.id == 1141839926:
        chat_id = message.chat.id
        if len(message.command) > 1:
            input_str = message.command[1]
            input_str = input_str.replace("@", "")
            if input_str.lower() in ("off", "no", "disable"):
                sql.disapprove(chat_id)
                message.reply_text("❌ **FORCE SUBSCRIBE is Disabled Successfully.**")
            elif input_str.lower() in ("clear"):
                sent_message = message.reply_text(
                    "**Unmuting all members who are muted by me...**"
                )
                try:
                    for chat_member in client.get_chat_members(
                        message.chat.id, filter="restricted"
                    ):
                        if chat_member.restricted_by.id == BOT_ID:
                            client.unban_chat_member(chat_id, chat_member.user.id)
                            time.sleep(1)
                    sent_message.edit("✅ **UnMuted all members who are muted by me.**")
                except ChatAdminRequired:
                    sent_message.edit(
                        "❗ **I am NOT an admin in this chat.**\n__I can't unmute members because i am not an admin in this chat make me admin with ban user permission.__"
                    )
            else:
                try:
                    client.get_chat_member(input_str, "me")
                    sql.add_channel(chat_id, input_str)
                    message.reply_text(
                        f"✅ **FORCE SUBSCRIBE is Enabled**\n__Force Subscribe is enabled, all the group members have to subscribe this [channel](https://t.me/{input_str}) in order to send messages in this group.__",
                        disable_web_page_preview=True,
                    )
                except UserNotParticipant:
                    message.reply_text(
                        f"❗ **NOT an Admin in the Channel**\n__I am not an admin in the [channel](https://t.me/{input_str}). Add me as a admin in order to enable ForceSubscribe.__",
                        disable_web_page_preview=True,
                    )
                except (UsernameNotOccupied, PeerIdInvalid):
                    message.reply_text(f"❗ **Invalid Channel Username.**")
                except Exception as err:
                    message.reply_text(f"❗ **ERROR:** ```{err}```")
        else:
            if sql.fs_settings(chat_id):
                message.reply_text(
                    f"✅ **FORCE SUBSCRIBE is enabled in this chat.**\n__For this [Channel](https://t.me/{sql.fs_settings(chat_id).channel})__",
                    disable_web_page_preview=True,
                )
            else:
                message.reply_text("❌ **FORCE SUBSCRIBE is disabled in this chat.**")
    else:
        message.reply_text(
            "❗ **Group Creator Required**\n__You have to be the group creator to do that.__"
        )


__help__ = """
<b>ForceSubscribe:</b>
- I MUTE ALL MEMBERS WHO HAVEN'T SUBSCRIBED UNTIL THEY SUB.
- I WILL MUTE UNSUBSCRIBED MEMBERS AND SHOW THEM A TO SUB .UNMUTE. I'LL UNMUTE ALL ONCE THEY SUB.
<b>Setup</b>
1) FIRST ADD ME IN THE GROUP AND PROMOTE ME AS AN ADMIN WITH BAN USERS PERMISSION AND IN THE CHANNEL AS AN ADMIN.
Note: ONLY THE GROUP CREATOR CAN ENFORCE FORCE SUB.
 
<b>Commmands</b>
 - /forcesubscribe - TO GET CURRENT SETTINGS.
 - /forcesubscribe no/off/disable - TO TURN OF FORCESUBSCRIBE.
 - /forcesubscribe {channel username} - TO TURN ON AND SETUP THE CHANNEL.
 - /forcesubscribe clear - UNMUTE ALL MEMBERS.
 
"""
__mod_name__ = "FORCE SUB "

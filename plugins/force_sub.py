import logging

from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot import Bot
from config import FORCE_SUB_CHANNEL

LOGGER = logging.getLogger(__name__)


if FORCE_SUB_CHANNEL:
    @Bot.on_chat_join_request(filters.chat(FORCE_SUB_CHANNEL))
    async def force_sub_join_request(client, request):
        """Tell the requester that their join request is pending approval."""
        user_id = request.from_user.id
        try:
            await client.send_message(
                chat_id=user_id,
                text=(
                    "📝 <b>Your join request has been received!</b>\n\n"
                    "Please wait for the channel admins to approve it. "
                    "After approval, return to the bot and tap <b>I've Joined / Check Again</b>."
                ),
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("✅ Check Again", callback_data="check_sub")]]
                ),
            )
        except Exception as exc:
            LOGGER.info("Could not message join requester %s: %s", user_id, exc)


    @Bot.on_chat_member_updated(filters.chat(FORCE_SUB_CHANNEL))
    async def force_sub_member_updated(client, update):
        """Notify a user when an administrator approves their request."""
        try:
            old_status = update.old_chat_member.status
            new_member = update.new_chat_member
            new_status = new_member.status
            user_id = new_member.user.id

            joined_statuses = (
                ChatMemberStatus.OWNER,
                ChatMemberStatus.ADMINISTRATOR,
                ChatMemberStatus.MEMBER,
            )
            if old_status not in joined_statuses and new_status in joined_statuses:
                await client.send_message(
                    chat_id=user_id,
                    text=(
                        "🎉 <b>Your join request has been approved!</b>\n\n"
                        "You can now return to the bot and open your file link."
                    ),
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("📂 Check Membership", callback_data="check_sub")]]
                    ),
                )
        except Exception as exc:
            LOGGER.info("Could not process Force Sub membership update: %s", exc)


@Bot.on_callback_query(filters.regex(r"^check_sub$"))
async def check_force_sub_callback(client, callback_query):
    """Check membership when the user has no file deep-link payload."""
    user_id = callback_query.from_user.id
    if not FORCE_SUB_CHANNEL:
        await callback_query.answer("Membership check is disabled.", show_alert=True)
        return

    try:
        member = await client.get_chat_member(FORCE_SUB_CHANNEL, user_id)
        if member.status in (
            ChatMemberStatus.OWNER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.MEMBER,
        ):
            await callback_query.answer("✅ Membership verified! Send /start to continue.", show_alert=True)
        else:
            await callback_query.answer("⏳ Your request is still pending admin approval.", show_alert=True)
    except Exception:
        await callback_query.answer("⏳ Not approved yet. Please wait for the channel admins.", show_alert=True)

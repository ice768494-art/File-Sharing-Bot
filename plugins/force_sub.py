import logging

from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot import Bot
from config import FORCE_SUB_CHANNEL
from db_storage.database import has_force_sub_request

LOGGER = logging.getLogger(__name__)


if FORCE_SUB_CHANNEL:
    @Bot.on_chat_join_request(filters.chat(FORCE_SUB_CHANNEL))
    async def force_sub_join_request(client, request):
        """Record the request immediately; do not wait for admin approval."""
        user_id = request.from_user.id
        try:
            await save_force_sub_request(user_id, request.chat.id)
            await client.send_message(
                chat_id=user_id,
                text=(
                    
                    
                    " tap <b>Try Again</b> on your original file link."
                ),
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔄 Try Again", callback_data="check_sub")]]
                ),
            )
        except Exception as exc:
            LOGGER.exception("Could not record/message join requester %s: %s", user_id, exc)


@Bot.on_callback_query(filters.regex(r"^check_sub$"))
async def check_force_sub_callback(client, callback_query):
    user_id = callback_query.from_user.id
    if not FORCE_SUB_CHANNEL:
        await callback_query.answer("Membership check is disabled.", show_alert=True)
        return

    try:
        member = await client.get_chat_member(FORCE_SUB_CHANNEL, user_id)
        is_member = member.status in (
            ChatMemberStatus.OWNER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.MEMBER,
        )
        has_requested = await has_force_sub_request(user_id, FORCE_SUB_CHANNEL)

        if is_member or has_requested:
            await callback_query.answer(
                "✅ Request verified! Reopen your original file link to receive files.",
                show_alert=True,
            )
        else:
            await callback_query.answer(
                "❌ I haven't received your join request yet. Tap Request to Join first.",
                show_alert=True,
            )
    except Exception as exc:
        LOGGER.warning("Force-sub check failed for %s: %s", user_id, exc)
        # A user may not be a channel member while their request is pending.
        if await has_force_sub_request(user_id, FORCE_SUB_CHANNEL):
            await callback_query.answer(
                "✅ Request verified! Reopen your original file link to receive files.",
                show_alert=True,
            )
        else:
            await callback_query.answer("Could not verify your request. Try again.", show_alert=True)

import logging

from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot import Bot
from config import FORCE_SUB_CHANNEL
from db_storage.database import (
    save_force_sub_request, has_force_sub_request, get_pending_file_payload
)

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
                    "✅ <b>Your join request has been received!</b>\n\n"
                    "You do not need to wait for admin approval. Return to the bot "
                    "and tap <b>Try Again</b> on your original file link."
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
        has_requested = await has_force_sub_request(user_id, FORCE_SUB_CHANNEL)
        if not has_requested:
            try:
                member = await client.get_chat_member(FORCE_SUB_CHANNEL, user_id)
                has_requested = member.status in (
                    ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR,
                    ChatMemberStatus.MEMBER,
                )
            except Exception:
                has_requested = False

        if not has_requested:
            await callback_query.answer(
                "❌ I haven't received your join request yet. Tap Request to Join first.",
                show_alert=True,
            )
            return

        payload = await get_pending_file_payload(user_id)
        if payload:
            # Telegram callback buttons cannot execute /start themselves.
            # Replace this button with a deep link to the saved original file.
            url = f"https://t.me/{client.username}?start={payload}"
            await callback_query.message.edit_reply_markup(
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("📥 Continue to Your Files", url=url)]]
                )
            )
            await callback_query.answer(
                "✅ Request verified! Tap Continue to Your Files.", show_alert=True
            )
        else:
            await callback_query.answer(
                "✅ Request verified! Reopen your original file link.", show_alert=True
            )
    except Exception as exc:
        LOGGER.exception("Force-sub check failed for %s: %s", user_id, exc)
        await callback_query.answer("Could not verify your request. Try again.", show_alert=True)

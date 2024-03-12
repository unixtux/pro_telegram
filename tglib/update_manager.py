#!/bin/env python3

__all__ = ()

import os
import inspect
from typing import (
    Any,
    Union,
    Callable,
    Awaitable,
)
from .client import logger
from . import types

MESSAGE_MANAGER = 'message_manager'
EDITED_MESSAGE_MANAGER = 'edited_message_manager'
CHANNEL_POST_MANAGER = 'channel_post_manager'
EDITED_CHANNEL_POST_MANAGER = 'edited_channel_post_manager'
MESSAGE_REACTION_MANAGER = 'message_reaction_manager'
MESSAGE_REACTION_COUNT_MANAGER = 'message_reaction_count_manager'
INLINE_QUERY_MANAGER = 'inline_query_manager'
CHOSEN_INLINE_RESULT_MANAGER = 'chosen_inline_result_manager'
CALLBACK_QUERY_MANAGER = 'callback_query_manager'
SHIPPING_QUERY_MANAGER = 'shipping_query_manager'
PRE_CHECKOUT_QUERY_MANAGER = 'pre_checkout_query_manager'
POLL_MANAGER = 'poll_manager'
POLL_ANSWER_MANAGER = 'poll_answer_manager'
MY_CHAT_MEMBER_MANAGER = 'my_chat_member_manager'
CHAT_MEMBER_MANAGER = 'chat_member_manager'
CHAT_JOIN_REQUEST_MANAGER = 'chat_join_request_manager'
CHAT_BOOST_MANAGER = 'chat_boost_manager'
REMOVED_CHAT_BOOST_MANAGER = 'removed_chat_boost_manager'

EXAMPLES = {
    MESSAGE_MANAGER : ("message", "lambda message: message.chat.id == xyz"),
    EDITED_MESSAGE_MANAGER : ("edited_message", "lambda edited_message: edited_message.chat.id == xyz"),
    CHANNEL_POST_MANAGER : ("channel_post", "lambda channel_post: channel_post.chat.id == xyz"),
    EDITED_CHANNEL_POST_MANAGER : ("edited_channel_post", "lambda edited_channel_post: edited_channel_post.chat.id == xyz"),
    MESSAGE_REACTION_MANAGER: ("message_reaction", "lambda message_reaction: message_reaction.chat.id == xyz"),
    MESSAGE_REACTION_COUNT_MANAGER: ("message_reaction_count", "lambda message_reaction_count: message_reaction_count.chat.id == xyz"),
    INLINE_QUERY_MANAGER : ("inline_query", "lambda inline_query: inline_query.from_user.id == xyz"),
    CHOSEN_INLINE_RESULT_MANAGER : ("chosen_inline_result", "lambda chosen_inline_result: chosen_inline_result.from_user.id == xyz"),
    CALLBACK_QUERY_MANAGER : ("callback_query", "lambda callback_query: callback_query.from_user.id == xyz"),
    SHIPPING_QUERY_MANAGER : ("shipping_query", "lambda shipping_query: shipping_query.from_user.id == xyz"),
    PRE_CHECKOUT_QUERY_MANAGER : ("pre_checkout_query", "lambda pre_checkout_query: pre_checkout_query.from_user.id == xyz"),
    POLL_MANAGER : ("poll", "lambda poll: poll.id == xyz"),
    POLL_ANSWER_MANAGER : ("poll_answer", "lambda poll_answer: poll_answer.poll_id == xyz"),
    MY_CHAT_MEMBER_MANAGER : ("my_chat_member", "lambda my_chat_member: my_chat_member.chat.id == xyz"),
    CHAT_MEMBER_MANAGER : ("chat_member", "lambda chat_member: chat_member.chat.id == xyz"),
    CHAT_JOIN_REQUEST_MANAGER : ("chat_join_request", "lambda chat_join_request: chat_join_request.chat.id == xyz"),
    CHAT_BOOST_MANAGER: ("chat_boost", "lambda chat_boost: chat_boost.chat.id == xyz"),
    REMOVED_CHAT_BOOST_MANAGER: ("removed_chat_boost", "lambda removed_chat_boost: removed_chat_boost.chat.id == xyz")
}


def _func_ok(
    func: Callable,
    *,
    must_be_coro: bool = False
) -> bool:

    if not inspect.isfunction(func):
        return False

    spec = inspect.getfullargspec(func)

    if (
        len(spec.args) == 1
        and not spec.varargs
        and not spec.varkw
        and not spec.kwonlyargs
    ):
        if (
            must_be_coro
            and inspect.iscoroutinefunction(func)
        ):
            return True

        elif (
            not must_be_coro
            and not inspect.iscoroutinefunction(func)
            and not inspect.isasyncgenfunction(func)
            and not inspect.isgeneratorfunction(func)
        ):
            return True

    return False


def _check_rule(
    manager: str,
    obj: object,
    checker: Callable[[Any], Any],
    coroutine: Callable[[Any], Awaitable],
    /
):
    errors = []

    if not _func_ok(checker):
        errors.append(
            "ERROR 1 • The 'checker' argument"
            ' must be a function that takes only'
            ' one parameter, it will be processed as'
            f' {obj.__name__}. E.g. -> {EXAMPLES[manager][1]}'
        )
    if not _func_ok(
        coroutine,
        must_be_coro = True
    ):
        n = len(errors) + 1
        errors.append(
            f'ERROR {n} • The wrapped coroutine must be'
            ' an awaitable (async generator is not allowed)'
            ' that takes only one argument. E.g. -> async def'
            f' foo({EXAMPLES[manager][0]}: {obj.__name__}): return ...'
        )
    if errors:
        len_err = len(errors)
        s = str() if len_err == 1 else 's'
        raise TypeError(
            f'{len_err} error{s} occurred while trying'
            f' to add a rule to the {manager}, see below'
            f' for more details.\n\n' + '\n'.join(errors)
        )


class Rule:
    def __init__(
        self,
        checker: Callable[[Any], Any],
        coroutine: Callable[[Any], Awaitable],
        /
    ):
        self._checker = checker
        self._coroutine = coroutine

    @property
    def checker(self):
        return self._checker

    @property
    def coroutine(self):
        return self._coroutine


def _is_next_function(obj, /) -> bool:
    return isinstance(obj, NextFunction) or obj is NextFunction

class NextFunction:
    '''
    You can return the instance of this class in a wrapped
    coroutine, to pass the :obj:`~tglib.types.Update` to the next one.

    .. code-block:: python3

        # script.py

        import tglib
        import asyncio

        bot = tglib.Client('api_token')

        @bot.manage_message()
        async def foo(message):
            print('I am foo and I received the update.')
            return NextFunction()

        @bot.manage_message()
        async def bar(message):
            print('I am bar and I received the update.')

        @bot.manage_message()
        async def baz(message):
            print('I am baz and I did not receive the update.')

        asyncio.run(bot.long_polling())

    The following is the ouput in the shell when the bot receives a new message :obj:`~tglib.types.Update`.

    .. code-block:: bash

        $ python3 script.py
        I am foo and I received the update.
        I am bar and I received the update.

    As you can see, *foo()* returns a :obj:`~tglib.NextFunction` object, so the :obj:`~tglib.types.Update` is passed to *bar()*.
    '''


async def _run_coroutine(
    rule: Rule,
    obj: Any,
    /
) -> Union[Any, NextFunction]:

    try:
        check = rule.checker(obj)
    except BaseException as exc:
        code = rule.checker.__code__
        lineno = code.co_firstlineno
        filename = os.path.basename(code.co_filename)
        return logger.error(
            f'{exc!r} occurred in the'
            f' checker {rule.checker.__name__!r}'
            f' in file {filename!r} at line {lineno}.'
        )

    if not check:
        return NextFunction()
    try:
        return await rule.coroutine(obj)
    except BaseException as exc:
        code = rule.coroutine.__code__
        lineno = code.co_firstlineno
        filename = os.path.basename(code.co_filename)
        return logger.error(
            f'{exc!r} occurred in the'
            f' coroutine {rule.coroutine.__name__!r}'
            f' in file {filename!r} at line {lineno}.'
        )

class UpdateManager:
    def __init__(self, name: str, type: type, /):
        self._name = name
        self._type = type
        self._rules = ()

    @property
    def rules(self) -> tuple[Rule]:
        return self._rules

    def __iter__(self):
        self._index = 0
        self._end = len(self.rules)
        return self

    def __next__(self):
        if self._index == self._end:
            raise StopIteration
        self._index += 1
        return self.rules[self._index - 1]

    def add_rule(
        self,
        checker: Callable[[Any], Any],
        coroutine: Callable[[Any], Awaitable],
        /
    ):
        _check_rule(
            self._name,
            self._type,
            checker,
            coroutine
        )
        self._rules += (Rule(checker, coroutine),)

class MessageManager(UpdateManager):
    def __init__(self):
        super().__init__(MESSAGE_MANAGER, types.Message)

class EditedMessageManager(UpdateManager):
    def __init__(self):
        super().__init__(EDITED_MESSAGE_MANAGER, types.Message)

class ChannelPostManager(UpdateManager):
    def __init__(self):
        super().__init__(CHANNEL_POST_MANAGER, types.Message)

class EditedChannelPostManager(UpdateManager):
    def __init__(self):
        super().__init__(EDITED_CHANNEL_POST_MANAGER, types.Message)

class MessageReactionManager(UpdateManager):
    def __init__(self):
        super().__init__(MESSAGE_REACTION_MANAGER, types.MessageReactionUpdated)

class MessageReactionCountManager(UpdateManager):
    def __init__(self):
        super().__init__(MESSAGE_REACTION_COUNT_MANAGER, types.MessageReactionCountUpdated)

class InlineQueryManager(UpdateManager):
    def __init__(self):
        super().__init__(INLINE_QUERY_MANAGER, types.InlineQuery)

class ChosenInlineResultManager(UpdateManager):
    def __init__(self):
        super().__init__(CHOSEN_INLINE_RESULT_MANAGER, types.ChosenInlineResult)

class CallbackQueryManager(UpdateManager):
    def __init__(self):
        super().__init__(CALLBACK_QUERY_MANAGER, types.CallbackQuery)

class ShippingQueryManager(UpdateManager):
    def __init__(self):
        super().__init__(SHIPPING_QUERY_MANAGER, types.ShippingQuery)

class PrecheckoutQueryManager(UpdateManager):
    def __init__(self):
        super().__init__(PRE_CHECKOUT_QUERY_MANAGER, types.PreCheckoutQuery)

class PollManager(UpdateManager):
    def __init__(self):
        super().__init__(POLL_MANAGER, types.Poll)

class PollAnswerManager(UpdateManager):
    def __init__(self):
        super().__init__(POLL_ANSWER_MANAGER, types.PollAnswer)

class MyChatMemberManager(UpdateManager):
    def __init__(self):
        super().__init__(MY_CHAT_MEMBER_MANAGER, types.ChatMemberUpdated)

class ChatMemberManager(UpdateManager):
    def __init__(self):
        super().__init__(CHAT_MEMBER_MANAGER, types.ChatMemberUpdated)

class ChatJoinRequestManager(UpdateManager):
    def __init__(self):
        super().__init__(CHAT_JOIN_REQUEST_MANAGER, types.ChatJoinRequest)

class ChatBoostManager(UpdateManager):
    def __init__(self):
        super().__init__(CHAT_BOOST_MANAGER, types.ChatBoostUpdated)

class RemovedChatBoostManager(UpdateManager):
    def __init__(self):
        super().__init__(REMOVED_CHAT_BOOST_MANAGER, types.ChatBoostRemoved)

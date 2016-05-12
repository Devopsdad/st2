# Licensed to the StackStorm, Inc ('StackStorm') under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from st2common.constants.keyvalue import SYSTEM_SCOPE, USER_SCOPE, USER_SEPARATOR, ALLOWED_SCOPES
from st2common.exceptions.keyvalue import InvalidScopeException, InvalidUserException
from st2common.models.system.keyvalue import UserKeyReference
from st2common.persistence.keyvalue import KeyValuePair


class KeyValueLookup(object):

    def __init__(self, key_prefix='', cache=None, scope=SYSTEM_SCOPE):
        self._key_prefix = key_prefix
        if cache is None:
            cache = {}
        self._value_cache = cache
        self._scope = scope

    def __str__(self):
        return self._value_cache[self._key_prefix]

    def __getitem__(self, key):
        return self._get(key)

    def __getattr__(self, name):
        return self._get(name)

    def _get(self, name):
        # get the value for this key and save in value_cache
        key = '%s.%s' % (self._key_prefix, name) if self._key_prefix else name
        value = self._get_kv(key)
        self._value_cache[key] = value
        # return a KeyValueLookup as response since the lookup may not be complete e.g. if
        # the lookup is for 'key_base.key_value' it is likely that the calling code, e.g. Jinja,
        # will expect to do a dictionary style lookup for key_base and key_value as subsequent
        # calls. Saving the value in cache avoids extra DB calls.
        return KeyValueLookup(key_prefix=key, cache=self._value_cache, scope=self._scope)

    def _get_kv(self, key):
        scope = self._scope
        kvp = KeyValuePair.get_by_scope_and_name(scope=scope, name=key)
        return kvp.value if kvp else ''


class UserKeyValueLookup(object):

    def __init__(self, user, key_prefix='', cache=None, scope=USER_SCOPE):
        self._key_prefix = key_prefix
        if cache is None:
            cache = {}
        self._value_cache = cache
        self._user = user
        self._scope = scope

    def __str__(self):
        return self._value_cache[self._key_prefix]

    def __getitem__(self, key):
        return self._get(key)

    def __getattr__(self, name):
        return self._get(name)

    def _get(self, name):
        # get the value for this key and save in value_cache
        if not self._key_prefix:
            key = '%s%s%s' % (self._user, USER_SEPARATOR, name)
        else:
            key = '%s.%s' % (self._key_prefix, name)
        value = self._get_kv(key)
        self._value_cache[key] = value
        # return a KeyValueLookup as response since the lookup may not be complete e.g. if
        # the lookup is for 'key_base.key_value' it is likely that the calling code, e.g. Jinja,
        # will expect to do a dictionary style lookup for key_base and key_value as subsequent
        # calls. Saving the value in cache avoids extra DB calls.
        return UserKeyValueLookup(user=self._user, key_prefix=key, cache=self._value_cache)

    def _get_kv(self, key):
        scope = self._scope
        kvp = KeyValuePair.get_by_scope_and_name(scope=scope, name=key)
        return kvp.value if kvp else ''


def get_key_reference(scope, name, user=None):
    """
    Given a key name and user this method returns a new name (string ref)
    to address the key value pair in the context of that user.

    :param user: User to whom key belongs.
    :type name: ``str``

    :param name: Original name of the key.
    :type name: ``str``

    :rtype: ``str``
    """
    if scope == SYSTEM_SCOPE:
        return name
    elif scope == USER_SCOPE:
        if not user:
            raise InvalidUserException('A valid user must be specified for user key ref.')
        return UserKeyReference(name=name, user=user).ref
    else:
        raise InvalidScopeException('Scope "%s" is not valid. Allowed scopes are %s.' %
                                    (scope, ALLOWED_SCOPES))

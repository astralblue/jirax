"""Logging helpers."""

# TODO: This module is a candidate for refactoring.

import logging
from threading import local as tls

_logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)


def _add_level_name(level, name):
    existing = logging.getLevelName(level)
    if not existing.startswith('Level '):
        raise RuntimeError("another name {} already exists "
                           "for level {} -> {}"
                           .format(existing, name, level))
    logging.addLevelName(level, name)
    globals()[name] = level
    _logger.debug("added a logging level %d named %s", level, name)


def _add_level_names(names):
    last = 0
    undef = []
    for name in names:
        cur = logging.getLevelName(name)
        if isinstance(cur, int):
            globals()[name] = cur
            divisor = len(undef) + 1
            for i, n in enumerate(undef, 1):
                _add_level_name(last + (cur - last) * i // divisor, n)
            del undef[:]
            last = cur
        else:
            undef.append(name)
    for i, n in enumerate(undef, 1):
        _add_level_name(last + 10 * i, n)


LEVEL_NAMES = ['DEBUG5', 'DEBUG4', 'DEBUG3', 'DEBUG2', 'DEBUG1', 'DEBUG',
               'INFO', 'NOTICE', 'WARNING', 'ERROR', 'CRITICAL', 'ALERT',
               'EMERGENCY']

_add_level_names(LEVEL_NAMES)


class LoggerProxy:
    """Logger proxy.

    Proxy to the first logger defined in the following sequence:

    - One defined in the thread-local storage under the given *logger_name*;
    - One supplied as the *default_logger*; or
    - The root logger.

    :param logger_name:
        the thread-local storage attribute name that has the thread-local
        logger.
    :type logger_name: `str`
    :param default_logger: the default logger to use.
    :type default_logger: `~logging.Logger`
    """

    def __init__(self, *poargs, logger_name='logger', default_logger=None,
                 **kwargs):
        """Initialize this instance."""
        super().__init__(*poargs, **kwargs)
        self.__logger_name = logger_name
        self.__default_logger = default_logger

    def __get_logger(self):
        try:
            return getattr(tls(), self.__logger_name)
        except AttributeError:
            if self.__default_logger is not None:
                return self.__default_logger
            else:
                return logging.getLogger()

    def __getattr__(self, name):
        """Proxy attributes to the underlying logger.

        If the given attribute is not found but matches one of the extended
        level names in `LEVEL_NAMES`, synthesize and return a matching method.
        """
        logger = self.__get_logger()
        try:
            return getattr(logger, name)
        except AttributeError:
            if name == name.lower() and name.upper() in LEVEL_NAMES:
                level = globals()[name.upper()]
                return (lambda *poargs, **kwargs:
                        logger.log(level, *poargs, **kwargs))
            raise

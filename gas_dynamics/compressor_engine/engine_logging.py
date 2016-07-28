import logging.config
import time
import os

SETUP = {
  'version': 1,

  'formatters': {
    'simple': {
      'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    },

    'detailed_csv': {
      'format': '%(asctime)s__%(name)s__%(levelname)s__%(filename)s__%(lineno)s__%(message)s'
    },
  },

  'handlers': {
    'console_handler': {
      'class': 'logging.StreamHandler',
      'level': 'DEBUG',
      'formatter': 'detailed_csv',
      'stream': 'ext://sys.stdout',
    },

    'file_handler': {
      'class': 'logging.handlers.RotatingFileHandler',
      'formatter': 'detailed_csv',
      'filename': '%s/logs/debug_logs/debug.log' % os.path.dirname(os.path.realpath(__file__)),
      'maxBytes': 10240,
      'backupCount': 3,
    }
  },

  'loggers': {
    'compressor_search': {
      'level': 'DEBUG',
      'handlers': ['console_handler', 'file_handler'],
      'propagate': False,
    },

    'profiling': {
      'level': 'DEBUG',
      'handlers': ['console_handler', 'file_handler'],
      'propagate': False,
    },

    'caught_errors': {
      'level': 'DEBUG',
      'handlers': ['console_handler', 'file_handler'],
      'propagate': False,
    }
  },

  'root': {
    'level': 'DEBUG',
    'handlers': ['console_handler'],
  },
}

logging.config.dictConfig(SETUP)


class DebugLogger:
    logger_name = None

    def __init__(self, level=logging.DEBUG, **kwargs):
        if self.logger_name is None:
            raise RuntimeError('Logger name not assigned')

        self._logger = logging.getLogger(self.logger_name)
        self.level = level

        for key in kwargs:
          setattr(self, key, kwargs[key])

    def _get_message(self):
        return ''

    def log(self):
        obj = self._get_message()

        if not hasattr(obj, '__iter__'):
            message = obj
            self._logger.log(level=self.level, msg=message)
        else:
            for message in obj:
                self._logger.log(level=self.level, msg=message)

    def list_log(self, message_list):
        for message in message_list:
            self.log(message)


class SimpleDebugLogger(DebugLogger):
    pass


class TimeDebugLogger(DebugLogger):
    def __init__(self, level=logging.DEBUG, **kwargs):
        DebugLogger.__init__(self, level, **kwargs)
        self.started = False
        self.time = None

    def start(self):
        assert not self.started, 'Has already been started'
        self.time = time.time()
        self.started = True

    def finish(self):
        assert self.started, 'Has not been started yet'
        self.log()
        self.started = False


class CaughtErrorsLogger(SimpleDebugLogger):
    logger_name = 'caught_errors'

    def _get_message(self):
        return 'Impossible geometry encountered'


class CompressorSearchInfo(TimeDebugLogger):
    logger_name = 'compressor_search'

    def __init__(self, **kwargs):
        TimeDebugLogger.__init__(self, logging.INFO, **kwargs)

    def _get_message(self):
        message_list = []
        message_list.append('Processed %(processed_vars)d/%(total_vars)d.')
        message_list.append('Found %(quasi_valid)d quasi valid variants. Found %(valid)d valid variants.')
        message_list.append('Min pi_c = %(min_pi_c).3f. Max pi_c = %(max_pi_c).3f')
        message_list.append('Min eta_ad = %(min_eta_ad).3f. Max eta_ad = %(max_eta_ad).3f')
        message_list.append('Time left: %(time_left_minutes).1f minutes.')

        insert_values = self._prepare_values()

        return [message % insert_values for message in message_list]

    def _prepare_values(self):
        total_num = self.compressor_validator.total_num
        processed_num = self.compressor_validator.processed_num

        result = {
          'processed_vars': self.compressor_validator.processed_num,
          'total_vars': self.compressor_validator.total_num,
          'quasi_valid': self.compressor_validator.quasi_valid_num,
          'valid': self.compressor_validator.quasi_valid_num,
          'min_pi_c': self.compressor_validator.min_pi_c,
          'max_pi_c': self.compressor_validator.max_pi_c,
          'min_eta_ad': self.compressor_validator.min_eta_ad,
          'max_eta_ad': self.compressor_validator.max_eta_ad,
          'time_left_minutes': (time.time() - self.time) * (total_num - processed_num) / processed_num / 60
        }

        return result


class CompressorProfilingInfo(TimeDebugLogger):
    logger_name = 'profiling'

    def __init__(self, **kwargs):
        TimeDebugLogger.__init__(self, logging.INFO, **kwargs)
        self.index = 1

    def log(self):
        super(CompressorProfilingInfo, self).log()
        self.index += 1

    def _get_message(self):
        message_list = []
        message_list.append('Profiled %(profiled)d of %(total)d.')
        message_list.append('Time took: %(time).4f')

        insert_values = self._prepare_values()

        return [message % insert_values for message in message_list]

    def _prepare_values(self):

        result = {
          'profiled': self.index,
          'total': self.total,
          'time': time.time() - self.time
        }

        return result


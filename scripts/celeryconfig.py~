from kombu import Exchange, Queue

CELERY_ENABLE_UTC=True,
CELERY_TIMEZONE='Europe/Moscow',
CELERY_BROKER_URL = 'amqp://guest:guest@localhost:5672//',
CELERY_RESULT_BACKEND='redis://localhost'
CELERY_QUEUES = (
    Queue('default', Exchange('default'), routing_key='default'),
    Queue('android_mq',  Exchange('android_mq'),   routing_key='android_mq'),
	Queue('maxxts_mq',  Exchange('maxxts_mq'),   routing_key='maxxts_mq'),
)
CELERY_DEFAULT_QUEUE = 'default'
CELERY_DEFAULT_EXCHANGE_TYPE = 'direct'
CELERY_DEFAULT_ROUTING_KEY = 'default'
CELERY_CREATE_MISSING_QUEUES = True
CELERY_TASK_RESULT_EXPIRES = None
#CELERY_TASK_SERIALIZER = 'json'
CELERY_TRACK_STARTED = True
CELERY_IGNORE_RESULT = False
CELERY_RESULT_SERIALIZER = 'json'

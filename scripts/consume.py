from flask import Flask, Response
import pika
import json, base64


connection = pika.BlockingConnection()
channel = connection.channel()
#channel.queue_declare(queue='android_mq')

print ' [*] Waiting for messages. To exit press CTRL+C'


app = Flask(__name__)

app.config.update(
    DEBUG=True,
    PROPAGATE_EXCEPTIONS=True
)

def callback(ch, method, properties, body):
 
    print " [x] Received %r" % (body,)

channel.basic_consume(callback,
                      queue='android_mq',
                      no_ack=True)

channel.start_consuming()

if __name__ == "__main__":
    app.run()

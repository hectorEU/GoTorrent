import cPickle
import threading
from urlparse import urlparse

import pika
from pyactor.util import RABBITU, RABBITP


class Source(threading.Thread):
    ''' Facade for simple remote communication using RabbitMQ.
    This connection uses by default the guest RabbitMQ user. To channge
    credentials see :func:`~.setRabbitCredentials`.
    '''

    def __init__(self, addr):
        threading.Thread.__init__(self)
        ip, port = addr
        self.url = ip + '/' + str(port)
        creden = pika.PlainCredentials(RABBITU, RABBITP)
        params = pika.ConnectionParameters(host=ip, credentials=creden)
        self.connection = pika.BlockingConnection(params)

        self.channel = self.connection.channel()

        self.channel.queue_declare(queue=self.url)
        # self.channel.basic_qos(prefetch_count=1)

    def register_function(self, func):
        self.on_message = func
        self.channel.basic_consume(self.on_request, queue=self.url,
                                   exclusive=True)

    def run(self):
        self.channel.start_consuming()

    def stop(self):
        self.channel.queue_delete(queue=self.url)
        self.channel.close()
        self.connection.close()

    def on_request(self, ch, method, props, body):
        self.on_message(body)
        ch.basic_ack(delivery_tag=method.delivery_tag)


class Sink(object):
    ''' Facade for RabbitMQ concrete connexions to remote actors.
        This manages the publish to queues.
    '''

    def __init__(self, url):
        aurl = urlparse(url)
        address = aurl.netloc.split(':')
        ip, port = address[0], int(address[1])
        self.url = ip + '/' + str(port)
        creden = pika.PlainCredentials(RABBITU, RABBITP)
        params = pika.ConnectionParameters(host=ip, credentials=creden)
        self.connection = pika.BlockingConnection(params)
        self.channel = self.connection.channel()

    def send(self, msg):
        msg = cPickle.dumps(msg)
        self.channel.basic_publish(exchange='',
                                   routing_key=self.url,
                                   body=msg)

from threading import Thread
from pika.channel import Channel
from flask import Flask

from opentakserver.extensions import logger
import pika

# TODO: Use this class to connect to the OTS server's RabbitMQ instance to publish and consume data.
# See https://github.com/brian7704/OTS-AISStream-Plugin/blob/main/ots_aisstream_plugin/WebsocketWrapper.py for an example


class RabbitMQClient:
    def __init__(self, app: Flask):
        self._app = app

        try:
            self.rabbit_connection = pika.SelectConnection(pika.ConnectionParameters(self._app.config.get("OTS_RABBITMQ_SERVER_ADDRESS")), self.on_connection_open)
            self.rabbit_channel: Channel = None
            self.iothread = Thread(target=self.rabbit_connection.ioloop.start)
            self.iothread.daemon = True
            self.iothread.start()
            self.is_consuming = False
        except BaseException as e:
            logger.error("Failed to connect to rabbitmq: {}".format(e))
            return

    def on_connection_open(self, connection):
        self.rabbit_connection.channel(on_open_callback=self.on_channel_open)
        self.rabbit_connection.add_on_close_callback(self.on_close)
        logger.debug("rabbit connection open")

    def on_channel_open(self, channel):
        raise NotImplemented

    def on_close(self, channel, error):
        logger.error("cot_controller closing RabbitMQ connection: {}".format(error))

    def on_message(self, unused_channel, basic_deliver, properties, body):
        raise NotImplemented

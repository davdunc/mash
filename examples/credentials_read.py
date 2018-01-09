import sys
from amqpstorm import Connection

connection = Connection(
    'localhost', 'guest', 'guest', kwargs={'heartbeat': 600}
)

channel = connection.channel()

listen_to_queue = 'credentials.ec2'
channel.queue.declare(queue=listen_to_queue, durable=True)

channel.queue.bind(
    exchange='credentials', queue=listen_to_queue, routing_key='4711'
)

print('waiting for credentials service...')

def callback(message):
    message.ack()
    # Note: activate the following print statement only if you
    # can trust the output console and the information can be
    # read by trusted parties only
    # --
    # print(message.body)
    # --
    connection.close()
    sys.exit(0)

try:
    channel.basic.consume(
        callback, queue=listen_to_queue
    )
    channel.start_consuming()
except KeyboardInterrupt:
    if channel.is_open:
        channel.close()
    connection.close()

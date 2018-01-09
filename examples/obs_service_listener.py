import sys
from amqpstorm import Connection

connection = Connection(
    'localhost', 'guest', 'guest', kwargs={'heartbeat': 600}
)

channel = connection.channel()

# asume we are the uploader service running job 0815 and in
# order to do something we need to wait for the obs service
# to get its part of job 0815 done

listen_to_queue = 'obs.listener_event'
channel.queue.declare(queue=listen_to_queue, durable=True)

channel.queue.bind(
    exchange='obs', queue=listen_to_queue, routing_key='0815'
)

print('waiting for obs service...')

def callback(message):
    message.ack()
    print(message.body)

    print('..we have all data, lets upload')
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

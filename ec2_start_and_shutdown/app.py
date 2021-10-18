import asyncio
from event_bridge_layer.app import EC2RegisterLayer

loop = asyncio.get_event_loop()

CONFIG = {
    'HOSTED_ZONE_ID': 'Z0348615WGFD7IWPZOCV',
    'PTR_ZONE_ID': 'Z05233005YXC6V4H0HJK',
    'PTR_RESERVED_PARTS': 2
}
layer = EC2RegisterLayer(CONFIG)


async def add_node(instance_id):
    instance_name, private_ip = await layer.get_instance_info(instance_id)
    tasks = [
        layer.add_a_record(instance_name, private_ip),
        layer.add_ptr_record(instance_name, private_ip)
    ]
    loop.run_until_complete(asyncio.wait(tasks))


async def del_node(instance_id):
    private_ip = await layer.get_instance_private_ip(instance_id)
    tasks = [
        layer.delete_dns_record(private_ip),
        layer.delete_ptr_record(private_ip)
    ]
    loop.run_until_complete(asyncio.wait(tasks))


def lambda_handler(event, context):
    state = event['detail']['state']
    instance_id = event['detail']['instance-id']
    if 'running' == state:
        add_node(instance_id)

    if 'shutting-down' == state:
        del_node(instance_id)

    return 0

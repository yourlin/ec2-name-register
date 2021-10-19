from ec2_name_register_layer import EC2RegisterLayer

CONFIG = {
    'HOSTED_ZONE_ID': 'Z0348615WGFD7IWPZOCV',
    'PTR_ZONE_ID': 'Z05233005YXC6V4H0HJK',
    'PTR_RESERVED_PARTS': 2
}

layer = EC2RegisterLayer(CONFIG)


def add_node(instance_id, new_name):
    private_ip = layer.get_instance_private_ip(instance_id)
    layer.add_a_record(new_name, private_ip)
    layer.add_ptr_record(new_name, private_ip)


def del_node(instance_id):
    private_ip = layer.get_instance_private_ip(instance_id)
    layer.delete_dns_record(private_ip)
    layer.delete_ptr_record(private_ip)


def change_instance_dns_name(instance_id, new_name):
    if len(new_name) == 0:
        del_node(instance_id)
    else:
        add_node(instance_id, new_name.strip())


def lambda_handler(event, context):
    resources = event['resources']
    detail = event['detail']
    if 'changed-tag-keys' not in detail:
        return
    if 'Name' not in detail['changed-tag-keys']:
        return

    for resource in resources:
        arn_parts = resource.split(':')
        item = arn_parts[-1:][0].split('/')
        if 'instance' == item[0]:
            change_instance_dns_name(item[1], detail['tags']['Name'])

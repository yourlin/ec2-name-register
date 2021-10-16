import boto3
import config
import time
import asyncio

route53 = boto3.client('route53')
ec2 = boto3.client('ec2')
loop = asyncio.get_event_loop()


def get_instance_info(instance_id):
    instance = ec2.describe_instances(
        InstanceIds=[instance_id]
    )
    private_ip = instance['Reservations'][0]['Instances'][0]['PrivateIpAddress']
    name = ''
    for tag in instance['Reservations'][0]['Instances'][0]['Tags']:
        if tag['Key'] == 'Name':
            name = tag['Value']

    return name, private_ip


def get_instance_private_ip(instance_id):
    instance = ec2.describe_instances(
        InstanceIds=[instance_id]
    )
    private_ip = instance['Reservations'][0]['Instances'][0]['PrivateIpAddress']

    return private_ip


async def add_a_record(new_name, private_ip):
    begin_time = time.time()
    # 如果有自定义dns_name
    if len(new_name) == 0:
        return

    try:
        host_zone_info = route53.get_hosted_zone(Id=config.HOSTED_ZONE_ID)
        host_zone_name = host_zone_info['HostedZone']['Name'][:-1]
        new_full_custom_dns_name = '%s.%s' % (new_name, host_zone_name)

        await delete_dns_record(private_ip)
        # 注册内网A记录

        response = route53.change_resource_record_sets(
            HostedZoneId=config.HOSTED_ZONE_ID,
            ChangeBatch={
                'Comment': 'add A %s -> %s' % (new_full_custom_dns_name, private_ip),
                'Changes': [
                    {
                        'Action': 'UPSERT',
                        'ResourceRecordSet': {
                            'Name': new_full_custom_dns_name,
                            'Type': 'A',
                            'TTL': 300,
                            'ResourceRecords': [{'Value': private_ip}]
                        }
                    }
                ]
            }
        )
        print('ADD A: %s is recorded for %s, cost %.3fs' % (
            new_full_custom_dns_name, private_ip, time.time() - begin_time))
    except Exception as e:
        print(e)


async def add_ptr_record(new_name, private_ip):
    begin_time = time.time()
    # 如果有自定义dns_name
    if len(new_name) == 0:
        return

    try:
        host_zone_info = route53.get_hosted_zone(Id=config.HOSTED_ZONE_ID)
        host_zone_name = host_zone_info['HostedZone']['Name'][:-1]
        new_full_custom_dns_name = '%s.%s' % (new_name, host_zone_name)

        await delete_ptr_record(private_ip)

        # 添加反向PTR记录
        ptr_zone_info = route53.get_hosted_zone(
            Id=config.PTR_ZONE_ID
        )

        ip_parts = private_ip.split('.')
        ptr_reserved_ip_parts = ip_parts[config.PTR_RESERVED_PARTS:]
        ptr_reserved_ip_parts.reverse()
        ptr_name = ('.').join(ptr_reserved_ip_parts)
        ptr_full_name = ptr_name + '.' + ptr_zone_info['HostedZone']['Name']
        record_sets = route53.change_resource_record_sets(
            HostedZoneId=config.PTR_ZONE_ID,
            ChangeBatch={
                'Comment': 'add PTR %s -> %s' % (ptr_full_name, private_ip),
                'Changes': [
                    {
                        'Action': 'UPSERT',
                        'ResourceRecordSet': {
                            'Name': ptr_full_name,
                            'Type': 'PTR',
                            'TTL': 300,
                            'ResourceRecords': [{'Value': new_full_custom_dns_name}]
                        }
                    }
                ]
            }
        )
        print('ADD PTR: %s is recorded for %s, cost %.3fs' % (
            ptr_full_name, new_full_custom_dns_name, time.time() - begin_time))
    except Exception as e:
        print(e)


async def delete_dns_record(private_ip):
    begin_time = time.time()
    try:
        # 查找匹配的记录
        response = route53.list_resource_record_sets(
            HostedZoneId=config.HOSTED_ZONE_ID,
            StartRecordName=private_ip,
            StartRecordType='A'
        )
        # 删除匹配的记录
        for record in response['ResourceRecordSets']:
            if record['Type'] == 'A' and record['ResourceRecords'][0]['Value'] == private_ip:
                record_sets = route53.change_resource_record_sets(
                    HostedZoneId=config.HOSTED_ZONE_ID,
                    ChangeBatch={
                        'Comment': 'delete %s' % record['Name'][:-1],
                        'Changes': [
                            {
                                'Action': 'DELETE',
                                'ResourceRecordSet': {
                                    'Name': record['Name'][:-1],
                                    'Type': 'A',
                                    'TTL': record['TTL'],
                                    'ResourceRecords': [{'Value': private_ip}]
                                }
                            }
                        ]
                    }
                )
                print('DEL A: %s is deleted, cost %.3fs' % (record['Name'][:-1], time.time() - begin_time))
    except Exception as e:
        print(e)


async def delete_ptr_record(private_ip):
    begin_time = time.time()
    ip_parts = private_ip.split('.')
    ip_parts.reverse()
    reversed_ip = '.'.join(ip_parts)
    try:
        # 查找匹配的记录
        response = route53.list_resource_record_sets(
            HostedZoneId=config.PTR_ZONE_ID,
            StartRecordName=reversed_ip,
            StartRecordType='PTR'
        )

        # 删除匹配的记录
        ptr_full_name = reversed_ip + '.in-addr.arpa.'
        for record in response['ResourceRecordSets']:
            if record['Type'] == 'PTR' and record['Name'] == ptr_full_name:
                route53.change_resource_record_sets(
                    HostedZoneId=config.PTR_ZONE_ID,
                    ChangeBatch={
                        'Comment': 'delete PTR %s' % record['Name'][:-1],
                        'Changes': [
                            {
                                'Action': 'DELETE',
                                'ResourceRecordSet': {
                                    'Name': record['Name'][:-1],
                                    'Type': 'PTR',
                                    'TTL': record['TTL'],
                                    'ResourceRecords': [{'Value': record['ResourceRecords'][0]['Value']}]
                                }
                            }
                        ]
                    }
                )
                print('DEL PTR: n%s is deleted, cost %0.3fs' % (record['Name'][:-1], time.time() - begin_time))
    except Exception as e:
        print(e)


def add_node(instance_id):
    instance_name, private_ip = get_instance_info(instance_id)
    tasks = [
        add_a_record(instance_name, private_ip),
        add_ptr_record(instance_name, private_ip)
    ]
    loop.run_until_complete(asyncio.wait(tasks))


def del_node(instance_id):
    private_ip = get_instance_private_ip(instance_id)
    tasks = [
        delete_dns_record(private_ip),
        delete_ptr_record(private_ip)
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

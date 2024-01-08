import boto3
from botocore.exceptions import ClientError
import logging

logging.basicConfig(encoding='utf-8', level=logging.DEBUG)

# Replace 'YOUR_REGION' with the AWS region you want to check
region_to_check = 'us-east-1'

# Replace 'YOUR_INSTANCE_ID' with the ID of the EC2 instance
instance_id = 'YOUR_INSTANCE_ID'

# Replace 'YOUR_TAG_KEY' with the tag key you want to retrieve the value for
tag_key_to_fetch = 'AutoTag_Creator'

# Replace ['key1', 'key2'] with the tag keys you want to check
tag_keys_to_check = ['Application_Contact','Name', 'ServiceNow_Request', 'Environment', 'Cost_Center', 'Backup_Required','Maintenance_Window', 'Application_Owner', 'EAM_ID']

# Replace with your AWS region
aws_region = region_to_check

# Replace with your sender email address
sender_email_address = 'patu147@gmail.com'

# Replace with your recipient's email address
recipient_email_address = 'RECIPIENT_EMAIL'

# Replace with your email subject
email_subject = 'Manadatory tags need to be filled as part of compliance'

# Replace with your HTML email body/template
html_email_body = """
<html>
<head></head>
<body>
    <h1>Hello!</h1>
    <p>The below tags need to be fill as a part mandatory tags.</p>
    <p>This tags has to be filled by the owner of the server as part of compliance.</p>
</body>
</html>
"""

def check_blank_tags(instance_id, tag_keys, creator_email):
    creator_mail = ''
    ec2 = boto3.resource('ec2')
    instance = ec2.Instance(instance_id)
    logging.info (instance)
    instance_tags = {tag['Key']: tag['Value'] for tag in instance.tags or []}
    
    blank_tags = []
    creator_email_address = creator_email
    for key in tag_keys:
        logging.info (tag_keys)
        if key in instance_tags and not instance_tags[key]:
            blank_tags.append(key)
    return blank_tags
    # send_email(sender_email_address, creator_email_address, email_subject, html_email_body, blank_tags, instance_id)

def check_all_instances_tags(region, tag_keys):
    ec2 = boto3.client('ec2', region_name=region)
    
    instances = ec2.describe_instances()

    for reservation in instances['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            creator_email = get_instance_tag_value(instance_id, tag_key_to_fetch)
            blank_tags = check_blank_tags(instance_id, tag_keys, creator_email)
            if len(blank_tags) > 0:
                send_email(sender_email_address, creator_email, email_subject, html_email_body, blank_tags, instance_id)
                
            else:
                logging.info("No blank values for the Mandatory tags")

# check_all_instances_tags(region_to_check, tag_keys_to_check)

# def send_email_to_creator(instance_id_report, tags_blank)

def send_email(sender_email, recipient_email, subject, html_body, blank_tags, instance_id):
    # Create a new SES client
    ses_client = boto3.client('ses', region_name=region_to_check)

    # Construct the email
    email_content = {
        'Destination': {
            'ToAddresses': [
                recipient_email,
            ],
        },
        'Message': {
            'Body': {
                'Html': {
                    'Charset': 'UTF-8',
                    'Data': html_body,
                },
            },
            'Subject': {
                'Charset': 'UTF-8',
                'Data': subject,
            },
        },
        'Source': sender_email,
    }

    # Send the email
    try:
        response = ses_client.send_email(
            Source=sender_email,
            Destination={
                'ToAddresses': [
                    recipient_email,
                ],
            },
            Message={
                'Subject': {
                    'Data': subject,
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Html': {
                        'Data': f"{html_body}\n for the instance id: {instance_id} these tags are blank: {blank_tags}",
                        'Charset': 'UTF-8'
                    }
                }
            }
        )
    except ClientError as e:
        logging.info(f"Email sending failed. Reason: {e.response['Error']['Message']} for email: {recipient_email} for the server {instance_id}")
    else:
        logging.info(f"Email sent successfully! on email: {recipient_email} for the server {instance_id}")
        logging.info(f"Message ID: {response['MessageId']}")

# #--------------------------------------------------------------

def get_instance_tag_value(instance_id, tag_key):
    ec2 = boto3.client('ec2', region_name=aws_region)

    response = ec2.describe_instances(InstanceIds=[instance_id])

    if 'Reservations' in response and len(response['Reservations']) > 0:
        instance = response['Reservations'][0]['Instances'][0]
        tags = instance.get('Tags', [])

        for tag in tags:
            if tag['Key'] == tag_key:
                value = tag['Value']
                mail = value.split("/")
                mail_id = mail[2]
                logging.info (mail_id)

    return mail_id  # Tag key not found or instance not found

check_all_instances_tags(region_to_check, tag_keys_to_check)

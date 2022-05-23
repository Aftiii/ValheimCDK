from __future__ import annotations
from curses import keyname
from unicodedata import name
from aws_cdk import (
    # Duration,
    Stack,
    aws_ec2 as cdk_ec2
)
from constructs import Construct
import os
import base64
import boto3

class ValheimInfraStack(Stack):

    public_key_name = "ec2_rsa"
    instance_name = 'valheim_instance' 
    instance_type = 't3.micro'
    ami_name = 'ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-20220511'
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        with open('ec2_rsa.pub') as file:
            public_key = file.read()
        
        ec2 = boto3.client('ec2')
        existingKeyPairs = ec2.describe_key_pairs(KeyNames=[self.public_key_name])

        #Only create the key if it doesn't exist
        if len(existingKeyPairs.keys()) == 0:
            ec2.import_key_pair(KeyName=self.public_key_name,PublicKeyMaterial=public_key,TagSpecifications=[{'ResourceType':'key-pair','Tags':[{'Key':'purpose','Value':'ec2_auth'}]}])

        #httpRequestMethod = "GET"
        #canonicalURI = "https://ec2.amazonaws.com/?"
        #canonicalQueryString = "Action=ImportKeyPair&"
        #canonicalQueryString += f"KeyName={self.public_key_name}&"
        #canonicalQueryString += f"PublicKeyMaterial={pub_key_as_base64}&"
        #canonicalQueryString += "TagSpecification.1.ResourceType=key-pair&"
        #canonicalQueryString += "TagSpecification.1.Tag.1.Key=purpose&"
        #canonicalQueryString += "TagSpecification.1.Tag.1.Value=ec2_auth"

        
        #canonicalRequest = 

        ami_image = cdk_ec2.MachineImage().lookup(name=self.ami_name)

        vpc = cdk_ec2.Vpc(self, 'valheim-cdk-vpc', 
            cidr='10.0.0.0/16',
            nat_gateways=0,
            subnet_configuration=[cdk_ec2.SubnetConfiguration(name='public',cidr_mask=24,subnet_type=cdk_ec2.SubnetType.PUBLIC)]
        )

        sshIngress = cdk_ec2.SecurityGroup(self,id='ssh-sg', security_group_name='ssh-sg', vpc=vpc, allow_all_outbound=True)
        sshIngress.add_ingress_rule(cdk_ec2.Peer.any_ipv4(), cdk_ec2.Port.tcp(22), 'ssh')

        valheimIngress = cdk_ec2.SecurityGroup(self,id='valheim-sg',security_group_name='valheim-sg',vpc=vpc,allow_all_outbound=True)
        valheimIngress.add_ingress_rule(cdk_ec2.Peer.any_ipv4(),cdk_ec2.Port.tcp(2456), 'Valheim connect 1')
        valheimIngress.add_ingress_rule(cdk_ec2.Peer.any_ipv4(),cdk_ec2.Port.tcp(2457), 'Valheim connect 2')
        valheimIngress.add_ingress_rule(cdk_ec2.Peer.any_ipv4(),cdk_ec2.Port.tcp(2458), 'Valheim connect 3')

        instance_type = cdk_ec2.InstanceType(self.instance_type)
        
        ec2_instance = cdk_ec2.Instance(
            self,'ec2_instance',instance_name=self.instance_name, instance_type=instance_type, machine_image=ami_image, vpc=vpc, key_name=self.public_key_name
        )
        ec2_instance.add_security_group(security_group=sshIngress)
        ec2_instance.add_security_group(security_group=valheimIngress)
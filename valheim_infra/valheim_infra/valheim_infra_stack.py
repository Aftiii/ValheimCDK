from unicodedata import name
from aws_cdk import (
    # Duration,
    Stack,
    aws_ec2 as ec2,
    aws_sqs as sqs,
)
from constructs import Construct

instanceName="valheimDedicated"
instanceType="t2.micro"

class ValheimInfraStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.instance_name = 'valheim_instance'
        self.instance_type = 't3.micro'
        self.ami_name = 'ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-20220511'
        
        ami_image = ec2.MachineImage().lookup(name=self.ami_name)

        vpc = ec2.Vpc(self, 'valheim-cdk-vpc', 
            cidr='10.0.0.0/16',
            nat_gateways=0,
            subnet_configuration=[ec2.SubnetConfiguration(name='public',cidr_mask=24,subnet_type=ec2.SubnetType.PUBLIC)]
        )

        sshIngress = ec2.SecurityGroup(self,id='ssh-sg', security_group_name='ssh-sg', vpc=vpc, allow_all_outbound=True)
        sshIngress.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(22), 'ssh')

        valheimIngress = ec2.SecurityGroup(self,id='valheim-sg',security_group_name='valheim-sg',vpc=vpc,allow_all_outbound=True)
        valheimIngress.add_ingress_rule(ec2.Peer.any_ipv4(),ec2.Port.tcp(2456), 'Valheim connect 1')
        valheimIngress.add_ingress_rule(ec2.Peer.any_ipv4(),ec2.Port.tcp(2457), 'Valheim connect 2')
        valheimIngress.add_ingress_rule(ec2.Peer.any_ipv4(),ec2.Port.tcp(2458), 'Valheim connect 3')

        instance_type = ec2.InstanceType(self.instance_type)

        ec2_instance = ec2.Instance(
            self,'ec2_instance',instance_name=self.instance_name, instance_type=instance_type, machine_image=ami_image, vpc=vpc
        )
        ec2_instance.add_security_group(security_group=sshIngress)
        ec2_instance.add_security_group(security_group=valheimIngress)
import cdk_tri
from aws_cdk import CfnOutput, RemovalPolicy
from aws_cdk import aws_ec2 as ec2
from constructs import Construct


class InfraStack(cdk_tri.TriStack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        app_name: str,
        environment_name: str,
        stack_name_suffix: str | None = None,
        env=None,
    ) -> None:
        super().__init__(
            scope,
            construct_id,
            app_name=app_name,
            environment_name=environment_name,
            stack_name_suffix=stack_name_suffix,
            env=env,
        )

        vpc = ec2.Vpc(self, "Vpc", max_azs=2)

        # Workaround for tri-cdk #39: default accessLogsPrefix has trailing
        # slash which AWS rejects. Create ALB explicitly with fixed prefix.
        alb = cdk_tri.TriAlb(
            self,
            "Alb",
            vpc=vpc,
            access_logs_prefix="alb-access-logs",
        )

        web = cdk_tri.TriWebService(
            self,
            "WebService",
            app_name=self.app_name,
            environment_name=self.environment_name,
            alb=alb,
            vpc=vpc,
            services=[
                cdk_tri.TriWebServiceServiceProps(
                    service_name="carbonsight-app",
                    image_asset_path="../",
                    ports=[8000],
                    desired_count=1,
                    healthcheck_url="/health",
                    environment={
                        "PORT": "8000",
                    },
                    listener_rule_priority=1,
                ),
            ],
        )

        # Workaround for tri-cdk #41: dev environment should use DESTROY
        # removal policy so failed deploys don't leave orphaned resources.
        if self.environment_name in ("dev", "development", "staging"):
            for child in self.node.find_all():
                if hasattr(child, "apply_removal_policy"):
                    child.apply_removal_policy(RemovalPolicy.DESTROY)

        CfnOutput(
            self,
            "AlbDnsName",
            value=web.alb.load_balancer.load_balancer_dns_name,
            description="Application load balancer DNS name",
        )

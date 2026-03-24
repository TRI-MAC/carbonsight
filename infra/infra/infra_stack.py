from aws_cdk import CfnOutput
from constructs import Construct
import cdk_tri


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

        web = cdk_tri.TriWebService(
            self,
            "WebService",
            app_name=self.app_name,
            environment_name=self.environment_name,
            services=[
                cdk_tri.TriWebServiceServiceProps(
                    service_name="carbonsight-app",
                    image_asset_path="../",
                    ports=[8000],
                    desired_count=1,
                    healthcheck_url="/docs",
                    environment={
                        "PORT": "8000",
                    },
                    listener_rule_priority=1,
                ),
            ],
        )

        CfnOutput(
            self,
            "AlbDnsName",
            value=web.alb.load_balancer.load_balancer_dns_name,
            description="Application load balancer DNS name",
        )

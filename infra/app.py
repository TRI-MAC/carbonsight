#!/usr/bin/env python3
import os

import cdk_tri
from aws_cdk import Environment
from infra.infra_stack import InfraStack

app = cdk_tri.TriApp(
    app_name="carbonsight",
    environment_name="dev",
    owner="mac-research",
    project="carbonsight",
    owner_email="andrew.taber@tri.global",
)

InfraStack(
    app,
    "CarbonSightStack",
    app_name=app.app_name,
    environment_name=app.environment_name,
    stack_name_suffix="web",
    env=Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION", "us-east-1"),
    ),
)

app.synth()

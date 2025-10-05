from aws_cdk import Duration, aws_stepfunctions as sfn, aws_stepfunctions_tasks as tasks, aws_lambda as lambda_
from constructs import Construct


class WorkflowConstruct(Construct):
    """Step Functions state machine for agent creation workflow"""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        kb_provisioner: lambda_.Function,
        agentcreator_invoker: lambda_.Function,
        agentcore_deployer: lambda_.Function,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Define tasks
        kb_provisioner_task = tasks.LambdaInvoke(
            self,
            "KBProvisionerTask",
            lambda_function=kb_provisioner,
            output_path="$.Payload",
        )

        agentcreator_invoker_task = tasks.LambdaInvoke(
            self,
            "AgentCreatorInvokerTask",
            lambda_function=agentcreator_invoker,
            output_path="$.Payload",
        )

        wait_for_code = sfn.Wait(self, "WaitForCode", time=sfn.WaitTime.duration(Duration.seconds(30)))

        check_code_task = tasks.LambdaInvoke(
            self,
            "CheckCodeTask",
            lambda_function=agentcore_deployer,
            payload=sfn.TaskInput.from_object(
                {"action": "check_code", "agentId": sfn.JsonPath.string_at("$.agentId")}
            ),
            output_path="$.Payload",
        )

        deployer_task = tasks.LambdaInvoke(
            self,
            "DeployerTask",
            lambda_function=agentcore_deployer,
            output_path="$.Payload",
        )

        # Define workflow
        definition = (
            kb_provisioner_task.next(agentcreator_invoker_task)
            .next(wait_for_code)
            .next(check_code_task)
            .next(
                sfn.Choice(self, "CodeReady?")
                .when(sfn.Condition.boolean_equals("$.codeReady", True), deployer_task)
                .otherwise(wait_for_code)
            )
        )

        # Create state machine
        self.state_machine = sfn.StateMachine(
            self,
            "AgentCreationWorkflow",
            state_machine_name="oratio-agent-creation",
            definition_body=sfn.DefinitionBody.from_chainable(definition),
        )

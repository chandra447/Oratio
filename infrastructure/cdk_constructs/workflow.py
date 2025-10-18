from aws_cdk import Duration, aws_stepfunctions as sfn, aws_stepfunctions_tasks as tasks, aws_lambda as lambda_
from constructs import Construct


class WorkflowConstruct(Construct):
    """Simplified Step Functions workflow for agent creation"""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        kb_provisioner: lambda_.Function,
        agentcreator_invoker: lambda_.Function,
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

        # Simplified workflow: KB Provisioner → AgentCreator (which marks as active)
        definition = kb_provisioner_task.next(agentcreator_invoker_task)

        # Create state machine
        self.state_machine = sfn.StateMachine(
            self,
            "AgentCreationWorkflow",
            state_machine_name="oratio-agent-creation",
            definition_body=sfn.DefinitionBody.from_chainable(definition),
        )
